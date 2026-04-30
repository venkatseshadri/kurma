#!/usr/bin/env python3
"""
🐢 Kurma Instrument Selector
Dynamic commodity selection based on trend strength, volatility, and liquidity
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class KurmaSelector:
    """Select best MCX commodity based on current market conditions"""

    def __init__(self, config, mode='dry-run', broker_connection=None):
        self.config = config
        self.mode = mode
        self.broker_connection = broker_connection
        self.instruments = ['CRUDEOILM', 'GOLDM', 'SILVERM', 'NATGASM']
        self.min_score_threshold = config.get('selector', {}).get('min_score_threshold', 5.0)
        self.lookback_minutes = config.get('selector', {}).get('lookback_minutes', 60)

    def select_best_instrument(self):
        """
        Analyze all instruments and select best one
        Returns: {'instrument': 'CRUDEOILM', 'score': 8.5, 'details': {...}}
        """

        logger.info("📊 Scanning instruments for trends...")

        scores = {}

        for instrument in self.instruments:
            logger.debug(f"  Analyzing {instrument}...")

            # Fetch OHLC data
            ohlc_data = self._fetch_ohlc(instrument)

            # Fall back to mock data if real data unavailable
            if not ohlc_data:
                if self.mode == 'dry-run':
                    # Dry-run should always generate mock
                    ohlc_data = self._generate_mock_ohlc(instrument)
                else:
                    # For paper/live, if real data fails, warn but continue with mock
                    logger.warning(f"  ⚠️ {instrument} - Real data unavailable, using mock")
                    ohlc_data = self._generate_mock_ohlc(instrument)

            # Calculate scores
            trend_score = self._calculate_trend_strength(ohlc_data)
            liquidity_score = self._calculate_liquidity(instrument, ohlc_data)
            bias_score = self._calculate_directional_bias(ohlc_data)

            # Weighted final score
            final_score = (
                trend_score * 0.5 +
                liquidity_score * 0.3 +
                bias_score * 0.2
            )

            scores[instrument] = {
                'score': final_score,
                'trend': trend_score,
                'liquidity': liquidity_score,
                'bias': bias_score,
                'data': ohlc_data
            }

            logger.info(
                f"  {instrument}: {final_score:.1f}/10 "
                f"(Trend:{trend_score:.0f} Vol:{liquidity_score:.0f} Bias:{bias_score:.0f})"
            )

        # Find best
        best_instrument = max(scores, key=lambda x: scores[x]['score'])
        best_score = scores[best_instrument]['score']

        # Check threshold
        if best_score < self.min_score_threshold:
            logger.warning(
                f"⚠️ Best instrument ({best_instrument}) scores {best_score:.1f} < "
                f"threshold {self.min_score_threshold}"
            )
            return None

        logger.info(f"\n✅ BEST INSTRUMENT: {best_instrument} ({best_score:.1f}/10)")

        return {
            'instrument': best_instrument,
            'score': best_score,
            'all_scores': scores,
            'details': scores[best_instrument]
        }

    def _fetch_ohlc(self, instrument):
        """Fetch 5-min OHLC data for last 60 minutes"""

        if self.mode == 'dry-run':
            return self._generate_mock_ohlc(instrument)

        # Fetch from broker API (paper/live modes)
        if self.broker_connection is None:
            logger.warning(f"No broker connection available for {instrument}, using mock data")
            return None

        try:
            ohlc = self.broker_connection.get_ohlc(instrument, interval='5min', lookback_minutes=self.lookback_minutes)
            return ohlc

        except Exception as e:
            logger.warning(f"Failed to fetch real OHLC for {instrument}: {e}")
            return None

    def _generate_mock_ohlc(self, instrument):
        """Generate mock OHLC for testing"""

        # Simulate realistic price movements
        import random

        base_prices = {
            'CRUDEOILM': 9110,
            'GOLDM': 152100,
            'SILVERM': 243000,
            'NATGASM': 303
        }

        base = base_prices.get(instrument, 100)
        ohlc = []

        for i in range(12):  # 12 candles = 60 minutes of 5-min data
            open_price = base + random.randint(-50, 50)
            close_price = open_price + random.randint(-30, 80)
            high = max(open_price, close_price) + random.randint(0, 30)
            low = min(open_price, close_price) - random.randint(0, 30)
            volume = random.randint(5000, 50000)

            ohlc.append({
                'time': (datetime.now() - timedelta(minutes=60-i*5)).isoformat(),
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })

            base = close_price  # Walk price

        return ohlc

    def _calculate_trend_strength(self, ohlc_data):
        """Score trend strength 0-10"""

        closes = [c['close'] for c in ohlc_data]

        # Simple moving average
        sma_5 = sum(closes[-5:]) / 5
        sma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else sum(closes) / len(closes)

        # Slope
        slope = (sma_5 - sma_10) / sma_10 * 100

        # ATR (Average True Range)
        atr = self._calculate_atr(ohlc_data)
        atr_score = min(10, atr / 2)  # Normalize to 0-10

        # Trend score
        score = 0

        if slope > 0.5:  # Uptrend
            score += 5
            if slope > 2.0:
                score += 3  # Strong uptrend
            if atr_score > 5:
                score += 2  # With volatility
        elif slope < -0.5:  # Downtrend
            score += 3  # Also tradeable
        else:
            score = 1  # Flat/choppy

        return min(10, score)

    def _calculate_atr(self, ohlc_data):
        """Calculate Average True Range"""

        tr_values = []

        for i in range(1, len(ohlc_data)):
            high = ohlc_data[i]['high']
            low = ohlc_data[i]['low']
            prev_close = ohlc_data[i-1]['close']

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_values.append(tr)

        if not tr_values:
            return 0

        return sum(tr_values) / len(tr_values)

    def _calculate_liquidity(self, instrument, ohlc_data):
        """Score liquidity 0-10"""

        # Volume analysis
        volumes = [c['volume'] for c in ohlc_data]
        avg_volume = sum(volumes) / len(volumes)

        # Spread estimate (in paise, lower is better)
        spread_estimates = {
            'CRUDEOILM': 2,    # 1-2 paise normally
            'GOLDM': 1,       # 0.5-1 paise
            'SILVERM': 5,     # 3-5 paise
            'NATGASM': 5      # 5-10 paise
        }

        expected_spread = spread_estimates.get(instrument, 5)

        score = 0

        # Volume score
        if avg_volume > 40000:
            score += 5
        elif avg_volume > 20000:
            score += 3
        else:
            score += 1

        # Spread score
        if expected_spread < 2:
            score += 5
        elif expected_spread < 5:
            score += 3
        else:
            score += 1

        return min(10, score)

    def _calculate_directional_bias(self, ohlc_data):
        """Score directional momentum 0-10"""

        closes = [c['close'] for c in ohlc_data]

        # RSI calculation
        rsi = self._calculate_rsi(closes)

        # MACD-like (simple momentum)
        ema_5 = self._calculate_ema(closes, 5)
        ema_12 = self._calculate_ema(closes, 12)
        momentum = ema_5 - ema_12

        score = 0

        # RSI-based scoring
        if rsi < 35:  # Oversold
            score += 8  # Strong reversal signal
        elif rsi < 45:
            score += 5
        elif rsi < 55:
            score += 3  # Neutral
        elif rsi < 65:
            score += 5
        else:  # > 65, overbought
            score += 3

        # Momentum confirmation
        if momentum > 0:
            score += 2

        return min(10, score)

    def _calculate_rsi(self, closes, period=14):
        """Calculate RSI"""

        if len(closes) < period:
            return 50  # Neutral if not enough data

        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_ema(self, data, period):
        """Calculate Exponential Moving Average"""

        if len(data) < period:
            return sum(data) / len(data)

        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period

        for price in data[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema
