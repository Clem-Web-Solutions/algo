# ÉTAPE 17 - LIVE TRADING STARTUP GUIDE

**Project:** Algo Trading System - Live Trading Phase  
**Date:** 24 Février 2026  
**Version:** 1.0 - Complete Startup & Operations Manual  
**Status:** Ready for Immediate Deployment

---

## PART 1: PRE-LIVE CHECKLIST (Before First Trade)

### ✓ SYSTEM VALIDATION

- [ ] Paper trading simulation completed (1+ year of data)
- [ ] Extended simulation shows positive returns
- [ ] All risk alerts properly handled
- [ ] Broker API working 100% (tested 10+ times)
- [ ] Position sizing calculated correctly
- [ ] Daily monitoring procedures understood
- [ ] Trader fully trained on all systems
- [ ] Emergency procedures documented
- [ ] Backup capital available (emergency fund)
- [ ] Daily commitment (2.5 hours/day) confirmed

### ✓ PSYCHOLOGICAL VALIDATION

- [ ] Trader comfortable   with -2% daily loss risk
- [ ] Trader can sit through drawdown without panic
- [ ] Trader has practiced rule-following
- [ ] Trader has backup income (not dependent on trading)
- [ ] Family/partner supportive of trading
- [ ] Trader has slept 8+ hours (clear head)
- [ ] Trader is NOT trader when emotional/stressed
- [ ] Trader committed to following system rules exactly

### ✓ BROKER SETUP

- [ ] Broker account opened (Interactive Brokers recommended)
- [ ] Account fully funded with initial capital
- [ ] API enabled (ports configured: 7497 live, 7498 paper)
- [ ] Trading permissions enabled for all 4 tickers
- [ ] Commission set to $1/order or lower
- [ ] Margin settings: 1.0x only (no margin initially)
- [ ] Data subscriptions: Real-time quotes active
- [ ] Test trade executed successfully
- [ ] Test trade cancelled without issue
- [ ] Account fully reconciled

### ✓ DOCUMENTATION READY

- [ ] Daily monitoring procedures printed/saved
- [ ] Live trading startup guide (this document) reviewed
- [ ] Risk management rules documented
- [ ] Emergency procedures taped to desk
- [ ] Daily checklist printed and placed at workstation
- [ ] Trade log template created and ready
- [ ] P&L tracking spreadsheet set up
- [ ] Broker statement saved for baseline

### ✓ FINAL SAFETY CHECKS

- [ ] No major economic announcements today
- [ ] Market open and normal hours
- [ ] Internet connection stable and tested
- [ ] Backup internet available (mobile hotspot charged)
- [ ] Computer has 20%+ battery or plugged in
- [ ] No distractions for trading session
- [ ] Phone set to silent (minimize interruptions)
- [ ] Bathroom/water break completed
- [ ] Mental state: Calm and focused

---

## PART 2: PHASE 1 - Initial Validation (Days 1-5)

### PHASE 1 OVERVIEW

**Objective:** Validate that the system works with real money on real market

**Duration:** 5 trading days minimum (can extend to 10 if uncertain)

**Capital At Risk:** $2,000 - $5,000 (small)

**Position Size:** Maximum $500 per trade

**Tickers:** MSFT ONLY (most reliable, highest win rate)

**Success Criteria:**
- Win rate > 40% (we expect 100% from backtest, slippage will reduce)
- Daily P&L > -2% (daily loss limit)
- All stop losses execute perfectly
- No broker/API issues
- P&L tracking matches broker statement exactly

**Failure Criteria:**
- Win rate < 30% (system broken)
- P&L mismatches broker statement (tracking error)
- Any unexecuted stop loss (critical issue)
- Broker connection problems
- System crashes

### DAY 1 DETAILED WALKTHROUGH

#### 8:30 AM - Morning Setup

```
☐ Power on all systems
☐ Start broker software (TWS)
☐ Start trading system (Python environment)
☐ Start daily monitoring dashboard
☐ Run broker connection test
☐ Download latest market data
☐ Verify account balance: $2,500
☐ Run regime detector (expected: BULL or SIDEWAYS)
```

#### 9:30 AM - Market Open

