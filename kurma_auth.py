#!/usr/bin/env python3
"""
🐢 Kurma Authentication Module
Flattrade connection, login, and margin checking
"""

import sys
import os
import json
import logging
import yaml
import pyotp
from pathlib import Path
from datetime import datetime

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, '/home/trading_ceo/python-trader/FlattradeApi-py')
sys.path.insert(0, '/home/trading_ceo/python-trader/NorenRestApiPy')

try:
    from api_helper import NorenApiPy
except ImportError:
    from NorenRestApiPy.NorenApi import NorenApi as NorenApiPy

logger = logging.getLogger(__name__)


class KurmaConnect:
    """Multi-broker connection wrapper for Kurma"""

    def __init__(self, broker='flattrade', mode='paper'):
        """Initialize connection (not logged in yet)

        Args:
            broker: 'flattrade' or 'shoonya'
            mode: 'dry-run', 'paper', or 'live'
        """
        self.broker = broker.lower()
        self.mode = mode
        self.api = self._get_api_for_broker()
        self.connected = False
        self.user_id = None
        self.credentials = self._load_credentials()

    def _get_api_for_broker(self):
        """Get appropriate API object for broker"""
        if self.broker == 'flattrade':
            return NorenApiPy()
        elif self.broker == 'shoonya':
            # TODO: Import Shoonya API if needed
            logger.warning("Shoonya API not yet implemented, using Flattrade")
            return NorenApiPy()
        else:
            logger.warning(f"Unknown broker: {self.broker}, using Flattrade")
            return NorenApiPy()

    def _get_token_for_instrument(self, instrument):
        """Map instrument name to MCX token ID (active contract)

        Returns the token ID for the current active future contract.
        As of Apr 30, 2026:
        """
        token_map = {
            'CRUDEOILM': '488291',   # CRUDEOILM 18-MAY-2026
            'GOLDM': '487819',       # GOLDM 05-MAY-2026
            'SILVERM': '457533',     # SILVERM 30-APR-2026
            'NATGASM': '488506',     # NATGASMINI 26-MAY-2026
        }
        return token_map.get(instrument)

    def _load_credentials(self):
        """Load Flattrade credentials from YAML"""

        cred_paths = [
            '/home/trading_ceo/python-trader/flattrade_cred.yml',
            '/home/trading_ceo/python-trader/FlattradeApi-py/cred.yml',
            os.path.expanduser('~/.flattrade/cred.yml')
        ]

        # Hardcoded defaults for development/testing
        default_creds = {
            'user_id': 'FT055702',
            'password': 'Taknev80*$$$',
            'api_key': '37d30474def84eb1a0666f1dc2bc0e4f',
            'totp_secret': 'HQ5233H3XG5YEWZ3F47CJ43XON6755AR'
        }

        for cred_path in cred_paths:
            if os.path.exists(cred_path):
                try:
                    with open(cred_path, 'r') as f:
                        creds = yaml.safe_load(f)

                    # Merge loaded creds with defaults to fill in missing fields
                    if creds:
                        merged = default_creds.copy()
                        merged.update(creds)
                        logger.info(f"Credentials loaded from {cred_path}")
                        return merged
                except Exception as e:
                    logger.warning(f"Failed to load {cred_path}: {e}")

        logger.warning("No credentials file found, using hardcoded (dev only)")
        return default_creds

    def login(self):
        """Login to Flattrade broker"""

        if self.mode == 'dry-run':
            logger.info(f"🔐 DRY-RUN: Skipping actual login (fully mocked)")
            self.connected = True
            self.user_id = self.credentials.get('user_id', 'FT055702')
            return True

        # Paper and Live modes: Try to authenticate with OAuth token
        logger.info("🔐 Connecting to Flattrade...")

        try:
            # First, try to use cached OAuth token
            token_file = os.path.join(os.path.dirname(__file__), '../FlattradeApi-py/tokens.json')

            if os.path.exists(token_file):
                try:
                    with open(token_file, 'r') as f:
                        token_data = json.load(f)

                    user_id = token_data.get('client')
                    token = token_data.get('token')

                    if user_id and token:
                        logger.debug(f"  Using cached OAuth token for {user_id}")
                        ret = self.api.set_session(userid=user_id, accesstoken=token)

                        if ret:
                            logger.info("✅ Flattrade OAuth session established")
                            self.connected = True
                            self.user_id = user_id
                            return True
                        else:
                            logger.warning(f"⚠️ OAuth token rejected, trying password auth...")
                except Exception as e:
                    logger.warning(f"⚠️ Could not use OAuth token: {e}")

            # Fallback: Try password + TOTP authentication
            user_id = self.credentials.get('user_id')
            password = self.credentials.get('password')
            api_key = self.credentials.get('api_key')
            totp_secret = self.credentials.get('totp_secret')

            totp = pyotp.TOTP(totp_secret)
            otp_code = totp.now()

            logger.debug(f"  User ID: {user_id}")
            logger.debug(f"  OTP Code: {otp_code}")

            ret = self.api.login(
                userid=user_id,
                password=password,
                twoFA=otp_code,
                vendor_code="",
                api_secret=api_key,
                imei=""
            )

            if ret:
                logger.info("✅ Flattrade login successful")
                self.connected = True
                self.user_id = user_id
                return True
            else:
                logger.warning(f"⚠️ Flattrade login returned: {ret}")
                return False

        except Exception as e:
            logger.warning(f"⚠️ Login error: {e}")
            return False

    def get_margin(self):
        """Get available margin and fund details"""

        if not self.connected:
            logger.warning("Not connected, login first")
            return None

        if self.mode == 'dry-run':
            logger.info(f"💰 DRY-RUN: Returning mock margin")
            return {
                'available': 400000,
                'used': 0,
                'total': 400000,
                'equity': 400000,
                'mode': self.mode.upper()
            }

        try:
            logger.info("💰 Fetching margin details from broker...")

            # Get fund/margin limits from API
            ret = self.api.get_limits()
            logger.debug(f"📊 Raw limits response: {ret}")

            if ret and ret.get('stat') == 'Ok':
                # Parse margin data from limits response (flat structure, not nested)
                margin_data = {
                    'available': float(ret.get('cash', 0)),
                    'payin': float(ret.get('payin', 0)),
                    'collateral': float(ret.get('collateral', 0)),
                    'gross_collateral': float(ret.get('grcoll', 0)),
                    'blocked': float(ret.get('blk_amt', 0)),
                    'raw': ret,
                    'timestamp': datetime.now().isoformat()
                }

                logger.info(f"✅ Margin fetched successfully")
                logger.info(f"   Available Cash: ₹{margin_data['available']:,.2f}")
                logger.info(f"   Collateral: ₹{margin_data['collateral']:,.2f}")
                logger.info(f"   Gross Collateral: ₹{margin_data['gross_collateral']:,.2f}")

                return margin_data
            else:
                logger.warning(f"⚠️ Margin fetch failed: {ret}, using mock margin")
                return {
                    'available': 400000,
                    'used': 0,
                    'total': 400000,
                    'equity': 400000,
                    'mode': 'MOCK'
                }

        except Exception as e:
            logger.warning(f"⚠️ Margin fetch error: {e}, using mock margin")
            return {
                'available': 400000,
                'used': 0,
                'total': 400000,
                'equity': 400000,
                'mode': 'MOCK'
            }

    def get_positions(self):
        """Get current open positions"""

        if not self.connected:
            logger.warning("Not connected, login first")
            return []

        if self.mode == 'dry-run':
            logger.info("📊 DRY-RUN: No positions (mocked)")
            return []

        try:
            logger.info("📊 Fetching positions...")
            ret = self.api.get_positions()

            if ret and isinstance(ret, list):
                logger.info(f"✅ Found {len(ret)} positions")
                return ret
            else:
                logger.info("No positions found")
                return []

        except Exception as e:
            logger.error(f"❌ Position fetch error: {e}")
            return []

    def get_orderbook(self):
        """Get order book"""

        if not self.connected:
            logger.warning("Not connected, login first")
            return []

        if self.mode == 'dry-run':
            logger.info("📖 DRY-RUN: Empty orderbook (mocked)")
            return []

        try:
            logger.info("📖 Fetching orderbook...")
            ret = self.api.get_order_book()

            if ret and isinstance(ret, list):
                logger.info(f"✅ Found {len(ret)} orders")
                return ret
            else:
                logger.info("No orders found")
                return []

        except Exception as e:
            logger.error(f"❌ Orderbook fetch error: {e}")
            return []

    def get_quote(self, instrument, exchange='MCX'):
        """Get live quote for a commodity"""

        if not self.connected:
            logger.warning("Not connected, login first")
            return None

        if self.mode == 'dry-run':
            logger.debug(f"📈 DRY-RUN: Mock quote for {instrument}")
            return {
                'ltp': 9110,
                'bid': 9108,
                'ask': 9112,
                'volume': 50000,
                'mode': 'DRY-RUN'
            }

        try:
            ret = self.api.get_quotes(exchange, instrument)

            if ret and ret.get('stat') == 'Ok':
                quote = {
                    'ltp': float(ret.get('ltp', 0)),
                    'bid': float(ret.get('bid', 0)),
                    'ask': float(ret.get('ask', 0)),
                    'volume': int(ret.get('volume', 0)),
                    'raw': ret
                }
                return quote
            else:
                logger.error(f"Quote error: {ret}")
                return None

        except Exception as e:
            logger.error(f"Quote fetch error: {e}")
            return None

    def place_order(self, **kwargs):
        """Place an order"""

        if not self.connected:
            logger.error("Not connected, login first")
            return None

        if self.mode in ['dry-run', 'paper']:
            logger.info(f"📝 {self.mode.upper()}: Simulating order placement")
            return {
                'orderno': f"SI{kwargs.get('exchange', 'MCX')}001",
                'stat': 'Ok',
                'mode': self.mode.upper()
            }

        try:
            ret = self.api.place_order(**kwargs)
            return ret

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return None

    def get_ohlc(self, instrument, interval='5min', lookback_minutes=60, exchange='MCX'):
        """Get OHLC data for an instrument

        Args:
            instrument: Symbol name (e.g. 'CRUDEOILM', 'GOLDM')
            interval: Candle interval (default '5min')
            lookback_minutes: How many minutes back (default 60)
            exchange: Exchange name (default 'MCX')

        Returns:
            List of OHLC dicts or None if error
        """

        if not self.connected:
            logger.warning("Not connected, login first")
            return None

        if self.mode == 'dry-run':
            return None  # Let selector generate mock data

        try:
            from datetime import datetime, timedelta
            import time

            # Calculate time range
            now = datetime.now()
            start_time = now - timedelta(minutes=lookback_minutes)

            # Convert to unix timestamps (Flattrade expects seconds)
            start_secs = int(start_time.timestamp())
            end_secs = int(now.timestamp())

            logger.debug(f"📊 Fetching {interval} OHLC for {instrument} ({lookback_minutes}min)")

            # Get token ID for instrument
            token = self._get_token_for_instrument(instrument)
            if not token:
                logger.warning(f"⚠️ Unknown instrument token for {instrument}")
                return None

            # Call Flattrade API for time series data (token must be numeric ID, not symbol)
            ret = self.api.get_time_price_series(
                exchange=exchange,
                token=token
            )

            if ret and isinstance(ret, list) and len(ret) > 0:
                # Convert Flattrade API response to standard OHLC format
                # Flattrade returns: into(open), inth(high), intl(low), intc(close), intv(volume)
                ohlc_data = []
                for candle in ret:
                    ohlc_data.append({
                        'time': candle.get('time', ''),
                        'open': float(candle.get('into', 0)),      # Flattrade: into = intraday open
                        'high': float(candle.get('inth', 0)),      # Flattrade: inth = intraday high
                        'low': float(candle.get('intl', 0)),       # Flattrade: intl = intraday low
                        'close': float(candle.get('intc', 0)),     # Flattrade: intc = intraday close
                        'volume': int(candle.get('intv', 0))       # Flattrade: intv = intraday volume
                    })

                logger.debug(f"✅ Fetched {len(ohlc_data)} candles for {instrument}")
                return ohlc_data
            else:
                logger.warning(f"⚠️ No OHLC data returned for {instrument}")
                return None

        except Exception as e:
            logger.warning(f"⚠️ OHLC fetch error for {instrument}: {e}")
            return None

    def close(self):
        """Disconnect from broker"""

        if self.connected:
            try:
                self.api.close_websocket()
                logger.info("✅ Disconnected from Flattrade")
            except:
                pass

        self.connected = False


