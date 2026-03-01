"""
Live Trading Monitoring Dashboard - ÉTAPE 24
==============================================

Real-time monitoring system for live trading with:
- Daily P&L tracking
- Position monitoring
- Risk limit alerts
- Trade logging
- Emergency procedures

Usage:
    from live_monitoring import TradingMonitor
    monitor = TradingMonitor()
    monitor.print_dashboard()
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"  # Red - Immediate action required
    WARNING = "WARNING"    # Orange - Attention needed
    INFO = "INFO"          # Blue - Information only


@dataclass
class TradeLog:
    """Single trade record"""
    timestamp: str
    ticker: str
    action: str  # BUY or SELL
    shares: int
    price: float
    p_l: float
    p_l_pct: float
    commission: float
    status: str  # FILLED, PARTIAL, REJECTED


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time"""
    timestamp: str
    equity: float
    cash: float
    positions_value: float
    daily_pl: float
    daily_pl_pct: float
    unrealized_pl: float
    realized_pl: float


class TradingMonitor:
    """Main monitoring dashboard class"""
    
    def __init__(self, initial_capital: float = 100000.0):
        """Initialize monitor"""
        self.initial_capital = initial_capital
        self.current_equity = initial_capital
        self.current_cash = initial_capital
        
        self.trade_log: List[TradeLog] = []
        self.portfolio_snapshots: List[PortfolioSnapshot] = []
        self.alerts: List[Dict] = []
        self.positions: Dict[str, Dict] = {}  # {'MSFT': {'shares': 100, 'avg_price': 470}}
        
        self.session_start_time = datetime.now().isoformat()
        self.session_daily_pl = 0.0
        self.consecutive_losses = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    def add_trade(self, ticker: str, action: str, shares: int, price: float, 
                  commission: float = 0.0, status: str = "FILLED"):
        """
        Log a trade execution
        
        Args:
            ticker: Stock symbol
            action: 'BUY' or 'SELL'
            shares: Number of shares
            price: Execution price
            commission: Transaction cost
            status: Order fill status
        """
        trade_value = shares * price
        trade_cost = trade_value + commission
        
        # Update cash and equity
        if action == "BUY":
            self.current_cash -= trade_cost
        else:  # SELL
            self.current_cash += (trade_value - commission)
        
        # Update position
        if ticker not in self.positions:
            self.positions[ticker] = {'shares': 0, 'avg_price': 0.0, 'entry_value': 0.0}
        
        pos = self.positions[ticker]
        if action == "BUY":
            # Update average price
            total_cost = (pos['avg_price'] * pos['shares']) + trade_cost
            pos['shares'] += shares
            pos['avg_price'] = total_cost / pos['shares'] if pos['shares'] > 0 else 0
            pos['entry_value'] = pos['avg_price'] * pos['shares']
        else:  # SELL
            pos['shares'] -= shares
            if pos['shares'] == 0:
                pos['avg_price'] = 0.0
        
        # Log trade
        p_l = (price - pos['avg_price']) * shares if action == "SELL" else 0.0
        p_l_pct = (p_l / (pos['avg_price'] * shares)) * 100 if action == "SELL" and pos['avg_price'] > 0 else 0.0
        
        trade = TradeLog(
            timestamp=datetime.now().isoformat(),
            ticker=ticker,
            action=action,
            shares=shares,
            price=price,
            p_l=p_l,
            p_l_pct=p_l_pct,
            commission=commission,
            status=status
        )
        
        self.trade_log.append(trade)
        self.total_trades += 1
        
        if p_l > 0:
            self.winning_trades += 1
            self.consecutive_losses = 0
        elif p_l < 0:
            self.losing_trades += 1
            self.consecutive_losses += 1
    
    def update_equity(self, current_prices: Dict[str, float]):
        """Update portfolio equity with current market prices"""
        positions_value = 0.0
        unrealized_pl = 0.0
        
        for ticker, pos in self.positions.items():
            if pos['shares'] > 0 and ticker in current_prices:
                current_value = pos['shares'] * current_prices[ticker]
                positions_value += current_value
                unrealized_pl += current_value - (pos['avg_price'] * pos['shares'])
        
        self.current_equity = self.current_cash + positions_value
        self.positions_value = positions_value
        self.unrealized_pl = unrealized_pl
        
        # Update session daily P&L
        self.session_daily_pl = self.current_equity - self.initial_capital
    
    def check_daily_loss_limit(self, limit_pct: float = -2.0) -> bool:
        """
        Check if daily loss limit exceeded
        
        Args:
            limit_pct: Daily loss limit as percentage (e.g., -2.0 for -2%)
        
        Returns:
            True if limit exceeded (STOP TRADING), False otherwise
        """
        daily_loss_pct = (self.session_daily_pl / self.initial_capital) * 100
        exceeded = daily_loss_pct <= limit_pct
        
        if exceeded:
            self.add_alert(
                AlertLevel.CRITICAL,
                "DAILY LOSS LIMIT EXCEEDED",
                f"Daily P&L: {daily_loss_pct:.2f}% (limit: {limit_pct:.2f}%) - STOP ALL TRADING"
            )
        
        return exceeded
    
    def check_consecutive_losses(self, limit: int = 5) -> bool:
        """
        Check if consecutive loss limit exceeded
        
        Args:
            limit: Maximum consecutive losses before pause
        
        Returns:
            True if limit exceeded (PAUSE TRADING), False otherwise
        """
        exceeded = self.consecutive_losses >= limit
        
        if exceeded:
            self.add_alert(
                AlertLevel.WARNING,
                "CONSECUTIVE LOSSES LIMIT",
                f"Consecutive losses: {self.consecutive_losses} (limit: {limit}) - PAUSE 1 DAY"
            )
        
        return exceeded
    
    def check_position_limits(self, max_positions: int = 4) -> bool:
        """
        Check if position limits exceeded
        
        Args:
            max_positions: Maximum number of concurrent positions
        
        Returns:
            True if limit exceeded, False otherwise
        """
        active_positions = sum(1 for p in self.positions.values() if p['shares'] > 0)
        exceeded = active_positions > max_positions
        
        if exceeded:
            self.add_alert(
                AlertLevel.WARNING,
                "POSITION LIMIT EXCEEDED",
                f"Active positions: {active_positions} (max: {max_positions})"
            )
        
        return exceeded
    
    def add_alert(self, level: AlertLevel, title: str, message: str):
        """Add an alert to the system"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'title': title,
            'message': message
        }
        self.alerts.append(alert)
        self._print_alert(alert)
    
    @staticmethod
    def _print_alert(alert: Dict):
        """Print alert to console"""
        level = alert['level']
        color_map = {
            'CRITICAL': '🛑',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }
        emoji = color_map.get(level, '•')
        print(f"{emoji} {level} [{alert['title']}]: {alert['message']}")
    
    def snapshot(self):
        """Create portfolio snapshot"""
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now().isoformat(),
            equity=self.current_equity,
            cash=self.current_cash,
            positions_value=getattr(self, 'positions_value', 0.0),
            daily_pl=self.session_daily_pl,
            daily_pl_pct=(self.session_daily_pl / self.initial_capital) * 100,
            unrealized_pl=getattr(self, 'unrealized_pl', 0.0),
            realized_pl=self.session_daily_pl - getattr(self, 'unrealized_pl', 0.0)
        )
        self.portfolio_snapshots.append(snapshot)
        return snapshot
    
    def print_dashboard(self):
        """Print monitoring dashboard"""
        print("\n" + "="*70)
        print("LIVE TRADING DASHBOARD")
        print("="*70)
        
        # Account summary
        daily_pl_pct = (self.session_daily_pl / self.initial_capital) * 100
        equity_change = ((self.current_equity / self.initial_capital) - 1) * 100
        
        print(f"\nACCOUNT SUMMARY")
        print(f"  Initial Capital:  ${self.initial_capital:>15,.2f}")
        print(f"  Current Equity:   ${self.current_equity:>15,.2f} ({equity_change:+.2f}%)")
        print(f"  Available Cash:   ${self.current_cash:>15,.2f}")
        print(f"  Daily P&L:        ${self.session_daily_pl:>15,.2f} ({daily_pl_pct:+.2f}%)")
        
        # Trading statistics
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        print(f"\nTRADING STATISTICS")
        print(f"  Total Trades:     {self.total_trades:>15}")
        print(f"  Winning Trades:   {self.winning_trades:>15}")
        print(f"  Losing Trades:    {self.losing_trades:>15}")
        print(f"  Win Rate:         {win_rate:>14.1f}%")
        print(f"  Consecutive Losses: {self.consecutive_losses:>11}")
        
        # Positions
        if self.positions:
            print(f"\nOPEN POSITIONS")
            for ticker, pos in self.positions.items():
                if pos['shares'] > 0:
                    print(f"  {ticker}: {pos['shares']:>3} shares @ ${pos['avg_price']:>7.2f}")
        else:
            print(f"\nOPEN POSITIONS: None")
        
        # Alerts
        if self.alerts:
            print(f"\nRECENT ALERTS ({len(self.alerts)} total)")
            for alert in self.alerts[-5:]:  # Show last 5 alerts
                emoji_map = {'CRITICAL': '🛑', 'WARNING': '⚠️', 'INFO': 'ℹ️'}
                emoji = emoji_map.get(alert['level'], '•')
                print(f"  {emoji} {alert['level']}: {alert['title']}")
        
        print("\n" + "="*70)
    
    def save_session_log(self, filename: str):
        """Save session log to JSON file"""
        session_data = {
            'session_start': self.session_start_time,
            'session_end': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'final_equity': self.current_equity,
            'daily_pl': self.session_daily_pl,
            'trades': [asdict(t) for t in self.trade_log],
            'alerts': self.alerts,
            'snapshots': [asdict(s) for s in self.portfolio_snapshots]
        }
        
        with open(filename, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"Session log saved to {filename}")


class EmergencyProcedures:
    """Emergency procedures for trading halt"""
    
    @staticmethod
    def broker_connection_lost(monitor: TradingMonitor):
        """Handle broker connection loss"""
        print("\n" + "🚨" * 35)
        print("EMERGENCY: BROKER CONNECTION LOST")
        print("🚨" * 35)
        print("\nPROCEDURE:")
        print("1. IMMEDIATELY CLOSE all open orders via TWS (if accessible)")
        print("2. Verify connection: ping broker.twsapi.com")
        print("3. If connection not restored in 5 minutes, contact broker phone support")
        print("4. Manually close all positions if broker unavailable > 15 minutes")
        print("\nCURRENT POSITIONS:")
        for ticker, pos in monitor.positions.items():
            if pos['shares'] > 0:
                print(f"  {ticker}: {pos['shares']} shares @ ${pos['avg_price']:.2f}")
        print("\nEstimated current values: Check market prices for each position")
    
    @staticmethod
    def daily_loss_limit_hit(monitor: TradingMonitor):
        """Handle daily loss limit breached"""
        print("\n" + "🛑" * 35)
        print("EMERGENCY: DAILY LOSS LIMIT EXCEEDED (-2%)")
        print("🛑" * 35)
        print("\nPROCEDURE:")
        print("1. IMMEDIATELY CLOSE all open positions for today")
        print("2. Set daily loss flag in trading system")
        print("3. NO NEW TRADES ALLOWED until next trading day")
        print("4. Document what happened - review trades")
        print("5. Analyze losing trades - identify pattern")
        print("\nCURRENT STATUS:")
        daily_pl_pct = (monitor.session_daily_pl / monitor.initial_capital) * 100
        print(f"  Daily P&L: ${monitor.session_daily_pl:,.2f} ({daily_pl_pct:.2f}%)")
        print(f"  Positions to close: {sum(1 for p in monitor.positions.values() if p['shares'] > 0)}")
    
    @staticmethod
    def system_error(monitor: TradingMonitor, error_details: str):
        """Handle system error"""
        print("\n" + "⚠️" * 35)
        print("EMERGENCY: SYSTEM ERROR")
        print("⚠️" * 35)
        print(f"\nError Details: {error_details}")
        print("\nPROCEDURE:")
        print("1. LOG the error details immediately")
        print("2. CHECK open positions in TWS (independent of system)")
        print("3. If system cannot recover in 5 minutes:")
        print("   a. Manually close high-risk positions in TWS")
        print("   b. Notify broker support of system issue")
        print("   c. Restart trading system after analysis")
        print("4. After restart, check system state vs TWS state (reconcile)")
        
        monitor.add_alert(
            AlertLevel.CRITICAL,
            "SYSTEM ERROR",
            f"System has encountered an error: {error_details}"
        )
    
    @staticmethod
    def excessive_slippage(monitor: TradingMonitor, avg_slippage_pct: float):
        """Handle excessive slippage detection"""
        print("\n" + "⚠️" * 35)
        print("WARNING: EXCESSIVE SLIPPAGE DETECTED")
        print("⚠️" * 35)
        print(f"\nAverage Slippage: {avg_slippage_pct:.3f}%")
        print("Expected: 0.05% | Warning threshold: 0.10%")
        print("\nPROCEDURE:")
        print("1. Check market liquidity for your symbols")
        print("2. Verify order types (limit vs market)")
        print("3. Consider switching to limit orders")
        print("4. Check broker connection quality")
        print("5. If persists, contact broker support")
        
        if avg_slippage_pct > 0.10:
            monitor.add_alert(
                AlertLevel.WARNING,
                "HIGH SLIPPAGE",
                f"Execution slippage {avg_slippage_pct:.3f}% exceeds threshold"
            )


if __name__ == "__main__":
    # Test monitoring dashboard
    monitor = TradingMonitor(initial_capital=5000)
    
    # Add some sample trades
    monitor.add_trade('MSFT', 'BUY', 10, 470.0, commission=10)
    monitor.update_equity({'MSFT': 475})
    
    monitor.add_trade('MSFT', 'SELL', 10, 475.0, commission=10)
    monitor.update_equity({'MSFT': 475})
    
    # Check limits
    print(f"Daily loss limit exceeded: {monitor.check_daily_loss_limit()}")
    print(f"Position limit exceeded: {monitor.check_position_limits(1)}")
    
    # Print dashboard
    monitor.print_dashboard()