```
☐ First price update received
☐ Review trading plan: MSFT only, 1 position max
☐ Identify first signal (if any)
```

#### 9:45 AM - First Entry Decision

**Example scenario:**
```
Market regime: BULL (detected at 89% confidence)
MSFT price: $440.00
Signal: Momentum bullish + regime BULL = BUY signal

ENTRY DECISION:
  Ticker: MSFT
  Direction: LONG (buy)
  Quantity: 5 shares
  Entry price: Market order ~$440.00
  Expected fill: ~$440.05 (0.01% slippage)
  Stop Loss: $430.80 (2.1% below entry) - MANDATORY
  Take Profit: $443.00 (0.7% above entry) - OK for small first trade
  Risk: $46 (5 shares × $0.92 = $46 risk per trade)

Execution:
  1. Place buy order for 5 MSFT @ market
  2. Verify filled at broker
  3. Place stop loss order (essential!)
  4. Place take profit order
  5. Log entry in trade log
  6. Monitor position
```

#### 10:30 AM - Position Monitoring

```
Every 30 minutes, check:
  ☐ Current price: $441.50
  ☐ Current P&L: +$7.50 (+0.17%)
  ☐ Stop loss still in place?
  ☐ Take profit still in place?
  ☐ Daily P&L: +$7.50 (far from -2% limit)
  ☐ Any alerts? NO
```

#### 3:30 PM - Closing Decision

```
Scenario: Take profit @ $443.00 was hit at 2:45 PM
  
Position closed automatically at $443.00
P&L: 5 × ($443.00 - $440.00) - commissions = ~$15 - $1 = +$14
Trade logged successfully
Daily P&L: +$14

Action for rest of day:
  ☐ Can trade more (1 position max), or
  ☐ Close for day (safe option for first day)
  
Recommendation: Close for day, do not get greedy on Day 1
```

#### 3:50 PM - Close All Positions

```
Orders check:
  ☐ All trades closed? YES
  ☐ No positions open? YES
  ☐ Cash back to $2,500+? YES (now $2,514)

P&L final: $14
Return: +0.56%
Status: SUCCESS ✓
```

#### 4:00 PM - Evening Checklist

```
☐ Daily report generated
☐ Trade log completed
☐ Broker P&L matches: $14 ✓
☐ No alerts triggered
☐ System health good
☐ Positions verified closed
☐ Data backed up
☐ Ready for tomorrow
```

### DAYS 2-5: REPEAT WITH CONFIDENCE

**If Day 1 successful:** Proceed to Day 2 with increased confidence

**Same procedure each day:**
1. Morning checklist (8:30 AM)
2. Trading per regime (9:30 AM - 3:30 PM)
3. Close all positions (3:50 PM)
4. Evening checklist (4:00 PM)

**Metrics to track each day:**

| Day | Regime | Trades | Wins | Loss | Return | Notes |
|-----|--------|--------|------|------|--------|-------|
| 1 | BULL | 1 | 1 | 0 | +0.56% | Perfect |
| 2 | BULL | 2 | 1 | 1 | +0.22% | One stop hit |
| 3 | SIDEWAYS | 1 | 0 | 1 | -0.15% | Tight stops OK |
| 4 | BULL | 3 | 2 | 1 | +0.45% | Good |
| 5 | SIDEWAYS | 2 | 1 | 1 | +0.18% | Average |
| **TOTAL** | **Mixed** | **9** | **5** | **4** | **+1.26%** | **Good start** |

**Phase 1 Success Criteria Check:**
- [ ] Win rate: 5/9 = 55.5% (target > 40%) ✓
- [ ] Daily max loss: -0.15% (target > -2%) ✓
- [ ] All stops executed: YES ✓
- [ ] No broker issues: YES ✓
- [ ] P&L matches broker: YES ✓

**Result: READY FOR PHASE 2** ✓

---

## PART 3: PHASE 2 - Multiple Tickers (Days 6-20)

### PHASE 2 OVERVIEW

**Objective:** Validate strategy on all 4 tickers

**Duration:** 15 trading days minimum

**Capital:** Increase to $5,000 - $10,000

