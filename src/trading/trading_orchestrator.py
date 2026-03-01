"""
Trading Orchestrator - ÉTAPE 26 - Main Automation Controller
============================================================

Central orchestration system that:
- Generates signals at regular intervals
- Executes orders automatically
- Monitors positions in real-time
- Manages risk limits and daily P&L
- Handles emergency procedures

Usage:
    from trading_orchestrator import TradingOrchestrator
    orchestra = TradingOrchestrator(broker, config)
    orchestra.start_live_trading()
"""

import logging
import schedule
import time
import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from .auto_order_executor import AutoOrderExecutor, ExecutionResult
from .live_monitoring import TradingMonitor
from .broker_interface import BrokerInterface
from .live_trading_config import LiveTradingConfig, TradingPhase

# Add core to path for imports
_core_path = str(Path(__file__).parent.parent / 'core')
if _core_path not in sys.path:
    sys.path.insert(0, _core_path)

try:
    from signal_generator import SignalGenerator
    from data_fetcher import DataFetcher
except ImportError:
    # Fallback if direct import fails
    from src.core.signal_generator import SignalGenerator
    from src.core.data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class TradingOrchestrator:
    """
    Main orchestration system for automated live trading
    """
    
    def __init__(self, 
                 broker: BrokerInterface,
                 config: LiveTradingConfig,
                 phase: TradingPhase = TradingPhase.PHASE_1,
                 signal_interval_minutes: int = 60):
        """
        Initialize trading orchestrator
        
        Args:
            broker: Connected BrokerInterface instance
            config: LiveTradingConfig instance
            phase: Current trading phase
            signal_interval_minutes: Generate signals every N minutes
        """
        self.broker = broker
        self.config = config
        self.phase = phase
        self.signal_interval_minutes = signal_interval_minutes
        
        # Get phase-specific config
        self.phase_config = config.get_config_for_phase(phase)
        self.active_tickers = config.get_active_tickers_for_phase(phase)
        
        # Initialize components
        self.executor = AutoOrderExecutor(broker, config)
        self.monitor = TradingMonitor(config.initial_capital)
        self.signal_generators = {
            ticker: SignalGenerator(ticker, use_model=True)
            for ticker in self.active_tickers
        }
        self.data_fetcher = DataFetcher()
        
        # State tracking
        self.is_running = False
        self.session_start_time = None
        self.daily_start_time = None
        self.execution_log = []
        self.signal_log = []
        self.daily_pl = 0.0
        self.consecutive_losses = 0
        
        logger.info(f"TradingOrchestrator initialized for {phase.value}")
        logger.info(f"Active tickers: {', '.join(self.active_tickers)}")
        logger.info(f"Signal generation interval: {signal_interval_minutes} minutes")
    
    def start_live_trading(self):
        """Start the automated trading session"""
        
        logger.info("="*70)
        logger.info("STARTING LIVE TRADING ORCHESTRATOR")
        logger.info("="*70)
        
        # Validation
        if not self.broker.is_connected:
            logger.error("Broker not connected. Aborting.")
            return False
        
        # Get account info
        account = self.broker.get_account_info()
        logger.info(f"Account balance: ${account.total_value:.2f}")
        logger.info(f"Available cash: ${account.cash:.2f}")
        logger.info(f"Buying power: ${account.buying_power:.2f}")
        
        # Start session
        self.is_running = True
        self.session_start_time = datetime.now()
        self.daily_start_time = datetime.now()
        
        # Schedule tasks
        self._setup_scheduler()
        
        # Main event loop
        try:
            logger.info("Entering main event loop...")
            while self.is_running:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
        
        except KeyboardInterrupt:
            logger.info("Stopping by user request...")
            self.stop_trading()
        
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            self.stop_trading()
        
        return True
    
    def _setup_scheduler(self):
        """Setup scheduled tasks"""
        
        # Generate signals at regular intervals
        schedule.every(self.signal_interval_minutes).minutes.do(
            self._generate_and_execute_signals
        )
        
        # Monitor positions every 15 minutes
        schedule.every(15).minutes.do(
            self._monitor_positions
        )
        
        # Check daily limits every hour
        schedule.every(1).hours.do(
            self._check_daily_limits
        )
        
        # Close all positions at market close
        schedule.at("15:50").do(
            self._close_all_positions
        )
        
        # Daily reset
        schedule.at("16:30").do(
            self._daily_reset
        )
        
        logger.info("Scheduler tasks configured")
    
    def _generate_and_execute_signals(self):
        """Generate signals for all tickers and execute trades"""
        
        logger.info("-" * 70)
        logger.info(f"[SIGNAL GENERATION] {datetime.now().strftime('%H:%M:%S')}")
        
        # Check trading hours
        if not self.broker.is_market_open():
            logger.info("Market is not open, skipping signal generation")
            return
        
        # Get account balance
        account = self.broker.get_account_info()
        
        # Generate signals for each active ticker
        for ticker in self.active_tickers:
            try:
                signal = self.signal_generators[ticker].generate_signal()
                
                if signal is None:
                    logger.warning(f"No signal generated for {ticker}")
                    continue
                
                # Log signal
                self.signal_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'ticker': ticker,
                    'signal': signal.get('signal'),
                    'confidence': signal.get('confidence'),
                    'price': signal.get('price', 0)
                })
                
                logger.info(f"{ticker}: {signal.get('signal')} (confidence: {signal.get('confidence'):.1%})")
                
                # Execute if not HOLD
                if signal.get('signal') != 'HOLD':
                    result = self.executor.execute_signal(
                        signal,
                        {ticker: signal.get('price', 0)},
                        account.cash
                    )
                    
                    if result.success:
                        logger.info(f"✓ {result.signal} executed: {ticker} x{result.shares}")
                        self.execution_log.append(result)
                    else:
                        logger.warning(f"✗ {result.signal} failed: {result.reason}")
            
            except Exception as e:
                logger.error(f"Error generating signal for {ticker}: {e}")
    
    def _monitor_positions(self):
        """Monitor open positions and check for risk limits"""
        
        logger.info(f"[POSITION MONITORING] {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            positions = self.broker.get_positions()
            account = self.broker.get_account_info()
            
            if not positions:
                logger.info("No open positions")
                return
            
            # Get current prices
            tickers = [p.symbol for p in positions]
            prices = self.broker.get_prices(tickers)
            
            # Update monitor
            total_pnl = 0
            for position in positions:
                if position.symbol in prices:
                    current_price = prices[position.symbol]
                    pnl = (current_price - position.avg_cost) * position.quantity
                    total_pnl += pnl
                    
                    logger.info(
                        f"{position.symbol}: {position.quantity} shares @ ${position.avg_cost:.2f} "
                        f"| Current: ${current_price:.2f} | P&L: ${pnl:.2f}"
                    )
            
            # Update daily P&L
            self.daily_pl = total_pnl
            
            # Check daily loss limit
            loss_limit_pct = self.config.risk_rules.DAILY_LOSS_LIMIT_PCT / 100
            max_loss = account.total_value * loss_limit_pct
            
            if self.daily_pl < max_loss:
                logger.critical(f"DAILY LOSS LIMIT HIT: ${self.daily_pl:.2f} < ${max_loss:.2f}")
                self.stop_trading()
            
            logger.info(f"Daily P&L: ${self.daily_pl:.2f}")
        
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
    
    def _check_daily_limits(self):
        """Check daily trading limits"""
        
        logger.info(f"[LIMIT CHECK] {datetime.now().strftime('%H:%M:%S')}")
        
        # Get trades from today
        today = datetime.now().date()
        trades_today = [e for e in self.execution_log 
                       if e.timestamp.date() == today and e.success]
        
        logger.info(f"Trades today: {len(trades_today)} / {self.config.risk_rules.MAX_DAILY_TRADES}")
        
        if len(trades_today) >= self.config.risk_rules.MAX_DAILY_TRADES:
            logger.warning("Daily trade limit reached")
    
    def _close_all_positions(self):
        """Close all positions at market close"""
        
        logger.info(f"[MARKET CLOSE - CLOSING ALL POSITIONS] {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            positions = self.broker.get_positions()
            
            if not positions:
                logger.info("No positions to close")
                return
            
            prices = self.broker.get_prices([p.symbol for p in positions])
            
            for position in positions:
                if position.symbol in prices:
                    price = prices[position.symbol]
                    result = self.executor.execute_signal(
                        {
                            'signal': 'SELL',
                            'ticker': position.symbol,
                            'confidence': 1.0,
                            'price': price,
                            'stop_loss': 0,
                            'take_profit': 0
                        },
                        prices,
                        0  # Don't care about balance for closing
                    )
                    
                    if result.success:
                        logger.info(f"✓ Closed {position.symbol} position")
                    else:
                        logger.error(f"✗ Failed to close {position.symbol}: {result.reason}")
        
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
    
    def _daily_reset(self):
        """Reset daily metrics"""
        
        logger.info(f"[DAILY RESET] {datetime.now().strftime('%H:%M:%S')}")
        
        # Save daily report
        self._save_daily_report()
        
        # Reset counters
        self.daily_start_time = datetime.now()
        self.daily_pl = 0.0
        self.consecutive_losses = 0
    
    def _save_daily_report(self):
        """Save daily execution report"""
        
        today = datetime.now().date()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report = {
            'date': today.isoformat(),
            'session_start': self.session_start_time.isoformat(),
            'session_end': datetime.now().isoformat(),
            'phase': self.phase.value,
            'active_tickers': self.active_tickers,
            'execution_stats': self.executor.get_execution_stats(),
            'daily_pl': self.daily_pl,
            'executions': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'signal': e.signal,
                    'ticker': e.ticker,
                    'shares': e.shares,
                    'entry_price': e.entry_price,
                    'success': e.success,
                    'reason': e.reason
                }
                for e in self.execution_log
                if e.timestamp.date() == today
            ]
        }
        
        # Save to file
        report_dir = Path(__file__).parent.parent.parent / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f'daily_auto_trading_{timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Daily report saved: {report_file}")
    
    def stop_trading(self):
        """Stop the automated trading session"""
        
        logger.info("="*70)
        logger.info("STOPPING TRADING")
        logger.info("="*70)
        
        # Close positions
        self._close_all_positions()
        
        # Save report
        self._save_daily_report()
        
        # Statistics
        stats = self.executor.get_execution_stats()
        logger.info(f"Total executions: {stats['total_executions']}")
        logger.info(f"Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
        logger.info(f"Buy orders: {stats['buy_orders']}")
        logger.info(f"Sell orders: {stats['sell_orders']}")
        logger.info(f"Final P&L: ${self.daily_pl:.2f}")
        
        self.is_running = False
    
    def get_status(self) -> Dict:
        """Get current trading status"""
        
        account = self.broker.get_account_info()
        positions = self.broker.get_positions()
        
        return {
            'is_running': self.is_running,
            'phase': self.phase.value,
            'session_duration': (datetime.now() - self.session_start_time).total_seconds() / 60 if self.session_start_time else 0,
            'account_balance': account.total_value,
            'cash_available': account.cash,
            'open_positions': len(positions) if positions else 0,
            'daily_pl': self.daily_pl,
            'executions': len(self.execution_log),
            'execution_stats': self.executor.get_execution_stats()
        }
