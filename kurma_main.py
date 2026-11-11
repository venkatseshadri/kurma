#!/usr/bin/env python3
"""
🐢 Project Kurma - MCX Intraday Trading Bot
Evening Session Momentum Trading System (5:00 PM - 11:20 PM IST)

Capital-efficient bot reusing Varaha's released margin for intraday MCX trading.
Targets: ₹1,000-1,500/day with 70%+ win rate.

Author: Kubera 🦞
Date: Apr 30, 2026
"""

import sys
import os
import argparse
import logging
import yaml
import json
from datetime import datetime, time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - KURMA - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/trading_ceo/projects/python-trader/kurma_system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Enable detailed debug logging for HTTP and API modules
http_logger = logging.getLogger("urllib3")
http_logger.setLevel(logging.DEBUG)
http_logger.propagate = True

requests_logger = logging.getLogger("requests")
requests_logger.setLevel(logging.DEBUG)
requests_logger.propagate = True

noren_logger = logging.getLogger("NorenApi")
noren_logger.setLevel(logging.DEBUG)
noren_logger.propagate = True

# Add handler for HTTP debug logs
http_handler = logging.StreamHandler(sys.stdout)
http_handler.setLevel(logging.DEBUG)
http_logger.addHandler(http_handler)
requests_logger.addHandler(http_handler)


class KurmaConfig:
    """Global configuration for Kurma"""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"Config loaded: {config_path}")

    def get(self, key, default=None):
        """Get config value"""
        return self.config.get(key, default)


class KurmaOrchestrator:
    """Master orchestrator for Kurma - MCX evening session trading"""

    def __init__(self, args):
        self.args = args
        self.config = KurmaConfig()
        self.mode = self.determine_mode()
        self.live_execution = args.live_execution
        self.confirm_live = args.confirm_live_execution
        self.broker_connection = None

        # Validate mode
        self._validate_mode()

        logger.info("=" * 60)
        logger.info("🐢 PROJECT KURMA - MASTER ORCHESTRATOR v1.0")
        logger.info(f"   Mode: {self.mode.upper()}")
        logger.info(f"   Data Broker: {args.data_broker}")
        logger.info(f"   Trade Broker: {args.exec_broker}")
        logger.info(f"   Live Execution: {self.live_execution}")
        logger.info(f"   Time: {datetime.now()}")
        logger.info("=" * 60)

    def determine_mode(self):
        """Determine execution mode based on args"""

        if self.args.dry_run:
            return 'dry-run'

        if self.args.live_execution:
            return 'live'

        # Paper mode: data-broker specified (exec-broker is optional, will default to data-broker)
        if self.args.data_broker:
            return 'paper'

        return 'dry-run'  # Default safe mode

    def _validate_mode(self):
        """Validate mode consistency"""

        # Cannot mix dry-run with live execution
        if self.mode == 'dry-run' and self.live_execution:
            logger.error("❌ INVALID: Cannot use --dry-run with --live-execution")
            sys.exit(1)

        # Live execution requires:
        # 1. Double confirmation
        # 2. Both data-broker and exec-broker specified
        if self.live_execution:
            if self.confirm_live != 'yes':
                logger.error("❌ INVALID: Live execution requires --confirm-live-execution=yes")
                logger.error(f"   Actual value: {self.confirm_live}")
                sys.exit(1)

            if not self.args.exec_broker:
                logger.error("❌ INVALID: Live execution requires --exec-broker to be specified")
                sys.exit(1)

            logger.warning("🔴 LIVE EXECUTION CONFIRMED - Real orders will be placed!")

        # Paper mode: data-broker required, exec-broker optional (defaults to data-broker)
        elif self.mode == 'paper':
            if not self.args.data_broker:
                logger.error("❌ INVALID: Paper mode requires --data-broker to be specified")
                sys.exit(1)

            # If exec-broker not specified, use data-broker for consistency
            if not self.args.exec_broker:
                self.args.exec_broker = self.args.data_broker
                logger.info(f"   exec-broker not specified, using data-broker: {self.args.exec_broker}")

    def check_market_hours(self):
        """Check if MCX evening session is open"""

        current_time = datetime.now().time()

        # MCX evening: 5:00 PM - 11:30 PM
        mcx_open = time(17, 0)   # 5:00 PM
        mcx_close = time(23, 30)  # 11:30 PM

        # Trading days: holiday-aware for MCX, not just Mon-Fri.
        try:
            from market_calendar import is_trading_day as _mcx_trading_day
            is_trading_day = _mcx_trading_day(datetime.now().date(), "MCX")
        except Exception as _e:
            logger.warning(f"market_calendar unavailable ({_e}) - weekday-only")
            is_trading_day = datetime.now().weekday() < 5

        if not is_trading_day:
            logger.info("🛑 MCX CLOSED (weekend or holiday) - No trading today")
            return False

        if current_time < mcx_open:
            logger.info(f"⏰ MCX not open yet (opens 5:00 PM, current {current_time.strftime('%H:%M')})")
            return False

        if current_time > mcx_close:
            logger.info(f"🛑 MCX CLOSED (closes 11:30 PM, current {current_time.strftime('%H:%M')})")
            return False

        logger.info(f"✅ MCX OPEN - Session runs until 11:30 PM")
        return True

    def authenticate_and_check_margin(self):
        """Authenticate with broker and get available margin"""

        from kurma_auth import KurmaConnect

        logger.info("🔐 Phase 1: Broker Authentication")

        # Create broker connection
        connect = KurmaConnect(broker=self.args.exec_broker, mode=self.mode)

        # Login
        if not connect.login():
            if self.mode == 'paper':
                logger.warning("⚠️ Paper mode: Real login failed, using mock margin for OHLC fallback")
                # For paper mode, we can continue with mocked margin if login fails
                margin_info = {
                    'available': 400000,
                    'used': 0,
                    'total': 400000,
                    'equity': 400000,
                    'mode': 'paper-mock'
                }
            elif self.mode == 'live':
                logger.error("❌ Live mode requires valid broker connection")
                return None
            else:
                logger.error("❌ Broker login failed")
                return None
        else:
            logger.info("✅ Broker login successful")
            # Get margin
            margin_info = connect.get_margin()

            if not margin_info:
                logger.error("❌ Failed to fetch margin")
                return None

        # Store connection for later use (even if login failed, selector can try)
        self.broker_connection = connect

        return margin_info

    def run_orchestrator(self):
        """Main execution flow"""

        logger.info("\n🐢 KURMA INITIALIZATION\n")

        # Phase 0: Check market hours
        if not self.check_market_hours():
            logger.info("Market not open, exiting")
            return False

        # Phase 1: Broker authentication & margin check
        margin_info = self.authenticate_and_check_margin()
        if not margin_info:
            logger.error("❌ Failed to authenticate or check margin")
            return False

        logger.info(f"✅ Authenticated & margin verified:")
        logger.info(f"   Available Cash: ₹{margin_info.get('available', 0):,.2f}")
        logger.info(f"   Collateral: ₹{margin_info.get('collateral', 0):,.2f}")
        logger.info(f"   Gross Collateral: ₹{margin_info.get('gross_collateral', 0):,.2f}")

        logger.info("\n📍 PHASE 1: INSTRUMENT SELECTOR")
        # Import selector module
        from kurma_selector import KurmaSelector
        selector = KurmaSelector(self.config, self.mode, broker_connection=self.broker_connection)
        selected_instrument = selector.select_best_instrument()

        if not selected_instrument:
            logger.warning("⚠️ No instruments with score > threshold, skipping session")
            return False

        logger.info(f"✅ Selected: {selected_instrument['instrument']} (Score: {selected_instrument['score']:.1f}/10)")

        logger.info("\n📍 PHASE 2: MOMENTUM TRADING")
        # Import momentum bot
        from kurma_momentum import KurmaMomentum
        momentum_bot = KurmaMomentum(
            config=self.config,
            mode=self.mode,
            selected_instrument=selected_instrument,
            broker_connection=self.broker_connection
        )

        trades = momentum_bot.run_trading_session()

        logger.info("\n📍 PHASE 3: EOD ANALYSIS")
        # Import EOD analyzer
        from kurma_eod_analyzer import KurmaEODAnalyzer
        analyzer = KurmaEODAnalyzer(self.config)
        analyzer.analyze_session(trades, selected_instrument)

        logger.info("\n✅ KURMA SESSION COMPLETE")
        logger.info("=" * 60)

        return True