**Allocation:**
- MSFT: 50% of available capital = $5,000 (most reliable)
- GOOGL: 30% = $3,000 (high opportunity)
- TSLA: 15% = $1,500 (selective)
- AAPL: 5% = $500 (diversification only)
- CASH: Remaining

**Position Limits:**
- Maximum 2 concurrent positions
- Max $1,000 per position
- All Kelly allocation rules apply

### DAY 6 - Adding Second Ticker

#### Morning Checklist (8:30 AM)

```
Market regime analysis:
  AAPL: BULL
  GOOGL: BULL (strong)
  MSFT: BULL
  TSLA: SIDEWAYS

Plan:
  Primary: MSFT (as in Phase 1)
  Secondary: GOOGL (high opportunity + BULL regime)
  Avoid: TSLA (SIDEWAYS, not prime time yet)
  Avoid: AAPL (no strong edge)

Allocation:
  MSFT: 100% of capital = $5,000
  GOOGL: 60% of capital = $3,000
  Available for trades: $8,000
```

#### 10:00 AM - First MSFT Position

```
MSFT Signal: BULL regime + momentum → BUY
Entry: 100 shares @ $440.00
Stop: -2% @ $431.20
Take Profit: +7% @ $470.80
Position size: $44,000 exposure (10 shares only, 1% of capital)
```

#### 11:00 AM - GOOGL Added

```
GOOGL Signal: BULL regime + technical + TP -7% = BUY
Entry: 50 shares @ $315.00
Stop: -2% @ $308.70
Take Profit: +7% → Target $336.50
Position size: $15,750 exposure (0.5% of capital)

Portfolio now:
  Position 1: MSFT 100 @ $440 = $44,000 exposure
  Position 2: GOOGL 50 @ $315 = $15,750 exposure
  Cash: Adjusted based on capital
  Total positions: 2 (at limit)
```

#### 3:30 PM - Closing

```
MSFT: Take profit hit @ $470.80 = +$3,080 ✓
GOOGL: Close for day @ $318.00 = +$150 (not at TP yet)

Daily P&L: +$3,230
Return: +0.43%
Status: Good start to Phase 2
```

### PHASE 2 DAILY PATTERN

**Days 6-20 repeat:**
1. Identify 1-2 best ticker prospects (regime analysis)
2. Trade per Kelly allocation
3. Monitor 2 positions maximum
4. Close by 3:30 PM
5. Log results

### PHASE 2 SUCCESS METRICS

**After 15 days:**

| Metric | Target | Actual |
|--------|--------|--------|
| Win Rate | >35% | 45% |
| Profit Factor | >1.5x | 1.8x |
| Total Return | +7% | +8.2% |
| Max Daily Loss | <-2% | -1.1% |
| Correlation issues | None | None |
| Unexecuted stops | 0 | 0 |
| Broker issues | 0 | 0 |

**Gate Check:**
- All metrics acceptable? → **PROCEED TO PHASE 3**
- Any metrics below target? → **PAUSE, ANALYZE, EXTEND PHASE 2**

---

## PART 4: PHASE 3 - Full Portfolio (Days 21+)

### PHASE 3 OVERVIEW

**Objective:** Run full strategy at full Kelly allocation

**Duration:** 30+ days (minimum 1 month)

**Capital:** Full allocation (starting from $100,000 or accumulated)

**Allocation (Kelly Criterion):**

| Ticker | Kelly % | Capital | Rationale |
|--------|---------|---------|-----------|
| MSFT | 25% | $25,000 | Anchor - most reliable (100% WR) |
| GOOGL | 15% | $15,000 | High opportunity (+13%+ in backtests) |
| TSLA | 8% | $8,000 | Conditional - only BEAR/SIDEWAYS |
| AAPL | 5% | $5,000 | Diversification only |
| CASH | 47% | $47,000 | Emergency buffer + flexibility |

**Position Limits:**
- Maximum 4 open positions (one per ticker)
- Never exceed Kelly allocation per ticker
- Maximum leverage: 1.0x (no margin)

### PHASE 3 DAILY ROUTINE

#### 8:30 AM - Morning Checklist
- Full system verification
- Regime detection on all 4 tickers
- Plan for tickers to trade today
- Verify Kelly allocation

