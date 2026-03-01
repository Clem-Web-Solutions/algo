"""
Live Trading Configuration Module - ÉTAPE 24
==============================================

Manages all configuration for live trading deployment including:
- Phase-specific parameters
- Position sizing and Kelly allocation
- Risk management rules
- Emergency procedures
- Monitoring requirements

Usage:
    from live_trading_config import LiveTradingConfig, Phase1Trading
    config = LiveTradingConfig()
    phase1 = Phase1Trading(config)
"""

from datetime import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class TradingPhase(Enum):
    """Enum for trading phases"""
    PHASE_1 = "phase_1"  # Days 1-5: MSFT only, $2-5k
    PHASE_2 = "phase_2"  # Days 6-20: MSFT + GOOGL, $5-10k
    PHASE_3 = "phase_3"  # Days 21+: All 4 tickers, Full allocation


@dataclass
class TickerConfig:
    """Configuration for a specific ticker"""
    symbol: str
    max_allocation_pct: float  # Max % of capital to allocate
    max_position_size: int     # Max shares to hold
    min_price: float           # Minimum valid price
    max_price: float           # Maximum valid price
    kelly_fraction: float      # Kelly criterion fraction (0.0-1.0)
    preferred_in_phases: List[TradingPhase]  # Phases where this ticker is active


@dataclass
class RiskManagementRules:
    """Risk management rules for live trading"""
    DAILY_LOSS_LIMIT_PCT: float = -2.0      # Stop all trading if hit -2% daily
    DAILY_LOSS_LIMIT_USD: float = -2000.0   # Stop all trading if hit -$2000
    WEEKLY_LOSS_LIMIT_PCT: float = -5.0     # Reduce position size if hit -5% weekly
    CONSECUTIVE_LOSS_LIMIT: int = 5          # Pause if 5 consecutive losses
    CONSECUTIVE_LOSS_PAUSE_DAYS: int = 1    # Pause for N trading days
    MAX_DAILY_TRADES: int = 10               # Max trades per day
    MAX_POSITION_LEVERAGE: float = 2.0       # Max leverage allowed
    MAX_HOLDING_PERIOD_DAYS: int = 30       # Max days to hold a position
    MIN_PROFIT_TARGET_USD: float = 100.0    # Min profit target per trade


@dataclass
class TradingHours:
    """Market trading hours"""
    MARKET_OPEN: time = time(9, 30)     # 9:30 AM ET
    MARKET_CLOSE: time = time(15, 30)   # 3:30 PM ET
    POSITION_CLOSE_TIME: time = time(16, 0)  # 4:00 PM ET (close all)
    PRE_MARKET_START: time = time(4, 0)      # 4:00 AM ET
    AFTER_HOURS_END: time = time(20, 0)     # 8:00 PM ET
    
    ALLOWED_TRADING_HOURS = (MARKET_OPEN, MARKET_CLOSE)
    MANDATORY_CLOSE_TIME = POSITION_CLOSE_TIME


