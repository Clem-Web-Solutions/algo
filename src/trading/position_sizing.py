"""
Live Trading Position Sizing Calculator - ÉTAPE 24
===================================================

Calculates optimal position sizes using Kelly Criterion for live trading

Features:
- Kelly Criterion calculation
- Conservative (half-Kelly) sizing
- Phase-specific allocation
- Risk per trade calculations
- Position limit enforcement

Usage:
    from position_sizing import PositionSizingCalculator
    calc = PositionSizingCalculator()
    sizes = calc.calculate_phase1_sizes(capital=5000)
"""

import json
from typing import Dict, Tuple
from live_trading_config import LiveTradingConfig, TradingPhase


class KellyCriterionCalculator:
    """Calculates Kelly Criterion position sizing"""
    
    @staticmethod
    def calculate_kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly Criterion fraction: f* = (p*b - q) / b
        where:
          p = win rate (0.0-1.0)
          b = payoff ratio (avg_win / abs(avg_loss))
          q = loss rate (1 - p)
        
        Args:
            win_rate: Percentage of winning trades (0.0-1.0)
            avg_win: Average win per trade (% or $)
            avg_loss: Average loss per trade (absolute value, negative)
        
        Returns:
            Kelly fraction (0.0-1.0), where values > 1.0 indicate overbetting
        """
        if avg_loss == 0:
            return 0.0
        
        payoff_ratio = abs(avg_win / avg_loss)
        q = 1.0 - win_rate
        
        # f* = (p*b - q) / b
        kelly_fraction = (win_rate * payoff_ratio - q) / payoff_ratio
        
        # Ensure it's not negative
        return max(kelly_fraction, 0.0)
    
    @staticmethod
    def calculate_conservative_kelly(kelly_fraction: float, conservative_factor: float = 0.5) -> float:
        """
        Apply conservative factor to Kelly (typically half-Kelly)
        
        Args:
            kelly_fraction: Raw Kelly fraction from calculate_kelly_fraction
            conservative_factor: Adjustment factor (0.5 = half-Kelly, 0.25 = quarter-Kelly)
        
        Returns:
            Conservative Kelly fraction
        """
        return kelly_fraction * conservative_factor
    
    @staticmethod
    def apply_limits(kelly_fraction: float, min_pct: float = 0.01, max_pct: float = 0.25) -> float:
        """
        Apply minimum and maximum limits to Kelly fraction
        
        Args:
            kelly_fraction: Calculated Kelly fraction
            min_pct: Minimum position size (0.01 = 1%)
            max_pct: Maximum position size (0.25 = 25%)
        
        Returns:
            Limited Kelly fraction
        """
        return max(min_pct, min(kelly_fraction, max_pct))


class PositionSizingCalculator:
    """Calculates position sizes for live trading"""
    
    def __init__(self, capital: float = 100000.0):
        """Initialize with account capital"""
        self.capital = capital
        self.config = LiveTradingConfig()
        self.kelly = KellyCriterionCalculator()
        
        # Historical performance metrics from ÉTAPE 22
        self.ticker_metrics = {
            'AAPL': {
                'win_rate': 0.50,
                'avg_win': 0.01,
                'avg_loss': -0.02,
                'return_pct': -0.25,
                'status': 'Poor - Avoid'
            },
            'GOOGL': {
                'win_rate': 0.756,
                'avg_win': 0.11,
                'avg_loss': -0.02,
                'return_pct': 13.38,
                'status': 'Excellent - Priority'
            },
            'MSFT': {
                'win_rate': 1.00,
                'avg_win': 0.0184,
                'avg_loss': -0.01,
                'return_pct': 1.84,
                'status': 'Reliable - Anchor'
            },
            'TSLA': {
                'win_rate': 0.525,
                'avg_win': 0.0572,
                'avg_loss': -0.01,
                'return_pct': 5.72,
                'status': 'Conditional - Selective'
            }
        }
    
    def calculate_kelly_for_ticker(self, ticker: str, conservative_factor: float = 0.5) -> Tuple[float, Dict]:
        """
        Calculate Kelly fraction for a ticker
        
        Args:
            ticker: Stock symbol
            conservative_factor: Adjustment for risk (0.5 = half-Kelly)
        
        Returns:
            Tuple of (kelly_fraction, detailed_metrics)
        """
        metrics = self.ticker_metrics.get(ticker, {})
        
        kelly_raw = self.kelly.calculate_kelly_fraction(
            win_rate=metrics.get('win_rate', 0.45),
            avg_win=metrics.get('avg_win', 0.01),
            avg_loss=metrics.get('avg_loss', -0.01)
        )
        
        kelly_conservative = self.kelly.calculate_conservative_kelly(kelly_raw, conservative_factor)
        kelly_limited = self.kelly.apply_limits(kelly_conservative)
        
        return kelly_limited, {
            'ticker': ticker,
            'kelly_raw': kelly_raw,
            'kelly_conservative': kelly_conservative,
            'kelly_final': kelly_limited,
            'win_rate': metrics.get('win_rate', 0),
            'avg_win': metrics.get('avg_win', 0),
            'avg_loss': metrics.get('avg_loss', 0),
            'status': metrics.get('status', 'Unknown')
        }
    
    def calculate_phase1_sizes(self, capital: float = 5000.0) -> Dict[str, Dict]:
        """
        Calculate position sizes for Phase 1 (MSFT only)
        
        Args:
            capital: Available capital for phase 1
        
        Returns:
            Dictionary with position sizing for each ticker
        """
        allocation = {}
        
        # MSFT gets 100% in Phase 1
        kelly_fraction, metrics = self.calculate_kelly_for_ticker('MSFT')
        
        allocation['MSFT'] = {
            'allocation_pct': 100.0,
            'kelly_fraction': kelly_fraction,
            'capital_allocated': capital,
            'shares_at_470': int(capital / 470),  # Approx share count at MSFT price
            'max_loss_usd': capital * -0.02,  # 2% max loss = daily stop
            'expected_return_pct': 1.84,
            'risk_per_trade': capital * kelly_fraction,
            'metrics': metrics
        }
        
        return allocation
    
    def calculate_phase2_sizes(self, capital: float = 10000.0) -> Dict[str, Dict]:
        """
        Calculate position sizes for Phase 2 (MSFT + GOOGL)
        
        Args:
            capital: Available capital for phase 2
        
        Returns:
            Dictionary with position sizing for each ticker
        """
        allocation = {}
        
        # MSFT 50%, GOOGL 50%
        for ticker, pct in [('MSFT', 0.50), ('GOOGL', 0.50)]:
            kelly_fraction, metrics = self.calculate_kelly_for_ticker(ticker)
            capital_for_ticker = capital * pct
            
            allocation[ticker] = {
                'allocation_pct': pct * 100,
                'kelly_fraction': kelly_fraction,
                'capital_allocated': capital_for_ticker,
                'shares_at_current': self._estimate_shares(ticker, capital_for_ticker),
                'max_loss_usd': capital_for_ticker * -0.02,
                'expected_return_pct': metrics['avg_win'] * 100,
                'risk_per_trade': capital_for_ticker * kelly_fraction,
                'metrics': metrics
            }
        
        return allocation
    
    def calculate_phase3_sizes(self, capital: float = 100000.0) -> Dict[str, Dict]:
        """
        Calculate position sizes for Phase 3 (All 4 tickers, full Kelly)
        
        Args:
            capital: Available capital for phase 3
        
        Returns:
            Dictionary with position sizing for each ticker
        """
        allocation = {}
        
        # Full Kelly allocation based on ÉTAPE 12 optimization
        ticker_allocations = {
            'AAPL': 0.05,    # 5% - small, diversification only
            'GOOGL': 0.30,   # 30% - large, best opportunity
            'MSFT': 0.50,    # 50% - anchor, most reliable
            'TSLA': 0.15     # 15% - selective, conditional
        }
        
        for ticker, pct in ticker_allocations.items():
            kelly_fraction, metrics = self.calculate_kelly_for_ticker(ticker)
            capital_for_ticker = capital * pct
            
            allocation[ticker] = {
                'allocation_pct': pct * 100,
                'kelly_fraction': kelly_fraction,
                'capital_allocated': capital_for_ticker,
                'shares_at_current': self._estimate_shares(ticker, capital_for_ticker),
                'max_loss_usd': capital_for_ticker * -0.02,
                'expected_return_pct': metrics['avg_win'] * 100,
                'risk_per_trade': capital_for_ticker * kelly_fraction,
                'metrics': metrics
            }
        
        return allocation
    
    @staticmethod
    def _estimate_shares(ticker: str, capital: float) -> int:
        """Estimate number of shares based on approximate prices"""
        approximate_prices = {
            'AAPL': 270,
            'GOOGL': 315,
            'MSFT': 470,
            'TSLA': 250
        }
        price = approximate_prices.get(ticker, 300)
        return int(capital / price)
    
    def get_daily_risk_budget(self, phase: TradingPhase, capital: float) -> Dict[str, float]:
        """
        Calculate daily risk budget based on phase
        
        Args:
            phase: Current trading phase
            capital: Available capital
        
        Returns:
            Dictionary with daily risk limits
        """
        return {
            'daily_loss_limit_pct': -2.0,
            'daily_loss_limit_usd': capital * -0.02,
            'weekly_loss_limit_pct': -5.0,
            'weekly_loss_limit_usd': capital * -0.05,
            'max_consecutive_losses': 5,
            'position_timeout_days': 30
        }


class PositionSizingSummary:
    """Generates readable summary of position sizing"""
    
    @staticmethod
    def print_phase1_summary(capital: float = 5000.0):
        """Print Phase 1 position sizing summary"""
        calc = PositionSizingCalculator(capital)
        sizes = calc.calculate_phase1_sizes(capital)
        
        print("\n" + "="*70)
        print("PHASE 1 POSITION SIZING - MSFT ONLY")
        print("="*70)
        print(f"\nTotal Capital: ${capital:,.2f}")
        print(f"Risk per trade: ${sizes['MSFT']['risk_per_trade']:,.2f}")
        print(f"Max daily loss: ${sizes['MSFT']['max_loss_usd']:,.2f}")
        print(f"Expected return: {sizes['MSFT']['expected_return_pct']:.2f}%")
        
        print(f"\nMSFT Allocation:")
        print(f"  Pct: 100%")
        print(f"  Capital: ${sizes['MSFT']['capital_allocated']:,.2f}")
        print(f"  Est. Shares: {sizes['MSFT']['shares_at_current']}")
        print(f"  Kelly Fraction: {sizes['MSFT']['kelly_fraction']:.2%}")
        print(f"  Status: {sizes['MSFT']['metrics']['status']}")
    
    @staticmethod
    def print_phase2_summary(capital: float = 10000.0):
        """Print Phase 2 position sizing summary"""
        calc = PositionSizingCalculator(capital)
        sizes = calc.calculate_phase2_sizes(capital)
        
        print("\n" + "="*70)
        print("PHASE 2 POSITION SIZING - MSFT + GOOGL")
        print("="*70)
        print(f"\nTotal Capital: ${capital:,.2f}")
        
        total_risk = 0
        for ticker in ['MSFT', 'GOOGL']:
            s = sizes[ticker]
            total_risk += s['risk_per_trade']
            print(f"\n{ticker} Allocation:")
            print(f"  Pct: {s['allocation_pct']:.1f}%")
            print(f"  Capital: ${s['capital_allocated']:,.2f}")
            print(f"  Est. Shares: {s['shares_at_current']}")
            print(f"  Kelly Fraction: {s['kelly_fraction']:.2%}")
            print(f"  Max loss: ${s['max_loss_usd']:,.2f}")
            print(f"  Status: {s['metrics']['status']}")
        
        print(f"\nTotal Risk: ${total_risk:,.2f}")
        print(f"Daily Loss Limit (-2%): ${capital * -0.02:,.2f}")
    
    @staticmethod
    def print_phase3_summary(capital: float = 100000.0):
        """Print Phase 3 position sizing summary"""
        calc = PositionSizingCalculator(capital)
        sizes = calc.calculate_phase3_sizes(capital)
        
        print("\n" + "="*70)
        print("PHASE 3 POSITION SIZING - FULL PORTFOLIO")
        print("="*70)
        print(f"\nTotal Capital: ${capital:,.2f}")
        print(f"Leverage: {sum(s['allocation_pct'] for s in sizes.values()) / 100:.2f}x")
        
        total_risk = 0
        for ticker in ['AAPL', 'GOOGL', 'MSFT', 'TSLA']:
            if ticker in sizes:
                s = sizes[ticker]
                total_risk += s['risk_per_trade']
                print(f"\n{ticker} Allocation:")
                print(f"  Pct: {s['allocation_pct']:.1f}%")
                print(f"  Capital: ${s['capital_allocated']:,.2f}")
                print(f"  Est. Shares: {s['shares_at_current']}")
                print(f"  Kelly Fraction: {s['kelly_fraction']:.2%}")
                print(f"  Max loss: ${s['max_loss_usd']:,.2f}")
                print(f"  Status: {s['metrics']['status']}")
        
        print(f"\nTotal Risk: ${total_risk:,.2f}")
        print(f"Daily Loss Limit (-2%): ${capital * -0.02:,.2f}")


if __name__ == "__main__":
    # Test position sizing
    PositionSizingSummary.print_phase1_summary(5000)
    PositionSizingSummary.print_phase2_summary(10000)
    PositionSizingSummary.print_phase3_summary(100000)
