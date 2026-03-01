# ÉTAPE 24 - Trader Preparation & Training Guide
## Live Trading Psychological & Technical Preparation

**Date:** 24 Février 2026
**Status:** Ready for ÉTAPE 25 Phase 1 Startup
**Target:** Enable successful live trading execution with minimal risk

---

## Table of Contents

1. [Psychological Preparation](#psychological)
2. [Technical Preparation](#technical)
3. [Daily Operating Procedures](#daily-procedures)
4. [Risk Management Enforcement](#risk-enforcement)
5. [Emergency Response Playbook](#emergency-playbook)
6. [Pre-Live Trading Checklist](#pre-live-checklist)

---

## Psychological Preparation {#psychological}

### Understanding Trading Psychology

Live trading is **fundamentally different** from backtesting:

| Aspect | Backtesting | Live Trading |
|--------|-------------|--------------|
| Risk | Hypothetical | **Real Capital** |
| Emotional | None | **High Stress** |
| Speed | Analysis available | **Immediate Decisions** |
| Losses | Abstract numbers | **Real Pain** |
| Wins | Satisfying | **Real Profit** |

### The 3 Killer Mistakes in Live Trading

**Mistake #1: Overriding Stop Losses**
- Problem: "This trade will come back - I'll hold"
- Reality: Small losses become large losses
- Consequence: Violates system rules = account destruction
- Solution: NEVER override a stop loss. EVER.

**Mistake #2: Revenge Trading**
- Problem: After a loss, want to "make it back" immediately
- Reality: Emotional decisions are terrible decisions
- Consequence: 2-3 revenge trades after a loss usually = bigger loss
- Solution: If you take 3 losses, STOP for rest of day

**Mistake #3: Ignoring Daily Loss Limits**
- Problem: "If I'm down $1,500, let me try one big trade to make it back"
- Reality: Violating your own rules destroys discipline
- Consequence: One $1,500 loss becomes a $5,000 loss
- Solution: When daily limit hit, STOP. PERIOD.

### Emotional Discipline Training

**Before Each Trading Day:**
- [ ] Sleep 7-8 hours (fatigue = poor decisions)
- [ ] Exercise or meditation (calm mind)
- [ ] Review your 10 trading rules (commitment)
- [ ] Check your risk limits (reality check)
- [ ] Say out loud: "I will follow my system exactly"

**During Trading:**
- [ ] NO revenge trading
- [ ] NO checking losses constantly
- [ ] NO changing stops or targets
- [ ] NO hope trading
- [ ] NO "just one more"

**After Each Trade:**
- [ ] Log immediately (not later)
- [ ] NO emotional analysis (save for evening)
- [ ] Focus on next signal (not last result)
- [ ] Stick to position sizing (no revenge)

### The Trader's Mindset

**Believe This:**
> "I follow the system. The system works. I don't need to beat the market, I just need to execute my strategy with discipline."

**Key Principles:**
1. **Process > Results:** Focus on executing rules, not on making money
2. **Small Losses > Big Losses:** Stop losses save capital
3. **Discipline > Genius:** Follow rules > Try clever trades
4. **Long Term > Today:** This is month 1 of years of trading
5. **Risk Managed > Uncontrolled Risk:** 2% daily loss limit is FREEDOM

---

## Technical Preparation {#technical}

### System Setup Verification

**Before going live, verify:**

```
[ ] Broker account funded with Phase 1 capital ($2,000-$5,000)
[ ] TWS (Trader Workstation) installed and tested
[ ] API enabled on port 7498 (paper trading)
[ ] Market data subscriptions active
[ ] Backup internet connection available (hotspot)
[ ] Monitor setup (dual monitors recommended)
[ ] Calculator for quick math (position sizing, loss limits)
[ ] Trading journal ready (physical or digital)
```

### Required Scripts Running

**BEFORE MARKET OPEN:**
```bash
# 1. Start monitoring system
python src/trading/daily_monitoring.py --phase morning

# 2. Check broker connection
python tests/test_broker_integration.py

# 3. Load today's data
python src/analysis/data_loader.py --date=TODAY
```

**DURING TRADING:**
```bash
# 1. Signal generation every 30 minutes
python src/analysis/signal_generator.py --mode=live

# 2. Position monitor (keeps running)
python src/trading/position_monitor.py --mode=streaming
```

### Hardware Requirements

Minimum setup:
- Laptop/Desktop with 4GB RAM
- Stable internet (critical!)
- **Backup internet (smartphone hotspot on standby)**
- Two monitors (one for charts, one for orders)
- Comfortable chair (you'll be here 6.5 hours)

Recommended:
- Dedicated trading computer
- UPS (Uninterruptible Power Supply)
- Dual monitors, mechanical keyboard
- Professional trading desk setup

### Software Stack

```
Programming:      Python 3.9+
Broker API:       Interactive Brokers TWS
Data:             Yahoo Finance / IB
Monitoring:       Custom Python dashboard
Backup:           Excel spreadsheet for manual operations
```

---

## Daily Operating Procedures {#daily-procedures}

### PHASE 1 - Morning (8:30 AM - 9:30 AM)

**Step 1: System Health Check (5 min)**
```
[ ] Laptop booted, all scripts running
[ ] TWS connection established
[ ] Broker account balance visible
[ ] Market data streaming (live quotes updating)
[ ] Internet speed test: ping < 50ms to broker
```

**Step 2: Market Analysis (15 min)**
```
[ ] Check market open status
[ ] Review S&P 500 futures (pre-market trend)
[ ] Check economic calendar (any major releases today?)
[ ] Review yesterday's market close (context)
[ ] Check weather/news (anything unusual?)
```

**Step 3: Position Review (5 min)**
```
[ ] Review any overnight news on MSFT
[ ] Check MSFT price action pre-market
[ ] Note key support/resistance levels
[ ] Plan entry and exit points for the day
```

**Step 4: Trading Plan (5 min)**
```
[ ] Write down daily target return: +2% to +5%
[ ] Write down daily stop loss: -2% (= -$100 on $5k)
[ ] Write down max shares to buy: ____ (from position_sizing.py)
[ ] Write down entry prices: __________
[ ] Write down exit prices: __________
```

**Step 5: Final Readiness (5 min)**
```
[ ] All systems ready GO/NO-GO decision
[ ] Trading rules printed and visible
[ ] Calculator on desk and ready
[ ] Journal/notepad for logging trades
[ ] Phone ready for emergency decisions
[ ] Alert system armed
```

### PHASE 2 - During Session (9:30 AM - 3:30 PM)

**Every 30 Minutes:**
```
[ ] Check open positions
[ ] Check daily P&L against target and limit
[ ] Verify stops are still active in TWS
[ ] Check for any system alerts
[ ] Review new signals generated
[ ] NO changes to existing stop losses
```

**When Taking a Trade:**
```
[ ] Verify signal quality (why are we entering?)
[ ] Check daily loss limit not hit
[ ] Check position limits not exceeded
[ ] Calculate shares based on Kelly (from position_sizing.py)
[ ] Enter BUY order with STOP ORDER simultaneously
[ ] Log trade in journal IMMEDIATELY
[ ] Set TAKE PROFIT order
[ ] Step back and monitor
```

**If Trade Goes Against You:**
```
[ ] Let the stop loss execute (AUTOMATIC)
[ ] DO NOT try to "save" the trade
[ ] DO NOT move the stop higher
[ ] Log the loss in journal
[ ] Move on to the next signal
```

**If Trade Goes For You:**
```
[ ] Watch for take profit to hit
[ ] If TP hits, great! Log profit
[ ] If still in profit but approaching time limit (30 days):
     - Consider taking profit manually
     - Let system determine exit if time is left
[ ] NEVER try to "squeeze more" from a winner
```

### PHASE 3 - Afternoon (3:30 PM - 4:00 PM)

**Step 1: Close All Positions (by 4:00 PM)**
```
Hard rule: NO POSITIONS held overnight in Phase 1
[ ] Check all positions are closed
[ ] Verify cash position = initial capital (approx)
[ ] Take screenshots of final positions
[ ] Confirm P&L is finalized
```

**Step 2: Daily Report (10 min)**
```
[ ] Calculate total trades: _____
[ ] Calculate total P&L: $_____
[ ] Calculate daily return %: _____%
[ ] Win rate today: ____/____ = _____%
[ ] Worst trade: _____ (ticker, loss)
[ ] Best trade: _____ (ticker, profit)
[ ] System performance: Normal/Degraded
```

**Step 3: Evening Review (30 min)**
```
[ ] Export trading log from TWS
[ ] Log all trades in master trading journal
[ ] Review winning trades - what went right?
[ ] Review losing trades - what went wrong?
[ ] Are you following the rules? ✓ or ✗
[ ] Confidence level tomorrow: 1-10
[ ] Any system issues to fix tonight?
```

---

## Risk Management Enforcement {#risk-enforcement}

### The 10 Golden Rules (MANDATORY)

```
1. STOP LOSS = SACRED
   - Every position MUST have a stop loss
   - Stop loss MUST be executed
   - NO EXCEPTIONS EVER

2. DAILY LOSS LIMIT = -2% (HARD STOP)
   - If daily P&L = -2%, STOP ALL TRADING
   - No ifs, ands, or buts
   - This is for your protection

3. KELLY ALLOCATION = PREDEFINED
   - Shares calculated before entry
   - No improvisation allowed
   - Risk per trade = Kelly fraction × capital

4. TRADING HOURS ONLY
   - 9:30 AM - 3:30 PM ET only
   - NO pre-market
   - NO after-hours
   - CLOSE all by 4:00 PM

5. REGIME-DEPENDENT TRADING
   - BULL/BEAR/SIDEWAYS: All go
   - CONSOLIDATION: Skip trading
   - Check regime at open daily

6. POSITION MONITORING = REQUIRED
   - Check every 30 minutes
   - 6.5 hours ÷ 0.5 hours = 13 checks/day
   - NO skipping monitoring

7. EMOTIONAL DISCIPLINE = ESSENTIAL
   - NO revenge trading
   - NO override stops
   - NO hope trading
   - Follow system exactly

8. BROKER OPERATIONS = CRITICAL
   - Connection verified at open
   - Orders executed correctly
   - P&L reconciled at close
   - System health checked daily

9. DOCUMENTATION = MANDATORY
   - Every trade logged
   - Daily report generated
   - Weekly review required
   - Monthly deep analysis

10. EMERGENCY PROCEDURES = MEMORIZED
    - Know how to close manually
    - Know who to call (broker support)
    - Know what to do if broker down
    - Know how to restore from backup

```

### Risk Limits (Per Phase)

**Phase 1 (MSFT Only):**
```
Daily loss limit:   -$100 (-2% of $5,000)
Weekly loss limit:  -$250 (-5% of $5,000)
Max consecutive:    5 losses = pause 1 day
Max position time:  5 trading days
```

**Phase 2 (MSFT + GOOGL):**
```
Daily loss limit:   -$200 (-2% of $10,000)
Weekly loss limit:  -$500 (-5% of $10,000)
Max consecutive:    5 losses = pause 1 day
Max position time:  10 trading days
```

**Phase 3 (All 4 Tickers):**
```
Daily loss limit:   -$2,000 (-2% of $100,000)
Weekly loss limit:  -$5,000 (-5% of $100,000)
Max consecutive:    5 losses = pause 1 day
Max position time:  30 trading days
```

---

## Emergency Response Playbook {#emergency-playbook}

### Scenario 1: Broker Connection Lost

**IF: Connection lost for < 5 minutes**
```
1. Restart TWS connection
2. Verify positions and orders still in place
3. Resume normal trading
4. Document in journal: "Connection lost 9:43 AM - resolved 9:47 AM"
```

**IF: Connection lost for 5-15 minutes**
```
1. Attempt TWS restart
2. Check backup internet (hotspot)
3. Call broker support: [PHONE NUMBER]
4. If positions exist, close manually via phone
5. Document incident, await resolution
6. Resume trading only after connection verified
```

**IF: Connection lost for > 15 minutes**
```
1. CLOSE ALL POSITIONS IMMEDIATELY via phone
2. Ask broker to confirm closes
3. Stop trading for the day
4. Contact technical support (broker)
5. Investigate what happened
6. Do NOT resume trading until issue resolved
```

### Scenario 2: Daily Loss Limit Hit

**When Daily P&L = -2%:**
```
1. STOP ALL TRADING (non-negotiable)
2. Close all open positions at market
3. Set daily flag: NO MORE TRADES TODAY
4. Log the event in the journal
5. Document what trades caused the loss
6. Review - can we avoid this pattern tomorrow?
7. Take 30-minute break
8. Resume next trading day
9. Analyze lessons learned
```

### Scenario 3: System Crash

**If trading system crashes mid-day:**
```
1. DO NOT PANIC - positions are still in broker system
2. Go to TWS and verify all positions directly
3. Check that stops and targets are still active
4. Restart trading system
5. Verify system state matches TWS state (reconcile)
6. Resume trading if everything matches
7. If discrepancies, contact broker support for reconciliation
```

### Scenario 4: Excessive Slippage

**If slippage > 0.10% (unusual):**
```
1. Check market liquidity - is volume low?
2. Verify order types (market orders cause slippage)
3. Switch to limit orders (example: buy limit 1% above current)
4. Monitor next few trades for improvement
5. If slippage persists, contact broker technical support
6. Possible issue: internet lag or broker performance
```

### Scenario 5: Win Rate Below 40%

**If any 10-trade window shows < 40% win rate:**
```
1. Pause trading for 1-2 hours
2. Review last 10 trades - what went wrong?
3. Check if market regime changed (run regime detector)
4. Verify stops and targets are correct
5. Check signal quality (are signals good or degraded?)
6. If signals degraded, wait for regime clarity
7. Resume trading once confident in signals
```

---

## Pre-Live Trading Checklist {#pre-live-checklist}

### Hardware & Software

- [ ] Laptop/computer tested and stable
- [ ] Dual monitors (or single monitor ready)
- [ ] TWS installed and tested
- [ ] Python scripts tested and working
- [ ] Backup internet (hotspot) available
- [ ] UPS/power backup (if available)

### Broker Account

- [ ] Account opened with Interactive Brokers
- [ ] Account verified and approved
- [ ] Initial capital deposited ($2,000-$5,000)
- [ ] TWS login working
- [ ] API enabled on port 7498
- [ ] Paper trading mode tested
- [ ] Market data subscriptions active
- [ ] Broker phone number in wallet

### Trading System

- [ ] Position sizing script tested: `position_sizing.py`
- [ ] Monitoring dashboard working: `live_monitoring.py`
- [ ] Broker integration validated: `test_broker_integration.py`
- [ ] Configuration loaded: `live_trading_config.py`
- [ ] Daily procedures documented and understood
- [ ] Backup procedures tested manually

### Psychological

- [ ] Read and re-read this guide (all sections)
- [ ] Memorized 10 golden rules
- [ ] Committed to daily loss limit (-2%)
- [ ] Committed to stop loss enforcement
- [ ] Identified and addressed fear/overconfidence
- [ ] Partner/family informed (support system)
- [ ] Arranged quiet trading workspace
- [ ] Committed to 2.5 hour daily commitment

### Paper Trading Validation

- [ ] Paper traded for 5 days minimum
- [ ] Win rate > 40% achieved
- [ ] System executed without crashes
- [ ] Daily procedures practiced
- [ ] Emergency procedures practiced
- [ ] Felt comfortable with order execution
- [ ] Ready for live trading with real money

### Financial

- [ ] Initial capital ready and funded
- [ ] Separate account for trading (not mixed with personal)
- [ ] Capital is "trading capital" not "rent money"
- [ ] Spouse/partner approves if married
- [ ] Understand: can lose this capital
- [ ] Have emergency fund (3-6 months living expenses)

### Final Decision

**Are you ready for Phase 1?**

If all checkboxes above are CHECKED ✓, then:

**YES, I AM READY FOR PHASE 1 LIVE TRADING**

Signature: _________________ Date: __________

If ANY checkbox is not checked, wait and prepare more. This is not a race.

---

## Success Metrics for Phase 1 Continuation

**To advance from Phase 1 (MSFT) to Phase 2 (MSFT + GOOGL):**

```
✓ 5 trading days completed
✓ Win rate ≥ 40%
✓ No system crashes
✓ Followed all rules perfectly
✓ Comfortable with order execution
✓ Daily P&L tracking accurate
✓ No emotional trades
✓ Broker connection stable

If all met: Advance to Phase 2
If any failed: Extend Phase 1 by 5 days
```

---

## Final Thoughts

> "The money will come. First comes discipline. Then comes success."

This is the beginning of your journey. Phase 1 is 5 days. If successful, you accumulate capital and scale. Your first year target is to prove the system works, not to get rich.

**Remember: Your job is to execute the system. The system's job is to make money.**

Start with MSFT. Small capital. Strict discipline. Document everything. Scale gradually if successful.

Good luck. You've got this.

