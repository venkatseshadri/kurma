# 🐢 Project Kurma - MCX Intraday Trading Bot

**Kurma** is an automated MCX (Multi Commodity Exchange) intraday trading bot that trades during evening session (5:00 PM - 11:20 PM IST) using capital released from Varaha's EOD exits.

**Mission:** Generate ₹1,000-₹1,500 daily profit from intraday momentum trading on liquid commodities (Crude Oil, Natural Gas, Gold, Silver).

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- Flattrade or Shoonya broker account (preferably Flattrade for zero brokerage)
- ₹4,00,000 trading margin (released by Varaha at 3:05 PM)
- Linux/macOS or Docker

### 2. Installation
```bash
cd /home/trading_ceo/python-trader
pip install -r requirements.txt
```

### 3. Run Kurma

**Safe Mode (Paper Trading with Real Data)**
```bash
./run_kurma.sh paper flattrade flattrade
```

**Test Mode (Fully Mocked)**
```bash
./run_kurma.sh dry-run
```

**Live Trading (⚠️ Real Orders)**
```bash
./run_kurma.sh live flattrade flattrade
```

See [OPERATIONS.md](./OPERATIONS.md) for all modes and examples.

---

## 📋 What is Intraday MCX Trading?

**Kurma trades commodity futures contracts intraday** (same day, no overnight):

```
Entry (5:30 PM):  BUY 1 Crude Oil contract @ ₹9,110
                  ↓ (price moves up with momentum)
Exit (6:15 PM):   SELL @ ₹9,210 = +₹10,000 profit
                  Position closed before EOD
```

**Key differences from equity trading:**
- **Contracts expire monthly** (different expiry dates)
- **Leverage built-in** (small margin = large exposure)
- **Higher volatility** (commodity price swings are bigger)
- **Evening session** (MCX runs 5 PM - 11:30 PM)
- **Lower volumes** than equity indices (expect wider spreads)

---

## 🎯 Trading Strategy

### Entry Signals
1. **Support Bounce** — Buy at support level when price rebounds on volume
2. **Momentum Breakout** — Buy above resistance with strong volume

### Exit Strategy (Partial TP + Trailing Stop)
```
Position: 1 contract

Tranche 1 (50%):  Exit at +50-100 points → Lock profit immediately
Tranche 2 (25%):  Exit at +100-150 points → Lock more
Tranche 3 (25%):  Trailing Stop Loss (trail 20-30 pts) → Catch trends
```

### Daily Target
- **Conservative:** ₹800-1,000/day
- **Good day:** ₹1,200-1,500/day
- **Excellent day:** ₹2,000+/day

### Daily Loss Limit
- **Max loss:** ₹3,000 (hard stop, no exceptions)

---

## 🔧 Execution Modes

| Mode | Data | Execution | Use Case |
|------|------|-----------|----------|
| **Dry-Run** | Mock | Mock | Development, testing |
| **Paper** | Real | Mock | Monitor with real data |
| **Live** | Real | Real | ⚠️ Production trading |

---

## 🛡️ Safety First

Kurma has **3 layers of safety**:

1. **Dry-Run Default** — All testing modes are mocked by default
2. **Mode Validation** — Cannot accidentally mix live + paper
3. **Hard Exit Times** — Automatic position close at 11:15 PM (before broker auto-close)

See [SAFETY.md](./SAFETY.md) for details.

---

## ⚡ Key Features

✅ **Dynamic Instrument Selection** — Picks best commodity based on current volatility/liquidity  
✅ **Intraday Only** — No overnight risk (same-day entry/exit)  
✅ **Partial TP + TSL** — Sophisticated position management with 3-tranche exits  
✅ **Zero Brokerage** — Uses Flattrade (no commissions!)  
✅ **Real-Time Monitoring** — 1-second quote updates  
✅ **EOD Analytics** — Deep analysis of why trades won/lost  
✅ **Next-Day Predictions** — ML-based forecasts for tomorrow's best instrument  
✅ **Capital Efficient** — Reuses Varaha's released margin  

---

