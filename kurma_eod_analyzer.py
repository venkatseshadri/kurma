#!/usr/bin/env python3
"""
🐢 Kurma EOD Analyzer
End-of-day analysis, research, and recommendations engine
"""

import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class KurmaEODAnalyzer:
    """Comprehensive end-of-day analysis"""

    def __init__(self, config):
        self.config = config
        self.report_dir = Path('/home/trading_ceo/python-trader/kurma_eod_reports')
        self.report_dir.mkdir(exist_ok=True)

    def analyze_session(self, trades, selected_instrument):
        """Run complete EOD analysis"""

        logger.info("\n📊 PHASE 3: EOD ANALYSIS\n")

        # Phase 1: Trade-level analysis
        trade_analysis = self._analyze_trades(trades)

        # Phase 2: Market condition analysis
        market_analysis = self._analyze_market(selected_instrument)

        # Phase 3: Deep research
        research = self._deep_research(trades, selected_instrument)

        # Phase 4: Recommendations
        recommendations = self._generate_recommendations(trade_analysis, market_analysis, research)

        # Generate report
        self._generate_report(trade_analysis, market_analysis, research, recommendations)

    def _analyze_trades(self, trades):
        """Analyze each trade"""

        logger.info("📈 Trade-level analysis...")

        analysis = {
            'total_trades': len(trades),
            'total_pnl': sum(t.total_pnl for t in trades),
            'winners': len([t for t in trades if t.win_loss == 'WIN']),
            'losers': len([t for t in trades if t.win_loss == 'LOSS']),
            'win_rate': 0,
            'trades': []
        }

        if len(trades) > 0:
            analysis['win_rate'] = analysis['winners'] / len(trades) * 100

        for trade in trades:
            trade_detail = {
                'trade_id': trade.trade_id,
                'instrument': trade.instrument,
                'entry_price': trade.entry_price,
                'entry_signal': trade.entry_signal,
                'entry_quality': trade.entry_quality,
                'total_pnl': trade.total_pnl,
                'win_loss': trade.win_loss
            }

            if trade.tranche_1:
                trade_detail['tranche_1_pnl'] = trade.tranche_1['pnl_rupees']
            if trade.tranche_2:
                trade_detail['tranche_2_pnl'] = trade.tranche_2['pnl_rupees']
            if trade.tranche_3:
                trade_detail['tranche_3_pnl'] = trade.tranche_3['pnl_rupees']

            analysis['trades'].append(trade_detail)

        logger.info(
            f"  ✅ Total P&L: +{analysis['total_pnl']:.0f} rupees "
            f"({analysis['winners']}/{analysis['total_trades']} wins, "
            f"{analysis['win_rate']:.0f}% win rate)"
        )

        return analysis

    def _analyze_market(self, selected_instrument):
        """Analyze market conditions"""

        logger.info("🌍 Market condition analysis...")

        analysis = {
            'selected_instrument': selected_instrument['instrument'],
            'trend_score': selected_instrument['details'].get('trend', 0),
            'liquidity_score': selected_instrument['details'].get('liquidity', 0),
            'bias_score': selected_instrument['details'].get('bias', 0),
            'final_score': selected_instrument['score'],
            'timestamp': datetime.now().isoformat()
        }

        logger.info(
            f"  Selected: {analysis['selected_instrument']} "
            f"(Trend: {analysis['trend_score']:.0f}, "
            f"Liquidity: {analysis['liquidity_score']:.0f})"
        )

        return analysis

    def _deep_research(self, trades, selected_instrument):
        """Deep research on why trades won/lost"""

        logger.info("🔬 Deep research on trade outcomes...")

        research = {
            'instruments_scored': len(selected_instrument.get('all_scores', {})),
            'best_signal': self._identify_best_entry_signal(trades),
            'correlation_insights': self._analyze_correlations(trades),
            'next_day_prediction': self._predict_next_day(selected_instrument)
        }

        return research

    def _identify_best_entry_signal(self, trades):
        """Which entry signal worked best?"""

        signal_results = {}

        for trade in trades:
            signal = trade.entry_signal

            if signal not in signal_results:
                signal_results[signal] = {'wins': 0, 'losses': 0, 'total_pnl': 0}

            if trade.win_loss == 'WIN':
                signal_results[signal]['wins'] += 1
            else:
                signal_results[signal]['losses'] += 1

            signal_results[signal]['total_pnl'] += trade.total_pnl

        if not signal_results or not any(signal_results.values()):
            logger.info(f"  Best entry signal: N/A (no trades executed)")
            return None

        best_signal = max(
            signal_results.items(),
            key=lambda x: x[1]['wins'] / (x[1]['wins'] + x[1]['losses']) if (x[1]['wins'] + x[1]['losses']) > 0 else 0
        )

        logger.info(f"  Best entry signal: {best_signal[0]}")

        return best_signal

    def _analyze_correlations(self, trades):
        """What factors correlated with wins?"""

        insights = []

        # Entry quality correlation
        win_quality = [t.entry_quality for t in trades if t.win_loss == 'WIN']
        loss_quality = [t.entry_quality for t in trades if t.win_loss == 'LOSS']

        if win_quality:
            avg_win_quality = sum(win_quality) / len(win_quality)
            insights.append(f"Winning trades averaged {avg_win_quality:.1f}/10 entry quality")

        return insights

    def _predict_next_day(self, selected_instrument):
        """Predict best instrument for next session"""

        current_best = selected_instrument['instrument']
        current_score = selected_instrument['score']

        prediction = {
            'predicted_instrument': current_best,
            'confidence': min(85, current_score * 10),  # Scale to percentage
            'reasoning': [
                f"Today's selected instrument ({current_best}) was strong",
                'Momentum tends to persist 1-2 sessions',
                'Monitor for external catalysts (news, economic data)'
            ]
        }

        return prediction

    def _generate_recommendations(self, trade_analysis, market_analysis, research):
        """Generate actionable recommendations"""

        recommendations = {
            'parameter_tweaks': self._recommend_parameter_changes(trade_analysis),
            'strategy_changes': self._recommend_strategy_changes(trade_analysis),
            'next_session': research['next_day_prediction']
        }

        return recommendations

    def _recommend_parameter_changes(self, trade_analysis):
        """Should we tweak TP/TSL/position size?"""

        tweaks = []

        win_rate = trade_analysis['win_rate']

        if win_rate > 85:
            tweaks.append('✅ Win rate excellent - keep current parameters')
        elif win_rate < 50:
            tweaks.append('⚠️ Win rate low - consider tightening TSL or reducing position size')

        return tweaks

    def _recommend_strategy_changes(self, trade_analysis):
        """Change entry/exit strategy?"""

        changes = []

        # Analyze by entry signal
        # Would need detailed breakdown

        return changes

    def _generate_report(self, trade_analysis, market_analysis, research, recommendations):
        """Generate text report"""

        report_path = self.report_dir / f"kurma_eod_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(report_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("🐢 KURMA EOD ANALYSIS REPORT\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

            # Trade summary
            f.write("TRADE SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Trades: {trade_analysis['total_trades']}\n")
            f.write(f"Wins: {trade_analysis['winners']}\n")
            f.write(f"Losses: {trade_analysis['losers']}\n")
            f.write(f"Win Rate: {trade_analysis['win_rate']:.1f}%\n")
            f.write(f"Total P&L: ₹{trade_analysis['total_pnl']:.0f}\n\n")

            # Market analysis
            f.write("MARKET ANALYSIS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Selected Instrument: {market_analysis['selected_instrument']}\n")
            f.write(f"Trend Score: {market_analysis['trend_score']:.0f}/10\n")
            f.write(f"Liquidity Score: {market_analysis['liquidity_score']:.0f}/10\n")
            f.write(f"Final Score: {market_analysis['final_score']:.1f}/10\n\n")

            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 70 + "\n")
            for tweak in recommendations['parameter_tweaks']:
                f.write(f"• {tweak}\n")
            f.write("\n")

            # Next day prediction
            f.write("NEXT SESSION PREDICTION\n")
            f.write("-" * 70 + "\n")
            pred = recommendations['next_session']
            f.write(f"Predicted Best Instrument: {pred['predicted_instrument']}\n")
            f.write(f"Confidence: {pred['confidence']:.0f}%\n")
            for reason in pred['reasoning']:
                f.write(f"• {reason}\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write(f"Report saved: {report_path}\n")

        logger.info(f"✅ Report saved: {report_path}")

        # Also save JSON for machine processing
        json_path = report_path.with_suffix('.json')
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'trade_analysis': trade_analysis,
            'market_analysis': market_analysis,
            'research': research,
            'recommendations': recommendations
        }

        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"✅ JSON saved: {json_path}")