#### 9:30 AM - Trading Session
- Execute per detected regimes
- Monitor all open positions
- Enforce stops and targets

#### 3:30 PM - Closing
- Close all positions
- Reconcile P&L
- Log all trades

#### 4:00 PM - Evening Review
- Generate daily report
- Update cumulative statistics
- Plan for tomorrow

### PHASE 3 SUCCESS GATES

**After 10 days:**
- Win rate > 35%?
- P&L > 0%?
- If NO → Something wrong, pause and analyze

**After 20 days:**
- Win rate > 40%?
- Monthly return > 2%?
- If NO → Consider reverting to Phase 2

**After 30 days:**
- Win rate > 45%?
- Monthly return > 4%?
- If NO → Analyze deeply before scaling

**If ALL gates passed:**
- ✓ **READY TO SCALE CAPITAL**
- → Increase allocation 50% next month
- → Monitor for next 30 days
- → Scale again if successful

---

## PART 5: SCALING STRATEGY (After Success)

### Month 1 (Current Month)

**Focus:** Validation at current capital level

**Capital:** $5,000 - $100,000 (per phase)

**Goal:** Prove system works with real money

**Success metric:** Positive return, no major issues

### Month 2-3

**IF Month 1 successful:**

- Increase capital allocation by 50%
- Example: $100k → $150k
- Maintain same Kelly allocation percentages
- Continue daily monitoring
- Monitor for any issues at larger scale

### Month 4-6

**IF Month 2-3 successful:**

- Scale to full amount
- Monitor for drawdowns
- Optimize based on real performance
- Consider additional strategies

### Month 6-12

**IF Month 1-6 successful:**

- Evaluate scaling further
- Consider adding tickers/strategies
- Optimize regime detection
- Implement advanced features

### No Scaling if

- Any major losses (< -5% monthly)
- Win rate drops below 45%
- Broker/API issues
- Drawdown exceeds 15%
- Trader confidence shaken

---

## PART 6: CRITICAL OPERATING RULES

### RULE #1: STOP LOSS ENFORCEMENT

**Every position MUST have a stop loss. NO EXCEPTIONS.**

```
Before placing trade:
  ☐ Calculate stop loss based on regime
  ☐ Verify stop loss is valid
  ☐ Place order
  ☐ Verify stop loss order exists
  ☐ Start position tracking
  
DO NOT TRADE if you can't place stop loss
```

**Stop Loss Prices (per regime):**

| Regime | Max SL | Target |
|--------|--------|--------|
| BULL | -2.0% | +5% to +7% |
| BEAR | -0.8% | +1% to +2% |
| SIDEWAYS | -0.5% | +2% |
| CONSOLIDATION | -0.6% | +2.5% to +3% |

### RULE #2: DAILY LOSS LIMIT

**If daily loss reaches -2% (-$2,000 at $100k), STOP ALL TRADING immediately for rest of day.**

```
Decision tree:
  If daily loss < -$1,000: Continue (within safe zone)
  If daily loss -$1,000 to -$1,500: CAUTION, few risks trades
  If daily loss -$1,500 to -$2,000: REDUCE position sizes 50%
  If daily loss < -$2,000: STOP TRADING IMMEDIATELY
```

### RULE #3: POSITION SIZING

**All positions must follow Kelly Criterion allocation.**

```
Max per ticker:
  MSFT: 25% of capital
  GOOGL: 15% of capital
  TSLA: 8% of capital
  AAPL: 5% of capital
  
Never exceed these limits.
Never use margin.
Never override Kelly allocation.
```

### RULE #4: TRADING HOURS

**Trade ONLY during peak liquidity:**
- Start: 9:30 AM ET (market open)
- End: 3:30 PM ET (before market close)
- Close ALL positions by 4:00 PM ET

**Do NOT:**
- Trade pre-market (before 9:30 AM)
- Trade after-hours (after 4:00 PM)
- Hold positions overnight
- Leave positions open unmonitored

### RULE #5: REGIME-DEPENDENT TRADING

**Only valid regimes for trading:**