## 📊 Trading Hours

| Session | Hours | Status |
|---------|-------|--------|
| **Morning** | 9:00 AM - 5:00 PM | Varaha (NIFTY/SENSEX) |
| **Evening** | 5:00 PM - 11:20 PM | **Kurma (Commodities)** |
| **Close** | 11:20-11:30 PM | Broker auto-squareoff |

---

## 📚 Documentation

- **[SETUP.md](./SETUP.md)** — Installation & configuration
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — System design & modules
- **[OPERATIONS.md](./OPERATIONS.md)** — How to run, all execution modes
- **[CLI_REFERENCE.md](./CLI_REFERENCE.md)** — All command-line parameters
- **[SAFETY.md](./SAFETY.md)** — Safety mechanisms & rules
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** — Common issues & fixes
- **[CLAUDE.md](./CLAUDE.md)** — For future AI agents

---

## 🚦 Instruments Traded

### Liquid (High Priority)
- **Crude Oil (CRUDEOIL)** — Most liquid, best spreads, high volatility
- **Gold Mini (GOLDM)** — Safe, lower volatility, good for choppy days

### Secondary
- **Natural Gas Mini (NATGASM)** — Volatile, good on weather events
- **Silver Mini (SILVERM)** — Less liquid, wider spreads

---

## 💰 Capital Requirements

| Item | Amount |
|------|--------|
| **Margin from Varaha** | ₹4,00,000 |
| **Kurma Position Size** | ₹50K-₹120K per trade |
| **Max Concurrent Positions** | 1 (sequential trades only) |
| **Daily Risk Limit** | ₹3,000 |

---

## 📞 Quick Commands

### Run Trading Session
```bash
./run_kurma.sh paper flattrade flattrade  # Paper mode
./run_kurma.sh dry-run                     # Test mode
```

### Check Logs
```bash
tail -f /home/trading_ceo/python-trader/kurma_system.log
```

### View EOD Report
```bash
ls -lt /home/trading_ceo/python-trader/kurma_eod_reports/ | head
cat /home/trading_ceo/python-trader/kurma_eod_reports/kurma_eod_*.txt
```

### Monitor Position
```bash
grep "TRANCHE\|EXIT" /home/trading_ceo/python-trader/kurma_system.log
```

---

## 🔄 Margin Flow

```
9:20 AM  → Varaha enters (locks ₹4,00,000 margin)

3:05 PM  → Varaha exits all positions
3:10 PM  → Margin released to account

5:10 PM  → Kurma checks available margin
5:20 PM  → Kurma starts trading (same ₹4,00,000)

11:15 PM → Kurma force-exits all positions
11:20 PM → Margin released

NEXT DAY 9:20 AM → Varaha can reuse ₹4,00,000

Result: 100% margin utilization (morning + evening)
```

---

## 🎓 Learning Path

1. **New to Kurma?** Read [SETUP.md](./SETUP.md) + [OPERATIONS.md](./OPERATIONS.md)
2. **Want to understand design?** Read [ARCHITECTURE.md](./ARCHITECTURE.md)
3. **Ready to trade?** Run `./run_kurma.sh dry-run` first, then paper mode
4. **Optimize parameters?** Check [CLI_REFERENCE.md](./CLI_REFERENCE.md) + EOD reports
5. **Going live?** Read [SAFETY.md](./SAFETY.md) completely before `--live-execution`

---

## ⚠️ Important Notes

- **Intraday only:** Positions MUST be closed by 11:15 PM (broker auto-closes at 11:20 PM)
- **Sequential trading:** Only 1 active trade at a time (avoid margin conflicts)
- **Paper first:** Test in paper mode for ₹5,000+ profit before going live
- **Monitor closely:** Even in paper mode, watch for slippage and spread widening
- **Daily loss stop:** If down ₹3,000, STOP TRADING (don't chase losses)

---

*Last Updated: April 30, 2026*  
*Status: Ready for Production*  
*Capital Efficiency: ₹4,00,000 + ₹4,00,000 = ₹8,00,000 daily capacity*