def main():
    """Entry point"""

    parser = argparse.ArgumentParser(
        description='🐢 Kurma MCX Intraday Trading Bot (Evening Session: 5:00 PM - 11:20 PM)',
        epilog="""
Examples:
  # Test (safe, fully mocked)
  python3 kurma_main.py --dry-run

  # Paper mode (real data, simulated orders) - exec-broker optional
  python3 kurma_main.py --data-broker flattrade
  # OR with explicit exec-broker:
  python3 kurma_main.py --data-broker flattrade --exec-broker flattrade

  # Live trading (⚠️ real orders) - exec-broker required
  python3 kurma_main.py --data-broker flattrade --exec-broker flattrade \\
    --live-execution --confirm-live-execution=yes
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # ============================================================
    # EXECUTION MODE PARAMETERS
    # ============================================================

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        help='Run in fully mocked mode (mock data + mock orders). '
             'Ignores all broker parameters. Default if no other params set.'
    )

    # ============================================================
    # DATA SOURCE PARAMETERS (ignored in dry-run)
    # ============================================================

    parser.add_argument(
        '--data-broker',
        type=str,
        default='flattrade',
        help='Data source broker(s) for market quotes. '
             'Options: flattrade, shoonya, yfinance, or comma-separated fallback chain. '
             'Default: flattrade (zero brokerage)'
    )

    # ============================================================
    # EXECUTION PARAMETERS (ignored in dry-run)
    # ============================================================

    parser.add_argument(
        '--exec-broker',
        type=str,
        default='',
        help='Broker for order execution: flattrade or shoonya. '
             'Required for --live-execution. '
             'Optional for paper mode (defaults to --data-broker if not specified). '
             'Ignored in --dry-run mode.'
    )

    # ============================================================
    # LIVE TRADING FLAGS (for safety)
    # ============================================================

    parser.add_argument(
        '--live-execution',
        action='store_true',
        default=False,
        help='Enable REAL order execution to broker. '
             'REQUIRES --confirm-live-execution=yes to prevent accidents. '
             'Cannot be used with --dry-run.'
    )

    parser.add_argument(
        '--confirm-live-execution',
        type=str,
        default='no',
        help='Confirm intent to execute REAL ORDERS. Must be exactly "yes". '
             'Required when using --live-execution.'
    )

    # ============================================================
    # OPTIONAL PARAMETERS
    # ============================================================

    parser.add_argument(
        '--instrument',
        type=str,
        help='Force specific instrument (override dynamic selector). '
             'Options: CRUDEOILM, GOLDM, SILVERM, NATGASM'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging (verbose output)'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run orchestrator
    orchestrator = KurmaOrchestrator(args)
    success = orchestrator.run_orchestrator()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