class LiveTradingConfig:
    """Main live trading configuration class"""
    
    def __init__(self):
        """Initialize live trading configuration"""
        self.initial_capital = 100000.0  # Full account size
        self.trading_hours = TradingHours()
        self.risk_rules = RiskManagementRules()
        
        # Define all tickers
        self.tickers = {
            'AAPL': TickerConfig(
                symbol='AAPL',
                max_allocation_pct=5.0,
                max_position_size=100,
                min_price=100.0,
                max_price=300.0,
                kelly_fraction=0.005,
                preferred_in_phases=[TradingPhase.PHASE_3]
            ),
            'GOOGL': TickerConfig(
                symbol='GOOGL',
                max_allocation_pct=15.0,
                max_position_size=150,
                min_price=100.0,
                max_price=500.0,
                kelly_fraction=0.15,
                preferred_in_phases=[TradingPhase.PHASE_2, TradingPhase.PHASE_3]
            ),
            'MSFT': TickerConfig(
                symbol='MSFT',
                max_allocation_pct=25.0,
                max_position_size=200,
                min_price=250.0,
                max_price=450.0,
                kelly_fraction=0.25,
                preferred_in_phases=[TradingPhase.PHASE_1, TradingPhase.PHASE_2, TradingPhase.PHASE_3]
            ),
            'TSLA': TickerConfig(
                symbol='TSLA',
                max_allocation_pct=8.0,
                max_position_size=150,
                min_price=150.0,
                max_price=350.0,
                kelly_fraction=0.08,
                preferred_in_phases=[TradingPhase.PHASE_2, TradingPhase.PHASE_3]
            )
        }
        
        # Phase-specific configurations
        self.phase_configs = {
            TradingPhase.PHASE_1: Phase1Config(self),
            TradingPhase.PHASE_2: Phase2Config(self),
            TradingPhase.PHASE_3: Phase3Config(self)
        }
    
    def get_config_for_phase(self, phase: TradingPhase) -> 'PhaseConfig':
        """Get configuration for a specific phase"""
        return self.phase_configs[phase]
    
    def get_active_tickers_for_phase(self, phase: TradingPhase) -> List[str]:
        """Get list of tickers active in a phase"""
        return [
            ticker for ticker, config in self.tickers.items()
            if phase in config.preferred_in_phases
        ]
    
    def get_daily_loss_limits(self) -> Dict[str, float]:
        """Get daily loss limits as dict"""
        return {
            'loss_pct': self.risk_rules.DAILY_LOSS_LIMIT_PCT,
            'loss_usd': self.risk_rules.DAILY_LOSS_LIMIT_USD,
            'consecutive_losses': self.risk_rules.CONSECUTIVE_LOSS_LIMIT
        }
    
    def get_position_sizing_for_phase(self, phase: TradingPhase) -> Dict[str, Dict]:
        """Get position sizing rules for a phase"""
        config = self.get_config_for_phase(phase)
        return config.get_position_allocation()


class PhaseConfig:
    """Base class for phase-specific configurations"""
    
    def __init__(self, parent_config: LiveTradingConfig):
        self.parent = parent_config
        self.phase_name = ""
        self.phase_number = 0
        self.starting_capital = 0.0
        self.max_capital = 0.0
        self.duration_days = 0
        self.max_positions = 0
        self.active_tickers = []
    
    def get_position_allocation(self) -> Dict[str, Dict]:
        """Return position sizing for each ticker in this phase"""
        raise NotImplementedError


class Phase1Config(PhaseConfig):
    """Phase 1 Configuration: Days 1-5, MSFT only, $2-5k"""
    
    def __init__(self, parent_config: LiveTradingConfig):
        super().__init__(parent_config)
        self.phase_name = "PHASE 1 - Initial Validation"
        self.phase_number = 1
        self.starting_capital = 2000.0
        self.max_capital = 5000.0
        self.duration_days = 5
        self.max_positions = 1
        self.active_tickers = ['MSFT']
        
        # Success criteria
        self.success_metrics = {
            'min_win_rate': 0.40,
            'max_drawdown_pct': -10.0,
            'required_profitability': False,  # Not required, just testing
            'execution_quality': 0.95  # 95% of orders should fill
        }
    
    def get_position_allocation(self) -> Dict[str, Dict]:
        """MSFT only in Phase 1"""
        allocation = {}
        for ticker, config in self.parent.tickers.items():
            if ticker in self.active_tickers:
                allocation[ticker] = {
                    'max_allocation_pct': 100.0,  # All capital to MSFT
                    'kelly_fraction': 0.25,
                    'max_positions': 1,
                    'sizing': 'CONSERVATIVE'
                }
        return allocation


class Phase2Config(PhaseConfig):
    """Phase 2 Configuration: Days 6-20, MSFT + GOOGL, $5-10k"""
    
    def __init__(self, parent_config: LiveTradingConfig):
        super().__init__(parent_config)
        self.phase_name = "PHASE 2 - Expansion"
        self.phase_number = 2
        self.starting_capital = 5000.0
        self.max_capital = 10000.0
        self.duration_days = 15  # 6-20 = 15 days
        self.max_positions = 2
        self.active_tickers = ['MSFT', 'GOOGL']
        
        # Success criteria
        self.success_metrics = {
            'min_win_rate': 0.45,
            'max_drawdown_pct': -8.0,
            'required_profitability': False,
            'execution_quality': 0.95,
            'all_systems_pass': True  # All monitoring systems must pass
        }
    
    def get_position_allocation(self) -> Dict[str, Dict]:
        """MSFT (50%) + GOOGL (50%) in Phase 2"""
        allocation = {}
        for ticker, config in self.parent.tickers.items():
            if ticker == 'MSFT':
                allocation[ticker] = {
                    'max_allocation_pct': 50.0,
                    'kelly_fraction': 0.25,
                    'max_positions': 1,
                    'sizing': 'BALANCED'
                }
            elif ticker == 'GOOGL':
                allocation[ticker] = {
                    'max_allocation_pct': 50.0,
                    'kelly_fraction': 0.15,
                    'max_positions': 1,
                    'sizing': 'BALANCED'
                }
        return allocation


