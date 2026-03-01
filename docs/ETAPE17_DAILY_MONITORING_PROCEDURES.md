# ÉTAPE 17 - DAILY MONITORING & OPERATIONAL PROCEDURES

**Project:** Algo Trading System  
**Date:** 24 Février 2026  
**Version:** 1.0 - Live Trading Operational Manual  
**Status:** Ready for Daily Use

---

## TABLE OF CONTENTS

1. [Overview & Purpose](#overview--purpose)
2. [Daily Monitoring Schedule](#daily-monitoring-schedule)
3. [Morning Procedures](#morning-procedures)
4. [During Session Procedures](#during-session-procedures)
5. [Afternoon Procedures](#afternoon-procedures)
6. [Evening Procedures](#evening-procedures)
7. [Weekly Review](#weekly-review)
8. [Monthly Deep Analysis](#monthly-deep-analysis)
9. [Alert Management](#alert-management)
10. [Emergency Procedures](#emergency-procedures)
11. [Documentation & Record Keeping](#documentation--record-keeping)

---

## OVERVIEW & PURPOSE

### What is Daily Monitoring?

Daily monitoring is the systematic review of your trading system to ensure it's operating correctly, adhering to risk management rules, and performing as expected based on backtests.

### Why is Daily Monitoring Critical?

1. **Early Problem Detection:** Catch issues before they become major losses
2. **Risk Management Enforcement:** Ensure all limits and stops are being respected
3. **Performance Tracking:** Validate actual performance vs. backtests
4. **Psychological Health:** Give yourself confidence the system is working
5. **Regulatory Compliance:** Document all trading activity
6. **Optimization Data:** Collect real-market data for future improvements

### Daily Monitoring is NOT Optional

This is as important as the trading strategy itself. Many traders fail because they don't monitor properly. **NO EXCEPTIONS.**

---

## DAILY MONITORING SCHEDULE

### Complete Daily Cycle

| Time | Duration | Activity | Priority |
|------|----------|----------|----------|
| **08:30** | 45 min | Morning Checklist | **CRITICAL** |
| **09:30-11:00** | Every 30 min | Session monitoring check 1,2 | IMPORTANT |
| **11:00-13:00** | Every 30 min | Session monitoring check 3,4 | IMPORTANT |
| **13:00-15:30** | Every 30 min | Session monitoring check 5,6 | IMPORTANT |
| **15:30-16:00** | 30 min | Afternoon Checklist | **CRITICAL** |
| **16:00-17:00** | 60 min | Evening Checklist | **CRITICAL** |
| **17:30+** | Variable | Weekly review (Fridays) | IMPORTANT |

### Time Commitment

- **Daily:** ~2.5 hours (including trading execution)
- **Weekly:** +2 hours (Friday end-of-week)
- **Monthly:** +4 hours (end-of-month review)

### Total Monthly Investment

- **Daily monitoring:** ~50 hours
- **Weekly review:** ~10 hours
- **Monthly analysis:** +4 hours
- **Total:** ~64 hours per month

**This is a full-time job. Budget accordingly.**

---

## MORNING PROCEDURES

### TIMING: 08:30 AM ET (90 minutes before market open)

### PURPOSE

Validate system readiness, verify all connections, prepare trading plan.

### STEP-BY-STEP CHECKLIST

#### 1. System Startup (10 min)
```
☐ Start broker software (TWS / API terminal)
☐ Start trading system (Python environment)
☐ Start monitoring dashboard
☐ Start backup/logging system
```

#### 2. Broker Connection Test (10 min)
```
☐ Test API connection to broker
☐ Verify account credentials working
☐ Check account balance on broker statement
☐ Verify no broker maintenance/issues
☐ Test order submission (mock trade)
☐ Cancel mock trade
```

**Command to run:**
```bash
python src/trading/test_broker_connection.py
```

**Expected output:**
```
✓ Connection successful
✓ Account balance: $100,000.00
✓ Order submission working
✓ API latency: 150ms (good)
```

#### 3. Market Status Verification (5 min)
```
☐ Check if market is open today (no holidays?)
☐ Check official US market calendar
☐ Verify trading hours (9:30 AM - 4:00 PM ET)
☐ Check for early closes (holidays, market events)
```

**Action if market closed:**
- No trading today
- Skip to Evening Checklist
- Use day for system maintenance/analysis

#### 4. Latest Market Data Download (10 min)
```
☐ Pull latest prices for all 4 tickers
☐ Verify data timestamps are current
☐ Check volume (is market active?)
☐ Verify no data gaps
```

**Command:**
```bash
python src/core/data_fetcher.py --tickers AAPL,GOOGL,MSFT,TSLA
```

**Expected:**
```
AAPL: Last update 2 min ago, Volume OK
GOOGL: Last update 2 min ago, Volume OK
MSFT: Last update 2 min ago, Volume OK
TSLA: Last update 2 min ago, Volume OK
```

#### 5. Account Balance Verification (5 min)
```
☐ Check broker account balance
☐ Verify matches your expected capital
☐ Check for any unexpected fees/charges
☐ Verify position count is 0 (from previous day)
```

**Reconciliation:**

| Item | Expected | Actual | Match |
|------|----------|--------|-------|
| Account balance | $100,000 | $100,024 | ✓ |
| Open positions | 0 | 0 | ✓ |
| Cash reserves | 100% | 100% | ✓ |
| Margin used | 0% | 0% | ✓ |
| Fees pending | $0 | $0 | ✓ |

#### 6. Regime Detection Analysis (15 min)
```
☐ Run market regime detector on all 4 tickers
☐ Document today's detected regime for each
☐ Compare to previous days (trends?)
☐ Decide trading strategy for each ticker
```

**Command:**
```bash
python src/core/market_regime_detector.py --date 2026-02-24
```

**Output format:**
```
AAPL:   BULL (97% confidence) - Trade normally
GOOGL:  BULL (85% confidence) - Trade normally 
MSFT:   SIDEWAYS (72% confidence) - Tight stops
TSLA:   BEAR (68% confidence) - Reduce size/avoid
```

**Action per regime:**

| Regime | Action | Position Size | Stops |
|--------|--------|---------------|-------|
| BULL | Trade all tickers | 100% Kelly | Normal |
| BEAR | Reduce risky tickers | 50% Kelly | Tight (-0.8%) |
| SIDEWAYS | Scalp small moves | 50% Kelly | Very tight (-0.5%) |
| CONSOLIDATION | Avoid/reduce | 25% Kelly | Tight (-0.6%) |

#### 7. Previous Day P&L Review (10 min)
```
☐ Load yesterday's trading log
☐ Calculate P&L for each trade
☐ Identify winning and losing trades
☐ Analyze reasons for losses (if any)
☐ Note if any alerts triggered
```

**Daily Review Checklist:**

| Question | Yes/No | Note |
|----------|--------|------|
| Were all positions closed? | ☐ | |
| Is daily P&L positive? | ☐ | |
| Are all stops properly executed? | ☐ | |
| Any unusual slippage? | ☐ | |
| Any system errors? | ☐ | |
| Any alerts triggered? | ☐ | |

#### 8. Stop Loss Execution Audit (10 min)
```
☐ Review all stop loss executions from yesterday
☐ Verify each stop was executed at correct price
☐ Check for any missed stops
☐ Verify no positions left overnight
☐ Check broker logs for any issues
```

**Expected result:**
```
Stop Loss Audit - Yesterday:
  ✓ MSFT short SL hit at -1.2% as expected
  ✓ GOOGL long TP hit at +7.1% on close
  ✓ All stops executed within slippage threshold
  ✓ No positions left open overnight
  Status: PASS
```

#### 9. Economic Calendar Check (5 min)
```
☐ Check economic calendar for today
☐ Note any major announcements (FOMC, CPI, NonFarm, etc)
☐ Plan to avoid trading around major events (±30 min)
☐ Adjust stop sizes if high volatility expected
```

**High-Impact Events to Avoid:**
- FOMC decisions (move size +1%, adjust stops to -1.5%)
- CPI releases (move size +1.5%, adjust stops)
- Non-Farm Payroll (move size +2%, be very careful)
- Fed rate decisions (move size +2.5%, consider not trading)

#### 10. Trading Plan Review (10 min)
```
☐ Define today's trading plan
☐ What tickers will you trade?
☐ What regimes detected?
☐ Maximum positions to open?
☐ Position sizing (see Kelly allocation)
☐ Stop losses per trade
☐ Take profits per trade
☐ Daily loss limit (-2%)
```

**Trading Plan Template:**

```
═════════════════════════════════════════════════════════
TODAY'S TRADING PLAN - 2026-02-24
═════════════════════════════════════════════════════════

REGIMES DETECTED:
  AAPL:   BULL    - Trade normally
  GOOGL:  BULL    - Trade normally
  MSFT:   SIDEWAYS - Tight stops (-0.5%)
  TSLA:   BEAR    - Reduce position size

TRADING STRATEGY:
  Strategy: Adaptive, based on regimes
  Max positions: 2 simultaneous
  Position sizing: Kelly allocation
  Daily loss limit: -$2,000 (2%)

PRIMARY TICKERS:
  1. MSFT (most reliable) - Trade with tight stops
  2. GOOGL (high opportunity) - Trade with normal stops

SECONDARY TICKERS:
  3. TSLA (only if BEAR regime confirmed) - Avoid today
  4. AAPL (diversification only) - Avoid today (no edge)

EXECUTION RULES:
  • Trade only 9:30 AM - 3:30 PM ET
  • Close all positions by 4:00 PM ET
  • Hit daily loss limit (-2%) → STOP TRADING
  • 5 consecutive losses → PAUSE 1 day
  • Every position must have stop loss
  • No exceptions to stop loss rules

KELLY ALLOCATION (Today):
  MSFT: 100% of available capital (100%)
  GOOGL: 0% (Sideways regime, skip today)
  TSLA: 0% (Bear regime, skip today)
  AAPL: 0% (No edge, skip today)

═════════════════════════════════════════════════════════
```

#### 11. System Health Check (5 min)
```
☐ Check CPU usage (should be <30%)
☐ Check memory usage (should be <50%)
☐ Check disk space (need >10 GB free)
☐ Check internet connection speed
☐ Verify no system warnings/errors
☐ Check log files for 0 errors
```

**Expected system metrics:**
```
CPU Usage:     15%  (Good)
Memory:        40%  (Good)
Disk Space:    250 GB (Good)
Network:       100 Mbps (Good)
API Latency:   145 ms (Good)
Errors:        0 (Good)
```

### MORNING CHECKLIST SUMMARY

After completing all steps above, you should have:

✓ System fully powered on and tested
✓ Broker connection verified working
✓ Market confirmed open
✓ Latest prices downloaded
✓ Account balance verified
✓ Market regimes analyzed
✓ Trading plan defined
✓ Alerts/losses reviewed
✓ Economic calendar checked
✓ System health confirmed

**If ALL items checked: ✓ GO AHEAD WITH TRADING**
**If ANY item failed: ✗ DO NOT TRADE - FIX PROBLEM FIRST**

---

## DURING SESSION PROCEDURES

### TIMING: 9:30 AM - 3:30 PM ET

### PURPOSE

Monitor active trading, verify execution, manage risk in real-time.

### MONITORING INTERVAL

**Check every 30 minutes during market hours:**

```
9:30 AM   → First 30-min check
10:00 AM  → Check 2
10:30 AM  → Check 3
...
3:00 PM   → Check 12
3:30 PM   → Final check before close
```

**Total: 12 checks per trading day**

### 30-MINUTE CHECKLIST (Repeat Every 30 Minutes)

#### ☐ 1. Open Positions Review (2 min)
```
For each open position:
- Check current price
- Calculate unrealized P&L ($)
- Calculate unrealized P&L (%)
- Check if below stop loss (ACTION: Execute immediately)
- Check if above take profit (ACTION: Execute immediately)
```

**Status template:**
```
Open Positions at 10:00 AM:
  MSFT 100 shares @ $445
    Current price: $448.50
    Unrealized P&L: +$350 (+3.5%)
    Stop Loss: $436.65 (-2%)
    Take Profit: $453.15 (+1.8%)
    Status: GOOD - within targets

  GOOGL 50 shares @ $315
    Current price: $318.20
    Unrealized P&L: +$160 (+1.0%)
    Stop Loss: $308.70 (-2%)
    Take Profit: $337.10 (+7.0%)
    Status: GOOD - on track for TP
```

#### ☐ 2. Daily P&L vs Target Check (2 min)
```
- Calculate total daily P&L (from open trades + closed)
- Compare to $100+ target (per backtest)
- If significantly below: Identify why
- Plan corrections for rest of day
```

**Target check:**
```
Daily P&L Performance:
  Closed trades P&L: +$145.20
  Open trades P&L: +$350.00
  Total Current: +$495.20
  
  Target: +$100+ per day
  Status: EXCEEDING TARGET ✓
```

#### ☐ 3. Stop Loss Verification (1 min)
```
For each open position:
- Verify stop loss order exists on broker
- Verify stop loss is active (not cancelled)
- Verify stop loss price is correct
- If not: Place order immediately
```

**Critical: If ANY position lacks a stop loss → CLOSE POSITION IMMEDIATELY**

#### ☐ 4. Take Profit Verification (1 min)
```
For each open position:
- Verify take profit order exists
- Verify price is correct
- If not: Place order or adjust
```

#### ☐ 5. Daily Loss Limit Check (1 min)
```
- Calculate cumulative daily loss (if any)
- Compare to -2% limit (-$2,000 on $100k)
- If less than -$2,000: STOP TRADING IMMEDIATELY
```

**Decision tree:**
```
If daily P&L >= -$1,500:  ✓ Continue trading
If daily P&L < -$1,500:   ⚠ Check if approaching -2% limit
If daily P&L < -$2,000:   ✗ STOP ALL TRADING - Hit limit
```

#### ☐ 6. Correlation Analysis (2 min)
```
Check if correlated positions moving together as expected
- GOOGL and MSFT often move together (high correlation)
- If both losing: May indicate system failure
- If both heading to take profits: Good, let them run
```

**Correlation check:**
```
GOOGL +1.8% ↑
MSFT  +2.1% ↑
Correlation: > 0.8 (expected, normal)

TSLA -0.5% ↓ (independent, OK)

Status: PATTERN NORMAL ✓
```

#### ☐ 7. Position Limits Compliance (1 min)
```
Rules:
- Maximum 2 simultaneous open positions
- Never exceed Kelly allocation per ticker
- MSFT max: 25% ($25k)
- GOOGL max: 15% ($15k)
- TSLA max: 8% ($8k)
- AAPL max: 5% ($5k)
```

**Limit check:**
```
Current Allocations:
  MSFT: 10% allocated ✓ (under 25%)
  GOOGL: 5% allocated ✓ (under 15%)
  TSLA: 0% allocated ✓
  AAPL: 0% allocated ✓
  
All within limits.
```

#### ☐ 8. Slippage Analysis (1 min)
```
For each closed trade:
- Compare entry/exit prices vs optimal
- Calculate actual slippage
- Compare to 0.05% expected
- If > 0.1%: May indicate liquidity issues
```

**Slippage check:**
```
Recent closed trades:
  MSFT: Expected $446, got $445.80 = 0.04% slippage ✓
  GOOGL: Expected $316, got $316.15 = 0.05% slippage ✓
  
Average slippage: 0.045% (Good)
```

### Session Monitoring Summary

After completing 30-min checks:
- All positions have stops ✓
- All positions on track ✓
- Daily loss limit not approaching ✓
- No correlated issues ✓
- Position limits OK ✓
- Slippage acceptable ✓

**ACTION:** Close position if any alert shows OR if alert system triggers

---

## AFTERNOON PROCEDURES

### TIMING: 3:30 PM - 4:00 PM ET (Last 30 minutes of trading)

### PURPOSE

Close out all remaining trades, lock in daily results, prepare end-of-day reporting.

### STEP-BY-STEP CHECKLIST

#### ☐ 1. Review All Open Positions (5 min)
```
For each open position:
- How long has it been open?
- Is it approaching TP or SL?
- Should it be closed or held hoping for more?
- Decision: Hold, close, or add to position
```

**Decision template:**
```
At 3:30 PM:

Position 1: MSFT 100 shares
- Unrealized P&L: +$350 (+3.5%)
- Held: 3 hours
- Taking profits: YES
- Action: SELL at market (close position)

Position 2: GOOGL 50 shares
- Unrealized P&L: +$160 (+1.0%)
- Held: 2 hours
- Still time for more profit: Maybe
- TP is +7%, currently +1%: Let it run more
- Check at 3:55 PM

Decision: Close MSFT now, hold GOOGL 20 min more
```

#### ☐ 2. Close Remaining Positions (10 min)
```
- Decide for each position: close it or not
- If profit > 50% of target: Consider closing (lock in)
- If loss approaching SL: Close to save capital
- If breakeven or small loss: Close to preserve capital
- Close at market price (not limit)
```

**Execution:**
```
Selling MSFT 100 @ market...
   Order submitted at 3:32 PM
   Filled at $448.20 (limit was $448)
   P&L locked in: +$350.00 ✓

GOOGL holding until 3:50 PM...
   4:00 PM: Close GOOGL @ $318.95
   P&L: +$195.25 ✓

Final position count: 0
Status: All closed by 4:00 PM ✓
```

#### ☐ 3. Calculate Daily P&L (5 min)
```
P&L = All closed trades P&L + All closing position P&L

Example calculation:
  Closed trade 1 (MSFT): +$145.00
  Closed trade 2 (spot): +$350.00
  Closed trade 3 (GOOGL): +$195.25
  ────────────────────────
  TOTAL DAILY P&L: +$690.25
  
  Return %: ($690.25 / $100,000) = +0.69%
  vs Target: +0.5% daily = EXCEEDED ✓
```

#### ☐ 4. Log All Trades (10 min)
```
For each trade executed today, log:
  - Ticker and quantity
  - Entry time and price
  - Exit time and price
  - Entry reason (regime, signal, etc)
  - Exit reason (TP hit, SL, manual close)
  - Slippage (entry vs expected, exit vs expected)
  - P&L ($ and %)
  - Notes (why closed, any issues)
```

**Trade log format:**
```
═══════════════════════════════════════════════════════
DAILY TRADE LOG - 2026-02-24
═══════════════════════════════════════════════════════

Trade 1: MSFT
  Entry: 10:15 AM @ $445.00 (100 shares)
  Exit: 3:35 PM @ $448.20 (100 shares)
  Regime: SIDEWAYS → Entry signal from momentum
  Reason to close: TP target 3% hit at 3.5%
  P&L: +$320.00 (+3.5%)
  Slippage: Entry 0.02%, Exit 0.03% → Average 0.025%
  Notes: Filled quickly, good execution

Trade 2: GOOGL
  Entry: 11:45 AM @ $315.00 (50 shares)
  Exit: 4:00 PM @ $318.95 (50 shares)
  Regime: BULL → TP target 7% still possible but close
  Reason to close: Closing for day, locked profit
  P&L: +$197.50 (+1.0%)
  Slippage: Entry 0.05%, Exit 0.06% → Average 0.055%
  Notes: Position held too long, missed target

═══════════════════════════════════════════════════════
DAILY SUMMARY:
  Total trades: 2
  Winning trades: 2
  Losing trades: 0
  Win rate: 100%
  Total P&L: +$517.50
  Return %: +0.52%
═══════════════════════════════════════════════════════
```

#### ☐ 5. Update Trade Statistics (5 min)

Update running totals:
```
CUMULATIVE STATISTICS:

Day Count: 15
Total Trades: 47
  Winning: 31
  Losing: 16
  Win Rate: 66%
  
Profit Factor: Total wins / Total losses = 2.1x

Total P&L: +$12,456
Cumulative Return: +12.46%
Monthly Avg: +0.83% per day

Max Win: +$895 (Trade #22 GOOGL)
Max Loss: -$325 (Trade #18 TSLA)
Max Consecutive Wins: 4
Max Consecutive Losses: 2

P&L by Ticker:
  MSFT: +$6,234 (62 trades, 75% WR)
  GOOGL: +$4,156 (45 trades, 68% WR)
  TSLA: +$1,200 (12 trades, 58% WR)
  AAPL: +$866 (8 trades, 50% WR)
```

#### ☐ 6. Check System Alerts (2 min)
```
Review all alerts generated today:
  - Performance alerts (backtest comparison)
  - Risk alerts (daily loss limit, correlation issues)
  - Execution alerts (slippage too high)
  - System alerts (connection issues, etc)
  
If any alerts: Review and document reason
```

#### ☐ 7. Reconcile with Broker (5 min)
```
Checklist:
  ☐ My P&L: +$517.50
  ☐ Broker statement: +$517.50
  ☐ Difference: $0.00 ✓
  
  ☐ My position count: 0
  ☐ Broker position count: 0
  ☐ Match: YES ✓
  
  ☐ Account balance check
  ☐ Expected: $100,517.50
  ☐ Broker statement: $100,517.50
  ☐ Match: YES ✓
```

---

## EVENING PROCEDURES

### TIMING: 4:00 PM - 5:00 PM ET

### PURPOSE

Generate reports, analyze performance, plan for tomorrow.

### STEP-BY-STEP CHECKLIST

#### ☐ 1. Generate Daily Performance Report (10 min)

Create comprehensive report:

```
═══════════════════════════════════════════════════════════════════════════════
                   DAILY TRADING REPORT - 24 February 2026
═══════════════════════════════════════════════════════════════════════════════

MARKET CONDITIONS:
  Overall Regime: BULL (detected at 8:30 AM this morning)
  AAPL regime: BULL (97% confidence)
  GOOGL regime: BULL (85% confidence)
  MSFT regime: SIDEWAYS (72% confidence)
  TSLA regime: BEAR (68% confidence)

  Economic Events: None major today
  Market Health: Normal volume, normal volatility
  VIX Level: 14.5 (normal range)

EXECUTION PERFORMANCE:
  Trading hours: 9:30 AM - 3:35 PM ET (5 hours 5 min)
  Positions opened: 3
  Positions closed: 3 (100% closed by 4 PM)
  Max concurrent positions: 2
  Average position duration: 3.2 hours

TRADING RESULTS:
  Closed trades: 2
    Winning trades: 2
    Losing trades: 0
    Win rate: 100%
    
  Trade 1 (MSFT): +$320 (+3.5%)
  Trade 2 (GOOGL): +$197.50 (+1.0%)
  
  Daily P&L: +$517.50
  Daily Return: +0.52%
  Target Return: +0.5% = EXCEEDED ✓

RISK MONITORING:
  Daily loss limit (-2%): $2,000
  Actual max daily loss: $0 (profitable day)
  Distance from limit: Beyond protection
  Daily loss limit triggered: NO ✓

SLIPPAGE ANALYSIS:
  Average entry slippage: 0.035%
  Average exit slippage: 0.045%
  Combined average: 0.040%
  Expected slippage: 0.05% = BETTER THAN EXPECTED ✓

COMPARISON vs BACKTEST:
  Backtest expected daily return: +0.5%
  Actual daily return: +0.52%
  Difference: +0.02 percentage points
  Status: MATCHING EXPECTATIONS ✓

SYSTEM HEALTH:
  Broker connection: ✓ Perfect
  Order execution: ✓ Quick & accurate
  Data feeds: ✓ Real-time & accurate
  Monitoring system: ✓ All functions working
  Alerts: ✓ All triggers working
  Error log: 0 errors ✓

═══════════════════════════════════════════════════════════════════════════════

KEY OBSERVATIONS:
  1. Market conditions were favorable (BULL/SIDEWAYS mix)
  2. Both trades hit targets (excellent execution)
  3. Slippage better than backtest assumption
  4. System performing as designed
  5. Risk management rules enforced perfectly

ALERTS GENERATED:
  None - clean day

NEXT DAY OUTLOOK:
  Expected regime: BULL (likely continuation)
  Recommended tickers: MSFT (SIDEWAYS), GOOGL (BULL)
  Position size: Normal Kelly allocation
  Caution: None

═══════════════════════════════════════════════════════════════════════════════
```

#### ☐ 2. Compare Actual vs Backtest Performance (5 min)

Track deviation:

```
PERFORMANCE COMPARISON:

Metric               Backtest    Actual    Diff      Status
────────────────────────────────────────────────────────────
Daily Return        +0.50%      +0.52%    +0.02%    ✓ Good
Win Rate            75%         100%      +25%      ✓ Excellent
Avg Slippage        0.05%       0.04%     -0.01%    ✓ Better
Max Drawdown        1.79%       0%        -1.79%    ✓ Excellent
Profit Factor       2.1x        ∞ (all W) N/A       ✓ Excellent

Conclusion: ACTUAL PERFORMANCE EXCEEDING EXPECTATIONS
```

#### ☐ 3. Document Slippage (3 min)

Track real slippage vs assumptions:

```
SLIPPAGE DOCUMENTATION:

Entry Slippage:
  MSFT entry: Expected $445.00, got $445.02 = 0.004%
  GOOGL entry: Expected $315.00, got $315.15 = 0.048%
  Average entry slippage: 0.026%
  Backtest assumption: 0.05%
  Status: BETTER THAN EXPECTED ✓

Exit Slippage:
  MSFT exit: Expected $448, got $448.20 = 0.045%
  GOOGL exit: Expected $318.95, got $318.95 = 0.000%
  Average exit slippage: 0.023%
  Backtest assumption: 0.05%
  Status: BETTER THAN EXPECTED ✓

Combined Slippage:
  Avg combined: 0.025% (entry + exit)
  Assumption: 0.10%
  Savings from assumption: 0.075%

Implication:
  If this slippage level continues (0.025% vs 0.10% assumed),
  actual returns will be approximately 0.075% per trade better than backtest.
  On 50 trades/month = +3.75% additional return vs backtest!
```

#### ☐ 4. Regime Detection Accuracy Check (3 min)

Track accuracy of regime detection:

```
REGIME DETECTION ACCURACY:

This morning detected regimes:
  AAPL: BULL (97%)
  GOOGL: BULL (85%)
  MSFT: SIDEWAYS (72%)
  TSLA: BEAR (68%)

What actually happened today:
  AAPL: +0.8% (confirmed BULL) ✓
  GOOGL: +3.5% (stronger than expected, confirmed BULL) ✓
  MSFT: +1.2% (rangebound, confirmed SIDEWAYS) ✓
  TSLA: -0.5% (direction matched, confirmed BEAR) ✓

Regime Detection Accuracy: 4/4 (100%)

Rolling accuracy (last 15 days):
  Prior 15-day accuracy: 62%
  Today: 100%
  New rolling average: 63%
  Target: > 65%
  Status: Approaching target ✓
```

#### ☐ 5. Update Cumulative Statistics (5 min)

Update running totals:

```
CUMULATIVE STATISTICS - UPDATED

Days Traded: 15
Total Trades: 47
Total P&L: +$12,456
Cumulative Return: 12.46%
Annualized Return (projected): ~150%

Daily Breakdown:
  Days profitable: 13 / 15 (86.7%)
  Days breakeven: 0 / 15
  Days loss: 2 / 15 (13.3%)
  
  Avg winning day: +0.76%
  Avg losing day: -0.45%
  
Win Rate by Ticker:
  MSFT: 31/41 = 75.6%
  GOOGL: 10/15 = 66.7%
  TSLA: 3/5 = 60%
  AAPL: 2/4 = 50%

Best performing: MSFT (+6,234 total)
Needs work: AAPL (+866 total)

Profit Factor: 2.1x (Total wins / Total losses)
```

#### ☐ 6. Plan for Tomorrow (5 min)

Prepare trading plan for next day:

```
TOMORROW'S OUTLOOK - 25 February 2026

Expected Market Conditions:
  • Regime likely to continue: BULL momentum strong
  • Volume expected: Normal
  • Volatility expected: Normal (VIX ~15)
  • Economic events: None major

Anticipated Regimes:
  AAPL: BULL likely continue (+92%)
  GOOGL: BULL likely continue (+80%)
  MSFT: SIDEWAYS likely continue (+68%)
  TSLA: BEAR might continue (-60%)

Recommended Trading Strategy:
  1. Focus on MSFT again (90% accuracy)
  2. Try GOOGL again if TP near (only 2 trades, small sample)
  3. Avoid TSLA (BEAR regime, tight position)
  4. Avoid AAPL (low win rate)

Position Sizing:
  MSFT: Full Kelly (25%)
  GOOGL: 75% Kelly (11%)
  TSLA: 50% Kelly (4%) if conditions right
  AAPL: Skip

Expected Daily Target: +0.5% = +$500-$600
```

#### ☐ 7. Verify All Positions Closed (2 min)

Critical checkpoint:

```
POSITION CLOSURE VERIFICATION:

Broker statement shows:
  Open positions: 0 ✓
  Cash balance: $100,517.50 ✓
  Margin used: $0 ✓
  Overnight risk exposure: ZERO ✓

Internal system shows:
  Open positions: 0 ✓
  Closed trades logged: 2 ✓
  All P&L accounted for: YES ✓

Status: ALL POSITIONS PROPERLY CLOSED ✓
No overnight risk exposure.
```

#### ☐ 8. Backup Trading Data (5 min)

Secure all important data:

```
BACKUP CHECKLIST:

☐ Daily trade log saved to:
  📁 reports/daily_trades_2026-02-24.csv

☐ Performance report saved to:
  📁 reports/performance_report_2026-02-24.txt

☐ Cumulative statistics updated:
  📁 data/cumulative_stats.json

☐ Broker statement downloaded:
  📁 statements/broker_statement_2026-02-24.pdf

☐ System logs archived:
  📁 logs/trading_system_2026-02-24.log

☐ Database backup:
  📁 backups/trading_db_2026-02-24.backup

Status: All data backed up to 2 locations ✓
```

#### ☐ 9. Critical Alert Review (2 min)

Final safety check:

```
CRITICAL ALERTS REVIEW:

Today's critical alerts: NONE ✓

Recent alerting triggers:
  Day 1: NONE
  Day 2: NONE
  Day 3: Slippage note (0.06% < 0.10% limit) - OK
  Day 4-15: Clean - no alerts

System health:
  Connection issues: 0
  API errors: 0
  Data feed failures: 0
  Execution failures: 0
  Monitoring failures: 0

Status: SYSTEM OPERATING PERFECTLY ✓
```

---

## WEEKLY REVIEW

### TIMING: Friday 5:00 PM ET

### PURPOSE

Analyze weekly performance, identify patterns, plan for next week.

### EXECUTION (60 minutes)

1. **Calculate Weekly P&L (10 min)**
   - Aggregate all 5 days of trading
   - Calculate win rate
   - Calculate profit factor
   - Compare to weekly target

2. **Analyze Win Rate per Ticker (15 min)**
   - Which tickers performed best?
   - Which need work?
   - Are we following regime rules?

3. **Identify Patterns (15 min)**
   - When do we make most money? (time of day)
   - When do we lose most? (time or regime)
   - Are there day-of-week patterns?

4. **Evaluate Risk Management (10 min)**
   - Did we follow all rules?
   - Any close calls to daily loss limit?
   - Any missed stop losses?
   - Any correlation issues?

5. **Plan Next Week (10 min)**
   - Which tickers to focus on?
   - Any parameter adjustments needed?
   - Any system improvements?

---

## MONTHLY DEEP ANALYSIS

### TIMING: End of month (Feb 28, Mar 31, etc.)

### EXECUTION (2-4 hours)

1. **Calculate Monthly Performance**
   - Total return
   - Win rate
   - Total P&L
   - Compare to target

2. **Statistical Analysis**
   - Test if results are statistically significant
   - Compare to backtests
   - Identify edge remaining?

3. **Risk Analysis**
   - Maximum drawdown for month
   - Largest losing trade
   - Largest consecutive losses
   - How close did we approach daily/weekly limits?

4. **Optimization Analysis**
   - Should we adjust parameters?
   - Should we change tickers?
   - Should we change position sizing?

5. **Psychological Assessment**
   - Did I follow all rules?
   - Any emotional trading?
   - Confidence level?
   - Ready to scale up?

---

## ALERT MANAGEMENT

### Alert Severity Levels

| Severity | Action | Timeline | Example |
|----------|--------|----------|---------|
| **CRITICAL** | Act immediately | <1 min | Daily loss limit hit |
| **WARNING** | Address ASAP | <5 min | Slippage exceeds limit |
| **INFO** | Review today | <1 hour | Regime uncertainty |
| **NOTE** | Log for review | <1 day | Trade slightly off optimal |

### Common Alerts

**DAILY LOSS LIMIT (-2%)**
- Trigger: Daily loss = -$2,000 (on $100k)
- Action: STOP ALL TRADING immediately
- Timeline: Same day after hitting limit
- Recovery: Next day, with reduced position sizes

**CONSECUTIVE LOSSES (5+)**
- Trigger: 5 consecutive losing trades
- Action: Pause all trading for 1 day
- Timeline: Current trading day
- Recovery: Resume next day with normal sizes

**SLIPPAGE > 0.10%**
- Trigger: Avg slippage exceeds expectation
- Action: Review execution and order types
- Timeline: Within 1 hour
- Solution: Adjust order type or add buffer

**REGIME DETECTION < 60% ACCURACY**
- Trigger: Rolling 30-day accuracy < 60%
- Action: Review regime indicators
- Timeline: At end of week
- Solution: Retrain regime detector on latest data

**BROKER CONNECTION FAILURE**
- Trigger: API connection lost > 5 minutes
- Action: Manually close all open positions
- Timeline: Immediately
- Recovery: Diagnostics after market close

---

## EMERGENCY PROCEDURES

### Broker Connection Lost

```python
IF broker_connection_lost AND time_in_lost_state > 5_minutes:
    CLOSE all open positions manually
    NOTIFY trader immediately
    ATTEMPT to reconnect
    DO NOT reopen positions until connected
```

### Market Crash (>5% intraday move)

```python
IF market_down > 5_percent:
    CHECK all stop losses executing
    IF stop_losses_not_working:
        CLOSE all positions manually immediately
        DO NOT wait
    REVIEW portfolio correlation
    WAIT for market stabilization
    REASSESS positions before reassigning
```

### System Crash

```python
IF trading_system_crashes:
    MANUALLY CHECK broker platform
    VERIFY all positions still exist
    CLOSE any positions manually if needed
    RESTART system
    RECONCILE all positions
    RESUME trading only after verification
```

---

## DOCUMENTATION & RECORD KEEPING

### Daily Records to Keep

1. **Trade Log** (CSV)
   - Every trade entry and exit
   - Prices, time, reason, P&L

2. **Daily Report** (Text)
   - Performance summary
   - Alerts generated
   - Issues encountered

3. **Monitoring Checklist** (Checklist)
   - Morning, during, afternoon, evening
   - All items checked

4. **System Log** (Automatic)
   - All system events
   - Errors and warnings

### Monthly Aggregation

- Combine all daily reports
- Statistical analysis
- Optimization recommendations
- Ready for next month

### Annual Review

- Full yearly analysis
- Strategy evaluation
- Capital scaling decisions
- Long-term plan updates

---

## SUMMARY

**Daily monitoring is NOT optional.** It's as important as the strategy itself.

**Time Investment:**
- Daily: 2.5 hours
- Weekly: +2 hours  
- Monthly: +4 hours
- **Total: ~64 hours/month (~8 hours/week)**

**Expected Return:**
- If you follow all procedures perfectly
- And the strategy performs as backtested
- You can expect: ~0.5% daily = ~12-15% monthly

**Commitment Level:**
This is a **full-time job**. Only proceed if you can commit this time daily.

---

**Document Version:** 1.0  
**Last Updated:** 24 February 2026  
**Next Review:** 26 February 2026 (after first full week)
