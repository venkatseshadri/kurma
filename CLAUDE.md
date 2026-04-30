# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Kurma** is an MCX (Multi Commodity Exchange) intraday trading bot that trades during evening session (5:00 PM - 11:20 PM IST) using capital released by Varaha's EOD exits. It employs dynamic instrument selection, momentum-based entry logic, and sophisticated exit management (partial TP + trailing stop loss).

**Location:** `/home/trading_ceo/python-trader/kurma/`  
**Entry point:** `kurma_main.py`  
**Daily execution:** 5:00 PM - 11:20 PM IST (reuses Varaha's released margin)

---

## Core Architecture

Kurma is a **4-phase orchestrated system** operating in evening session only:

### Module Layout

```
kurma_main.py          Master orchestrator (args, mode, phase sequencing)
├── Phase 1: kurma_selector.py    Scan all 4 commodities, score trends, select best
├── Phase 2: kurma_momentum.py    Entry/exit logic with Partial TP + Trailing SL
├── Phase 3: kurma_monitor.py     Real-time position tracking (future: tick loop)
└── Phase 4: kurma_eod_analyzer.py Deep analysis + next-day recommendations
```

### Key Responsibilities

1. **kurma_selector.py** — Dynamic commodity selection engine. Scores each instrument on:
   - **Trend Strength** (50% weight) — ATR, SMA slope, direction
   - **Volatility/Liquidity** (30% weight) — Spreads, volume, slippage risk
   - **Directional Bias** (20% weight) — RSI, MACD, momentum confirmation
   
   Only trades if best instrument scores > 5.0/10 (capital preservation first).

2. **kurma_momentum.py** — Entry/exit logic with sophisticated position management:
   - **Support Bounce** — Primary entry: buy at support on volume
   - **Momentum Breakout** — Secondary entry: breakout above resistance
   - **Partial TP + TSL** — 3-tranche exits:
     - T1: 50% position at TP1 (+50-100 pts, locks profit)
     - T2: 25% position at TP2 (+100-150 pts, locks more profit)
     - T3: 25% position with TSL (trails behind high, captures trends)

3. **kurma_monitor.py** — Real-time P&L tracking (placeholder for future tick loop):
   - Fetch quotes every 1 second
   - Update position MTM
   - Trigger tranche exits when TP/TSL levels hit
   - Force exit at 11:15 PM (hard stop)

4. **kurma_eod_analyzer.py** — Comprehensive end-of-day analysis:
   - **Trade-level:** Score entry quality, exit quality, R:R ratio achieved
   - **Market:** Which instruments scored best, why did trends occur?
   - **Deep research:** External catalysts, technical patterns, correlations
   - **Recommendations:** Parameter tweaks for next session, ML predictions

---

## Execution Modes (Critical)

Kurma has **3 mutually exclusive modes** determined by command-line flags:

| Mode | Command | Data | Orders | Auth | Use |
|------|---------|------|--------|------|-----|
| **Dry-Run** | (default or `--dry-run`) | Mock | Mock (no API) | No | Testing, development |
| **Paper** | `--data-broker X --exec-broker Y` | Real | Mock (no API) | Yes | Real data, no risk |
| **Live** | Above + `--live-execution --confirm-live-execution=yes` | Real | Real | Yes | ⚠️ Production only |

**Safety rules:**
- Cannot mix `--dry-run` + `--live-execution` (will error)
- Live mode requires BOTH flags AND exact confirmation text
- Dry-run overrides all broker params

---

## Common Development Commands

### Test (Fully Mocked)
```bash
cd /home/trading_ceo/python-trader
./run_kurma.sh dry-run
```

### Monitor with Real Data (Paper Mode)
```bash
./run_kurma.sh paper flattrade flattrade
```

### Live Trading (⚠️ Real Orders)
```bash
./run_kurma.sh live flattrade flattrade
# Will prompt for confirmation
```

### Direct Python Execution
```bash
cd kurma
python3 kurma_main.py --dry-run
python3 kurma_main.py --data-broker flattrade --exec-broker flattrade
```

### Check Logs
```bash
tail -100 /home/trading_ceo/python-trader/kurma_system.log
tail -f /home/trading_ceo/python-trader/kurma_system.log    # Follow live
```

### Check Session Report
```bash
ls -lt /home/trading_ceo/python-trader/kurma_eod_reports/ | head
cat /home/trading_ceo/python-trader/kurma_eod_reports/kurma_eod_TIMESTAMP.txt
```

---

## Trading Timeline (IST)

```
3:05 PM   Varaha exits all positions → Margin released
3:10 PM   Margin settles in broker account

5:00 PM   ┌──────────────────────────────────────┐
          │ MCX evening session OPENS             │
          │                                      │
5:10 PM   ├─ Kurma Selector runs                 │
5:15 PM   │ (Score all 4 commodities, pick best) │
          │                                      │
5:20 PM   ├─ Momentum Bot starts trading         │
5:30 PM   │ Entry: Support bounce or momentum    │
6:00 PM   │                                      │
          │ PEAK LIQUIDITY WINDOW (6-10 PM)      │
8:00 PM   │ Trade 2 entry (if available)         │
          │                                      │
10:00 PM  │ Spreads widening, volume declining   │
11:00 PM  │                                      │
11:15 PM  ├─ FINAL EXIT: Close all positions     │
          │ (5 min before broker auto-close)     │
          │                                      │
11:20 PM  ├─ Broker auto-squareoff               │
11:30 PM  │ MCX CLOSES                           │
          └──────────────────────────────────────┘

11:35 PM  ┌──────────────────────────────────────┐
          │ EOD Analyzer runs                     │
11:50 PM  │ Generate reports, next-day forecast  │
          └──────────────────────────────────────┘

12:00 AM  Ready for next day
```

---

## Instrument-Specific Parameters

Per `config.yaml`, each commodity has unique parameters:

### Crude Oil (CRUDEOIL)
- **Lot:** 100 barrels
- **P&L per point:** ₹100
- **TP levels:** +100 pts (T1), +150 pts (T2)
- **TSL:** 30 points behind high
- **Position:** 1 contract normal, 2 during peak hours
- **Max loss:** ₹4,000 per trade

### Gold Mini (GOLDM)
- **Lot:** 100 grams
- **P&L per point:** ₹100
- **TP levels:** +50 pts, +100 pts
- **TSL:** 20 points
- **Position:** 1 contract
- **Max loss:** ₹1,500 per trade

### Silver Mini (SILVERM)
- **Lot:** 5 kg
- **P&L per point:** ₹5,000
- **TP levels:** +75 pts, +125 pts
- **TSL:** 30 points
- **Position:** 1 contract
- **Max loss:** ₹1,500 per trade

### Natural Gas Mini (NATGASM)
- **Lot:** 250 MMBtu
- **P&L per point:** ₹25
- **TP levels:** +50 pts, +75 pts
- **TSL:** 25 points
- **Position:** 0.5 contract (volatile)
- **Max loss:** ₹1,500 per trade

---

## Selector Logic (How Best Instrument is Chosen)

```
At 5:10 PM, Kurma Selector analyzes 60 minutes of 5-min candles:

For each commodity:
  Trend Score (0-10):
    - ATR (volatility)
    - SMA slope (direction)
    - Confluence signals
  
  Liquidity Score (0-10):
    - Bid-ask spreads
    - Volume per minute
    - Slippage risk
  
  Bias Score (0-10):
    - RSI (momentum)
    - MACD (confirmation)
    - Overbought/oversold levels

FINAL SCORE = (Trend×0.5) + (Liquidity×0.3) + (Bias×0.2)

Example:
  Crude Oil:  9.0 (Trend) + 8.0 (Liq) + 8.0 (Bias) = 8.5 ⭐ PICK THIS
  Gold Mini:  3.0 (choppy) + 7.0 (Liq) + 4.0 (Bias) = 4.4 (SKIP)
  Nat Gas:    7.0 (Trend) + 6.0 (Liq) + 6.0 (Bias) = 6.5 (secondary)
```

Only trade if best score > 5.0 (threshold). If all < 5, skip session.

---

## Exit Strategy: Partial TP + Trailing Stop Loss

### The 3-Tranche System

```
Entry: Buy 1 contract at ₹9,110

TRANCHE 1 (50% = 0.5 contracts):
  Exit at: +100 points = ₹9,210
  Profit: +₹5,000
  → Locks first half of profit immediately

TRANCHE 2 (25% = 0.25 contracts):
  Exit at: +150 points = ₹9,260
  Profit: +₹7,500 (cumulative)
  → Locks second chunk

TRANCHE 3 (25% = 0.25 contracts):
  Exit: Trailing Stop Loss
  Trail 30 points behind high
  
  Example:
    High: ₹9,280 → TSL at ₹9,250
    High: ₹9,300 → TSL at ₹9,270 (trail follows up)
    Price: ₹9,265 → TSL hit, exit at ₹9,265
    Profit: +₹6,625
  
TOTAL P&L = ₹5,000 + ₹7,500 + ₹6,625 = ₹19,125 ✅

Key:
• TSL only moves UP (never down)
• SL never moves against position
• Locks profits while letting trends run
```

### Why This Works

✅ **Capital preservation:** 75% locked in at known profit levels  
✅ **Trend capture:** 25% runner with TSL catches big moves  
✅ **No "giving back gains":** SL stops below highest point  
✅ **Intraday-friendly:** Quick profit locks, low holding risk  

---

## Configuration Hierarchy

1. **Command-line arguments** (highest priority)
   ```bash
   ./run_kurma.sh paper flattrade flattrade --debug
   ```

2. **Environment variables** (optional)
   ```bash
   KURMA_MODE=paper ./run_kurma.sh
   ```

3. **config.yaml** (file-based defaults)
   ```yaml
   instruments:
     CRUDEOIL:
       tp_1_points: 100
       tsl_points: 30
   ```

4. **Code defaults** (lowest priority)
   ```python
   DEFAULT_TP_1 = 50
   DEFAULT_TSL = 20
   ```

---

## Key Classes & Entry Points

| Class | Module | Purpose |
|-------|--------|---------|
| `KurmaOrchestrator` | kurma_main.py | Master control, mode logic, phase sequencing |
| `KurmaSelector` | kurma_selector.py | Score commodities, pick best trend |
| `KurmaMomentum` | kurma_momentum.py | Entry/exit logic, TP/TSL management |
| `PartialTPTrailingStopLogic` | kurma_momentum.py | Position tracking with tranche exits |
| `KurmaEODAnalyzer` | kurma_eod_analyzer.py | Trade analysis, research, recommendations |

**Main entry point:** `kurma_main.py:main()` → parses args → `KurmaOrchestrator.run_orchestrator()`

---

## Important Notes for Agents

1. **MCX Hours Correct:** Evening session 5:00 PM - 11:20 PM IST (NOT 10 PM!). Hard exit at 11:15 PM to allow 5-min buffer before auto-squareoff.

2. **Dynamic Selection:** Instrument chosen at 5:10 PM based on that moment's conditions. Not hardcoded. Agent should trust selector algorithm, not override.

3. **Partial Exits Critical:** TP+TSL system prevents common intraday mistakes (giving back gains, holding losers). Do not simplify to fixed stop-loss only.

4. **Peak Liquidity:** 6:00 PM - 10:00 PM IST is best trading window. Spreads widen after 10 PM. Position sizing should increase during peak hours (2 contracts vs 1).

5. **Margin Handoff:** Kurma receives margin from Varaha exit at ~3:10 PM. Should verify available margin before starting trades.

6. **Paper Mode is Safe:** Run in paper mode first. Real data + simulated orders = risk-free testing with actual market conditions.

7. **Zero Brokerage:** Use Flattrade (zero brokerage) for optimal P&L. Shoonya charges ₹5/order (high for intraday).

8. **EOD Report is Gold:** EOD analyzer identifies what worked/failed. Check `/home/trading_ceo/python-trader/kurma_eod_reports/` daily for insights.

9. **Selector Threshold:** Min score 5.0 is deliberate. Better to skip a session than lose money on weak setups. Agents should not lower this.

10. **Time Hard Stops:** 11:15 PM hard exit is non-negotiable. MCX auto-closes at 11:20 PM. Broker will force-square leftover positions with bad slippage.

---

## When in Doubt

1. Check logs: `tail -50 /home/trading_ceo/python-trader/kurma_system.log`
2. Run dry-run first: `./run_kurma.sh dry-run`
3. Review ARCHITECTURE.md for system design
4. Check config.yaml for parameter definitions
5. Look at EOD reports from yesterday: identify what worked, why

---

## Documentation Reference

- **README.md** — Overview, quick start
- **SETUP.md** — Installation, credential setup
- **ARCHITECTURE.md** — Detailed system design, data flows
- **OPERATIONS.md** — All execution modes with examples
- **CLI_REFERENCE.md** — Parameter reference
- **SAFETY.md** — Safety mechanisms, guardrails
- **00_START_HERE.txt** — Navigation guide
