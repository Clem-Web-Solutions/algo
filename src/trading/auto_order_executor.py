"""
Automatic Order Execution Module - ÉTAPE 26
=====================================================

Automatically executes trades based on signals with:
- Market vs Limit order logic
- Position sizing validation
- Stop loss & Take profit placement
- Risk management checks
- Order status tracking

Usage:
    from auto_order_executor import AutoOrderExecutor
    executor = AutoOrderExecutor(broker, config)
    result = executor.execute_signal(signal, current_prices)
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .broker_interface import (
    BrokerInterface, OrderData, OrderSide, OrderType, OrderStatus
)
from .live_trading_config import LiveTradingConfig

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a signal execution"""
    success: bool
    signal: str
    ticker: str
    main_order_id: Optional[str]
    stop_order_id: Optional[str]
    profit_order_id: Optional[str]
    entry_price: Optional[float]
    shares: Optional[int]
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    reason: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AutoOrderExecutor:
    """
    Automatically executes trading signals with full risk management
    """
    
    def __init__(self, broker: BrokerInterface, config: LiveTradingConfig):
        """
        Initialize order executor
        
        Args:
            broker: BrokerInterface instance (connected)
            config: LiveTradingConfig instance
        """
        self.broker = broker
        self.config = config
        self.execution_history = []
        
        logger.info(f"AutoOrderExecutor initialized for account {broker.account_id}")
    
    def execute_signal(self, 
                      signal: Dict,
                      current_prices: Dict[str, float],
                      account_balance: float) -> ExecutionResult:
        """
        Execute a trading signal automatically
        
        Args:
            signal: Dict with keys:
                - 'signal': 'BUY', 'SELL', or 'HOLD'
                - 'ticker': stock symbol
                - 'confidence': float 0-1
                - 'price': current price
                - 'stop_loss': calculated SL
                - 'take_profit': calculated TP
            current_prices: Dict of symbol->price
            account_balance: Current account balance
        
        Returns:
            ExecutionResult with execution details
        """
        
        # 1. Validate signal
        if signal.get('signal') == 'HOLD':
            return ExecutionResult(
                success=False,
                signal='HOLD',
                ticker=signal.get('ticker', 'UNKNOWN'),
                main_order_id=None,
                stop_order_id=None,
                profit_order_id=None,
                entry_price=None,
                shares=None,
                stop_loss_price=None,
                take_profit_price=None,
                reason='No action on HOLD signal'
            )
        
        ticker = signal.get('ticker', 'UNKNOWN')
        signal_type = signal.get('signal', 'HOLD')
        confidence = signal.get('confidence', 0.0)
        current_price = signal.get('price', current_prices.get(ticker, 0))
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        # 2. Pre-execution checks
        checks_passed, check_reason = self._perform_pre_execution_checks(
            ticker, signal_type, confidence, current_price, account_balance
        )
        
        if not checks_passed:
            return ExecutionResult(
                success=False,
                signal=signal_type,
                ticker=ticker,
                main_order_id=None,
                stop_order_id=None,
                profit_order_id=None,
                entry_price=None,
                shares=None,
                stop_loss_price=None,
                take_profit_price=None,
                reason=f"Pre-execution check failed: {check_reason}"
            )
        
        # 3. Calculate position size
        shares = self._calculate_position_size(
            ticker, current_price, account_balance, stop_loss
        )
        
        if shares <= 0:
            return ExecutionResult(
                success=False,
                signal=signal_type,
                ticker=ticker,
                main_order_id=None,
                stop_order_id=None,
                profit_order_id=None,
                entry_price=None,
                shares=None,
                stop_loss_price=None,
                take_profit_price=None,
                reason='Calculated position size is invalid'
            )
        
        # 4. Execute the trade
        if signal_type == 'BUY':
            return self._execute_buy_order(
                ticker, shares, current_price, stop_loss, take_profit
            )
        elif signal_type == 'SELL':
            return self._execute_sell_order(
                ticker, shares, current_price, stop_loss, take_profit
            )
        
        return ExecutionResult(
            success=False,
            signal=signal_type,
            ticker=ticker,
            main_order_id=None,
            stop_order_id=None,
            profit_order_id=None,
            entry_price=None,
            shares=None,
            stop_loss_price=None,
            take_profit_price=None,
            reason='Invalid signal type'
        )
    
    def _perform_pre_execution_checks(self, 
                                     ticker: str,
                                     signal_type: str,
                                     confidence: float,
                                     current_price: float,
                                     account_balance: float) -> Tuple[bool, str]:
        """
        Perform validation checks before execution
        
        Returns:
            (passed, reason)
        """
        # Check 1: Market hours
        if not self.broker.is_market_open():
            return False, "Market is not open"
        
        # Check 2: Confidence threshold
        if confidence < 0.55:
            return False, f"Confidence too low: {confidence:.1%}"
        
        # Check 3: Price validity
        if current_price <= 0:
            return False, "Invalid price"
        
        # Check 4: Ticker configuration
        if ticker not in self.config.tickers:
            return False, f"Ticker {ticker} not configured"
        
        ticker_config = self.config.tickers[ticker]
        
        # Check 5: Price bounds
        if not (ticker_config.min_price <= current_price <= ticker_config.max_price):
            return False, f"Price {current_price} outside bounds [{ticker_config.min_price}, {ticker_config.max_price}]"
        
        # Check 6: Account balance
        min_required = current_price * 10  # Minimum 10 shares
        if account_balance < min_required:
            return False, f"Insufficient funds: {account_balance:.2f} < {min_required:.2f}"
        
        # Check 7: Daily trade limit
        trades_today = len([t for t in self.execution_history 
                           if t.timestamp.date() == datetime.now().date()])
        if trades_today >= self.config.risk_rules.MAX_DAILY_TRADES:
            return False, f"Daily trade limit ({self.config.risk_rules.MAX_DAILY_TRADES}) reached"
        
        return True, "OK"
    
    def _calculate_position_size(self,
                                 ticker: str,
                                 current_price: float,
                                 account_balance: float,
                                 stop_loss_price: Optional[float]) -> int:
        """
        Calculate position size based on risk management
        
        Returns:
            Number of shares to trade
        """
        if not stop_loss_price or current_price <= 0:
            return 0
        
        ticker_config = self.config.tickers[ticker]
        
        # Risk per trade (2% of account)
        risk_amount = account_balance * 0.02
        
        # Risk per share
        risk_per_share = abs(current_price - stop_loss_price)
        
        if risk_per_share <= 0:
            return 0
        
        # Shares = Risk amount / Risk per share
        shares = int(risk_amount / risk_per_share)
        
        # Validate against limits
        shares = min(shares, ticker_config.max_position_size)
        shares = max(shares, 1)  # At least 1 share
        
        logger.info(f"Position size for {ticker}: {shares} shares (risk: ${risk_amount:.2f})")
        
        return shares
    
    def _execute_buy_order(self,
                          ticker: str,
                          shares: int,
                          entry_price: float,
                          stop_loss: float,
                          take_profit: float) -> ExecutionResult:
        """Execute a BUY order with stop loss and take profit"""
        
        try:
            # 1. Place main BUY order (LIMIT order for better fills)
            buy_order = OrderData(
                order_id="",
                symbol=ticker,
                side=OrderSide.BUY,
                quantity=shares,
                order_type=OrderType.LIMIT,
                limit_price=entry_price
            )
            
            main_order_id = self.broker.place_order(buy_order)
            
            if not main_order_id:
                return ExecutionResult(
                    success=False,
                    signal='BUY',
                    ticker=ticker,
                    main_order_id=None,
                    stop_order_id=None,
                    profit_order_id=None,
                    entry_price=None,
                    shares=None,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason='Failed to place main BUY order'
                )
            
            logger.info(f"BUY order placed: {ticker} x{shares} @ ${entry_price:.2f}")
            
            # 2. Place STOP LOSS order (activate after entry fills)
            stop_order_id = None
            if stop_loss > 0:
                stop_order = OrderData(
                    order_id="",
                    symbol=ticker,
                    side=OrderSide.SELL,
                    quantity=shares,
                    order_type=OrderType.STOP,
                    stop_price=stop_loss
                )
                stop_order_id = self.broker.place_order(stop_order)
                logger.info(f"STOP LOSS order placed: {ticker} @ ${stop_loss:.2f}")
            
            # 3. Place TAKE PROFIT order (activate after entry fills)
            profit_order_id = None
            if take_profit > 0:
                profit_order = OrderData(
                    order_id="",
                    symbol=ticker,
                    side=OrderSide.SELL,
                    quantity=shares,
                    order_type=OrderType.LIMIT,
                    limit_price=take_profit
                )
                profit_order_id = self.broker.place_order(profit_order)
                logger.info(f"TAKE PROFIT order placed: {ticker} @ ${take_profit:.2f}")
            
            result = ExecutionResult(
                success=True,
                signal='BUY',
                ticker=ticker,
                main_order_id=main_order_id,
                stop_order_id=stop_order_id,
                profit_order_id=profit_order_id,
                entry_price=entry_price,
                shares=shares,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit,
                reason='BUY order executed successfully'
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error executing BUY order: {e}")
            return ExecutionResult(
                success=False,
                signal='BUY',
                ticker=ticker,
                main_order_id=None,
                stop_order_id=None,
                profit_order_id=None,
                entry_price=None,
                shares=None,
                stop_loss_price=None,
                take_profit_price=None,
                reason=f'Exception: {str(e)}'
            )
    
    def _execute_sell_order(self,
                           ticker: str,
                           shares: int,
                           exit_price: float,
                           stop_loss: float,
                           take_profit: float) -> ExecutionResult:
        """Execute a SELL order with stop loss and take profit"""
        
        try:
            # Get current position
            position = self.broker.get_position(ticker)
            
            if not position or position.quantity <= 0:
                return ExecutionResult(
                    success=False,
                    signal='SELL',
                    ticker=ticker,
                    main_order_id=None,
                    stop_order_id=None,
                    profit_order_id=None,
                    entry_price=None,
                    shares=None,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason=f'No position to sell for {ticker}'
                )
            
            # Sell actual position (not more)
            sell_shares = min(shares, int(position.quantity))
            
            # Place SELL order
            sell_order = OrderData(
                order_id="",
                symbol=ticker,
                side=OrderSide.SELL,
                quantity=sell_shares,
                order_type=OrderType.LIMIT,
                limit_price=exit_price
            )
            
            main_order_id = self.broker.place_order(sell_order)
            
            if not main_order_id:
                return ExecutionResult(
                    success=False,
                    signal='SELL',
                    ticker=ticker,
                    main_order_id=None,
                    stop_order_id=None,
                    profit_order_id=None,
                    entry_price=None,
                    shares=None,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason='Failed to place SELL order'
                )
            
            logger.info(f"SELL order placed: {ticker} x{sell_shares} @ ${exit_price:.2f}")
            
            result = ExecutionResult(
                success=True,
                signal='SELL',
                ticker=ticker,
                main_order_id=main_order_id,
                stop_order_id=None,
                profit_order_id=None,
                entry_price=exit_price,
                shares=sell_shares,
                stop_loss_price=stop_loss,
                take_profit_price=take_profit,
                reason='SELL order executed successfully'
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error executing SELL order: {e}")
            return ExecutionResult(
                success=False,
                signal='SELL',
                ticker=ticker,
                main_order_id=None,
                stop_order_id=None,
                profit_order_id=None,
                entry_price=None,
                shares=None,
                stop_loss_price=None,
                take_profit_price=None,
                reason=f'Exception: {str(e)}'
            )
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        total_executions = len(self.execution_history)
        successful = len([e for e in self.execution_history if e.success])
        failed = total_executions - successful
        
        buy_orders = len([e for e in self.execution_history if e.signal == 'BUY' and e.success])
        sell_orders = len([e for e in self.execution_history if e.signal == 'SELL' and e.success])
        
        return {
            'total_executions': total_executions,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_executions * 100) if total_executions > 0 else 0,
            'buy_orders': buy_orders,
            'sell_orders': sell_orders,
            'last_execution': self.execution_history[-1].timestamp if self.execution_history else None
        }