# Convenience function for Kurma
def test_connection(broker='flattrade', mode='paper'):
    """Test broker connection and margin

    Args:
        broker: 'flattrade' or 'shoonya'
        mode: 'dry-run', 'paper', or 'live'
    """

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - KURMA - %(levelname)s - %(message)s'
    )

    logger.info("=" * 70)
    logger.info(f"🐢 KURMA {broker.upper()} CONNECTION TEST ({mode.upper()} MODE)")
    logger.info("=" * 70)

    connect = KurmaConnect(broker=broker, mode=mode)

    # Login
    if not connect.login():
        logger.error("❌ Login failed")
        return False

    # Get margin
    margin = connect.get_margin()
    if margin:
        logger.info("\n💰 MARGIN DETAILS:")
        logger.info(f"   Available Cash: ₹{margin['available']:,.2f}")
        logger.info(f"   Collateral: ₹{margin['collateral']:,.2f}")
        logger.info(f"   Gross Collateral: ₹{margin['gross_collateral']:,.2f}")
        logger.info(f"   Blocked: ₹{margin['blocked']:,.2f}")
    else:
        logger.error("❌ Failed to get margin")

    # Get positions
    positions = connect.get_positions()
    if positions:
        logger.info(f"\n📊 POSITIONS: {len(positions)} open positions")
        for pos in positions[:3]:  # Show first 3
            logger.info(f"   {pos.get('symbol')}: Qty {pos.get('qty')} @ {pos.get('netprice')}")
    else:
        logger.info("\n📊 POSITIONS: None")

    # Get orderbook
    orders = connect.get_orderbook()
    if orders:
        logger.info(f"\n📖 ORDERS: {len(orders)} open orders")
        for order in orders[:3]:  # Show first 3
            logger.info(f"   {order.get('symbol')}: {order.get('qty')} @ {order.get('price')} ({order.get('status')})")
    else:
        logger.info("\n📖 ORDERS: None")

    # Cleanup
    connect.close()

    logger.info("\n" + "=" * 70)
    logger.info("✅ TEST COMPLETE")
    logger.info("=" * 70)

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test Kurma broker connection')
    parser.add_argument('--broker', type=str, default='flattrade', help='Broker (flattrade, shoonya)')
    parser.add_argument('--mode', type=str, default='paper', help='Mode (dry-run, paper, live)')
    args = parser.parse_args()

    test_connection(broker=args.broker, mode=args.mode)
