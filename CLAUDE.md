# Kurma — MCX Evening Bot

MCX intraday bot trading 5:00 PM – 11:20 PM IST using Varaha's released margin. Dynamic instrument selection + partial-TP / trailing-SL exits.

**Entry:** `kurma_main.py` → `KurmaOrchestrator.run_orchestrator()`

## Architecture

```
kurma_main.py                Master orchestrator
├── kurma_selector.py        Phase 1 — score 4 commodities, pick best (>5.0/10)
├── kurma_momentum.py        Phase 2 — entry (support bounce or breakout) + 3-tranche exit
├── kurma_monitor.py         Phase 3 — real-time MTM tracking (placeholder for tick loop)
└── kurma_eod_analyzer.py    Phase 4 — EOD reports → next-day recommendations
```

Selector scoring: Trend × 0.5 + Liquidity × 0.3 + Bias × 0.2. If best < 5.0, skip the session.

Exit system (3 tranches): T1 50% at TP1, T2 25% at TP2, T3 25% on trailing stop (trails behind high; only moves up). Per-instrument TP/TSL points live in `config.yaml`.

## Execution modes

| Mode | Command | Data | Orders | Auth |
|---|---|---|---|---|
| Dry-Run | `./run_kurma.sh dry-run` | Mock | Mock | No |
| Paper | `./run_kurma.sh paper flattrade flattrade` | Real | Mock | Yes |
| Live | `./run_kurma.sh live flattrade flattrade` | Real | Real | Yes |

**Safety:** Live mode requires `--live-execution` AND `--confirm-live-execution=yes` (case-sensitive, exact `yes`). Cannot mix with `--dry-run`.

## Common commands

```bash
# Test
./run_kurma.sh dry-run

# Paper with real data
./run_kurma.sh paper flattrade flattrade

# Logs
tail -f /home/trading_ceo/projects/python-trader/kurma_system.log

# EOD reports
ls -lt /home/trading_ceo/projects/python-trader/kurma_eod_reports/ | head
```

## Critical rules

1. **Hard exit at 11:15 PM IST** — non-negotiable. MCX auto-squareoff is 11:20 PM and will fill leftovers with bad slippage.
2. **Selector threshold 5.0 is a floor.** Skipping a weak session beats trading it. Do not lower.
3. **Peak liquidity 6:00 PM – 10:00 PM.** Position sizing increases (e.g., 2 contracts vs 1) during peak only.
4. **Use Flattrade, not Shoonya.** Zero brokerage vs ₹5/order — material at intraday volume.
5. **3-tranche exit is the strategy.** Don't simplify to a fixed stop. Removing partial TPs breaks the system's edge.
6. **Margin handoff.** Verify Varaha released margin (~3:10 PM settle) before starting.

## Per-instrument config

All TP/TSL/lot/max-loss values live in `config.yaml` keyed by symbol (CRUDEOIL, GOLDM, SILVERM, NATGASM). Don't hard-code in scripts.

## Reference docs

`OPERATIONS_REFERENCE.md` (this dir) — full timeline, per-instrument params, selector scoring breakdown, exit-strategy walkthrough, configuration hierarchy, key class map, operator notes.

Also: `README.md`, `SETUP.md`, `ARCHITECTURE.md`, `OPERATIONS.md`, `SAFETY.md` in this dir.