| Regime | Trading? | Position Size | Notes |
|--------|----------|---------------|-------|
| BULL | YES | 100% | Trade all 4, normal stops |
| BEAR | YES | 50% | Reduce TSLA, avoid AAPL |
| SIDEWAYS | YES | 50% | Use tight stops, scalp |
| CONSOLIDATION | NO | 0% | DON'T TRADE, wait for regime |

### RULE #6: RISK LIMITS (Hierarchy)

**Follow this strictly:**

```
Level 1 (Daily): Max daily loss = -2%
  Action: STOP TRADING for rest of day

Level 2 (Sessions): Max consecutive losses = 5
  Action: PAUSE ALL TRADING for 1 day

Level 3 (Weekly): Max weekly loss = -5%
  Action: REDUCE position sizes by 50%

Level 4 (Monthly): Max monthly loss = -10%
  Action: CLOSE all positions, deep review
```

### RULE #7: POSITION MONITORING

**Monitor every open position continuously during market hours:**

**Every 30 minutes, verify:**
- Current price
- Current unrealized P&L
- Stop loss still in place
- Take profit still in place
- No correlation issues
- Not approaching daily loss limit

### RULE #8: EMOTIONAL DISCIPLINE

```
NEVER:
  ✗ Override a stop loss
  ✗ Add to a losing position
  ✗ Revenge trade after losses
  ✗ Deviate from Kelly allocation
  ✗ Trade hours outside 9:30-3:30
  ✗ Leave positions open overnight

ALWAYS:
  ✓ Execute the specified plan
  ✓ Honor all stop losses
  ✓ Follow Kelly allocation
  ✓ Close by 4:00 PM
  ✓ Log all trades
  ✓ Monitor positions
  ✓ Trust the system
```

### RULE #9: BROKER OPERATIONS

**Daily broker checks:**

```
Morning:
  ☐ API connection working
  ☐ Account balance correct
  ☐ No pending orders
  ☐ Trading permissions active
  
During session:
  ☐ Orders execute quickly
  ☐ Fills at expected prices
  ☐ Stop losses working
  ☐ No error messages
  
End of day:
  ☐ All positions closed
  ☐ P&L matches broker
  ☐ No stuck orders
  ☐ Ready for next day
```

### RULE #10: WHEN TO PAUSE/STOP

**PAUSE trading immediately if:**
- Broker API down > 5 minutes
- Unexpected gap risk trades
- Win rate drops below 30% (3+ days)
- System crashes/won't restart
- Trader feeling stressed/emotional
- Major market event (Black Swan)

**DO NOT resume until:**
- System fully tested and working
- Root cause identified and fixed
- Trader calm and focused
- All systems double-checked

---

## PART 7: DAILY MONITORING FRAMEWORK

### Morning (8:30 AM) - 45 minutes

**11-point checklist:**
1. System startup and health
2. Broker connection test
3. Market open verification
4. Data download
5. Account balance check
6. Regime detection
7. Previous day review
8. Stop loss audit
9. Economic calendar check
10. Trading plan creation
11. Final readiness verification

**Output:** Clear GO/NO-GO decision on trading

### During Session (9:30 AM - 3:30 PM) - Continuous

**30-minute interval checks:**
1. Open positions review
2. Daily P&L vs target
3. Stop loss verification
4. Take profit verification
5. Daily loss limit check
6. Correlation analysis
7. Position limits
8. Slippage tracking

**Output:** Confidence that system operating normally

### Afternoon (3:30 PM - 4:00 PM) - 30 minutes

**7-point checklist:**
1. Review all open positions
2. Close all positions
3. Calculate daily P&L
4. Log all trades
5. Update statistics
6. Check alerts
7. Reconcile with broker

**Output:** All positions closed, P&L locked in

### Evening (4:00 PM - 5:00 PM) - 60 minutes

**9-point checklist:**
1. Generate daily report
2. Compare vs backtest
3. Document slippage
4. Check regime accuracy
5. Update cumulative stats
6. Plan for tomorrow
7. Verify positions closed
8. Backup data
9. Review critical alerts

**Output:** Ready for next trading day

### Total Daily Time Commitment: 2.5 hours

---

## PART 8: EMERGENCY PROCEDURES

### Scenario 1: Broker Connection Lost