class Phase3Config(PhaseConfig):
    """Phase 3 Configuration: Days 21+, All 4 tickers, Full allocation"""
    
    def __init__(self, parent_config: LiveTradingConfig):
        super().__init__(parent_config)
        self.phase_name = "PHASE 3 - Full Strategy"
        self.phase_number = 3
        self.starting_capital = 10000.0
        self.max_capital = 100000.0
        self.duration_days = 9999  # Ongoing
        self.max_positions = 4
        self.active_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        
        # Success criteria
        self.success_metrics = {
            'min_win_rate': 0.45,
            'max_drawdown_pct': -10.0,
            'required_profitability': True,  # Must be profitable
            'execution_quality': 0.95,
            'consistency': True  # Must show consistent returns
        }
    
    def get_position_allocation(self) -> Dict[str, Dict]:
        """Full Kelly allocation in Phase 3"""
        allocation = {}
        for ticker, config in self.parent.tickers.items():
            if ticker == 'AAPL':
                allocation[ticker] = {
                    'max_allocation_pct': 5.0,
                    'kelly_fraction': 0.005,
                    'max_positions': 1,
                    'sizing': 'SMALL'
                }
            elif ticker == 'GOOGL':
                allocation[ticker] = {
                    'max_allocation_pct': 30.0,
                    'kelly_fraction': 0.15,
                    'max_positions': 1,
                    'sizing': 'LARGE'
                }
            elif ticker == 'MSFT':
                allocation[ticker] = {
                    'max_allocation_pct': 50.0,
                    'kelly_fraction': 0.25,
                    'max_positions': 1,
                    'sizing': 'ANCHOR'
                }
            elif ticker == 'TSLA':
                allocation[ticker] = {
                    'max_allocation_pct': 15.0,
                    'kelly_fraction': 0.08,
                    'max_positions': 1,
                    'sizing': 'CONDITIONAL'
                }
        return allocation


# Module-level helper functions

def get_current_phase_from_days(days_trading: int) -> TradingPhase:
    """Determine current phase based on days trading"""
    if days_trading <= 5:
        return TradingPhase.PHASE_1
    elif days_trading <= 20:
        return TradingPhase.PHASE_2
    else:
        return TradingPhase.PHASE_3


def print_config_summary(config: LiveTradingConfig, phase: TradingPhase):
    """Print configuration summary"""
    phase_config = config.get_config_for_phase(phase)
    print("\n" + "="*60)
    print(f"{phase_config.phase_name}")
    print("="*60)
    print(f"Capital Range: ${phase_config.starting_capital:,.0f} - ${phase_config.max_capital:,.0f}")
    print(f"Duration: {phase_config.duration_days} days")
    print(f"Active Tickers: {', '.join(phase_config.active_tickers)}")
    print(f"Max Concurrent Positions: {phase_config.max_positions}")
    print(f"\nSuccess Metrics:")
    for metric, value in phase_config.success_metrics.items():
        print(f"  {metric}: {value}")
    print(f"\nPosition Allocation:")
    for ticker, alloc in phase_config.get_position_allocation().items():
        print(f"  {ticker}: {alloc['max_allocation_pct']}%")


if __name__ == "__main__":
    # Test configuration
    config = LiveTradingConfig()
    
    # Print all phases
    for phase in [TradingPhase.PHASE_1, TradingPhase.PHASE_2, TradingPhase.PHASE_3]:
        print_config_summary(config, phase)
    
    # Example: Get risk limits
    print("\n" + "="*60)
    print("RISK MANAGEMENT RULES")
    print("="*60)
    print(config.get_daily_loss_limits())