```
IF broker_connected == False AND time_disconnected > 5_minutes:
  
  STEP 1: Check your internet connection
    - Restart app/reconnect WiFi
    - Check mobile hotspot available
    
  STEP 2: Try to reconnect to broker
    - Restart TWS/API
    - Check broker status page
    - Verify no maintenance
    
  STEP 3: If still down, CLOSE ALL POSITIONS MANUALLY
    - Call broker phone line
    - Provide order details
    - Verify order confirmation
    - DO NOT wait for API to restore
    
  STEP 4: After market close
    - File complaint with broker
    - Document loss (if any)
    - Analyze what went wrong
    - Prevent future occurrence
```

### Scenario 2: Market Crash (>5% down)

```
IF market_down_percent > 5:
  
  STEP 1: IMMEDIATELY check stop losses
    - Are they executing?
    - Is P&L locked in?
    - Or orders pending?
    
  STEP 2: If stops NOT working:
    - CLOSE all positions manually immediately
    - Do NOT wait
    - Market orders in any market
    - Accept any fill
    
  STEP 3: If stops ARE working:
    - Let them execute as designed
    - Monitor execution prices
    - Stay alert for cascading losses
    
  STEP 4: After initial shock:
    - WAIT for market stabilization
    - DO NOT put on new trades
    - Assess portfolio health
    - Review what happened
    
  STEP 5: Resume trading only after:
    - Market stabilized
    - All stops executed cleanly
    - No mysterious losses
    - Plan for rest of day determined
```

### Scenario 3: System Crash

```
IF trading_system_crashes:
  
  STEP 1: MANUALLY log into broker account
    - Check if positions still exist
    - Check broker statement P&L
    - Are my positions there?
    
  STEP 2: If positions stuck open:
    - CLOSE them manually on broker platform
    - Use phoned orders if system down
    - Get confirmation numbers
    
  STEP 3: Restart trading system
    - Reboot computer if needed
    - Reload all software
    - Test connection
    - Verify all data loads
    
  STEP 4: Reconcile discrepancies
    - My system position log vs broker
    - My P&L calculations vs broker statement
    - Make sure everything matches
    
  STEP 5: ONLY THEN resume trading
    - Do NOT trade until fully reconciled
    - Test 1 mock trade first
    - Cancel mock trade
    - Verify system stable
    - THEN resume normal trading
```

### Scenario 4: Stop Loss Not Executed

```
IF stop_loss_order_not_executed AND price_below_stop_price:
  
  THIS IS A CRITICAL ISSUE - immediate action required:
  
  STEP 1: IMMEDIATELY call broker
    - Explain: Stop loss order not executed
    - Provide: Ticker, quantity, stop price
    - Request: Manual close-out order
    - Get: Confirmation number
    
  STEP 2: CLOSE THE POSITION MANUALLY
    - If phone contact fails: Mobile app
    - If app fails: Broker website
    - Get order filled ASAP
    - Accept ANY price
    - Priority is CLOSING, not price
    
  STEP 3: Document the issue:
    - Screenshot stop loss order
    - Screenshot actual fills
    - Write down exactly what happened
    - Note time of failure
    
  STEP 4: After market close:
    - File complaint with broker
    - Demand explanation
    - Ask for compensation
    - Get root cause analysis
    
  STEP 5: DO NOT TRADE until:
    - Root cause identified
    - Fix implemented
    - Successfully tested 3x with mock trades
    - Broker confirms system working
```

---

## PART 9: GO/NO-GO DECISION GATES

### Before First Trade

**Gate questions - ALL must be YES:**

- [ ] Paper trading showed positive returns? YES
- [ ] Broker account fully set up? YES
- [ ] System tested 5+ times? YES
- [ ] Morning checklist completed? YES
- [ ] Trading plan defined? YES
- [ ] Risk limits understood? YES
- [ ] Emergency procedures reviewed? YES
- [ ] Trader feeling calm? YES
- [ ] No major market events? YES
- [ ] Full commitment to rules? YES

**If ANY answer is NO:**
→ **DO NOT TRADE TODAY** → Fix the issue → Try tomorrow

---

## PART 10: FINAL CHECKLIST BEFORE FIRST LIVE TRADE

Print this and tape it to your desk:

```
╔═════════════════════════════════════════════════════════╗
║          FINAL CHECKLIST - FIRST LIVE TRADE            ║
╚═════════════════════════════════════════════════════════╝

SYSTEM READINESS:
  ☐ Computer powered on
  ☐ Internet connection stable
  ☐ Broker software running
  ☐ Trading system running
  ☐ All dashboards loaded
  ☐ Test API connection successful
  ☐ Latest market data loaded

BROKER ACCOUNT:
  ☐ Account balance verified
  ☐ Correct account (paper vs live?)
  ☐ Trading permissions active
  ☐ Commission settings reviewed
  ☐ Margin disabled (1.0x only)

FIRST POSITION PREPARATION:
  ☐ Regime analysis complete
  ☐ Ticker identified: ___________
  ☐ Entry price calculated
  ☐ Stop loss price calculated
  ☐ Take profit price calculated
  ☐ Position size calculated
  ☐ Kelly allocation verified

RISK MANAGEMENT:
  ☐ Stop loss rule understood
  ☐ Daily loss limit understood
  ☐ Position limit understood
  ☐ Trading hours understood
  ☐ All rules able to be followed

EMOTIONAL STATE:
  ☐ Trader calm and focused
  ☐ Trader NOT rushed
  ☐ Trader NOT emotional
  ☐ Trader ready for -$500 loss
  ☐ Trader ready for -2% daily loss
  ☐ Trader committed to follow rules

GO-LIVE APPROVAL:
  ☐ All items above checked: YES
  ☐ Ready to execute first trade: YES
  ☐ Understood all risks: YES
  ☐ Will follow all rules: YES

═════════════════════════════════════════════════════════

APPROVED TO BEGIN LIVE TRADING: ________________

Date/Time: ________________

═════════════════════════════════════════════════════════
```

---

## SUMMARY

| Phase | Duration | Capital | Success Target | Gate Requirement |
|-------|----------|---------|-----------------|-----------------|
| **Phase 1** | 5+ days | $2-5k | +0.5% daily | Win rate > 40% |
| **Phase 2** | 15 days | $5-10k | +0.5% daily | All metrics pass |
| **Phase 3** | 30+ days | Full | +2% monthly | Win rate > 45% |
| **Scale Up** | Ongoing | $100k+ | +2% monthly | Consistent |

**Time Commitment:**
- Daily: 2.5 hours (morning + during + afternoon + evening)
- This is a **full-time job**

**Expected Returns:**
- Backtest: +0.5% daily = +12-15% monthly = +150%+ annually
- Real-world (with slippage): -30% discount = +8-10% monthly realistic

**Risk Management:**
- Daily loss limit: -2%
- Position sizing: Kelly Criterion
- Stop losses: MANDATORY on every trade
- Monitoring: Continuous during market hours

---

**Document Version:** 1.0  
**Ready to Deploy:** 24 February 2026  
**Status:** [✓ READY FOR IMMEDIATE USE]

---

## APPENDIX: Quick Reference Cards

### MORNING CHECKLIST (5 minutes)

```
☐ System on, internet working
☐ Broker connection verified
☐ Account balance: $___________
☐ Market open? (Check calendar)
☐ Regimes detected: AAPL___ GOOGL___ MSFT___ TSLA___
☐ Trading plan defined
☐ Ready to trade? YES / NO
```

### DURING SESSION (Every 30 min)

```
☐ Open positions exist
☐ Unreal P&L positive/acceptable
☐ Stops in place
☐ Daily loss limit not approaching
☐ Everything normal? YES / NO
```

### AFTERNOON (3:30 PM)

```
☐ Close all positions
☐ Daily P&L calculated: $_________
☐ All trades logged
☐ Broker P&L matches? YES
```

### EMERGENCY HOTLINE

```
If broker connection lost > 5 min:
  Phone: [Your broker emergency number]
  Action: Manual close-out

If system crash:
  Broker app/website: Close positions manually
  System restart: Full check before resuming
```

---

**THIS IS YOUR BIBLE FOR LIVE TRADING**

**Keep permanent copy at your desk**
**Review daily**
**Follow EXACTLY - no deviations**

**Your success depends on discipline.**
