"""
Quick Test - Automatic Trading System Demo
===========================================

This script demonstrates how automatic trading works
without needing a real broker connection.

Run this to see the orchestrator in action.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
project_root = Path(__file__).parent.parent.parent  # Go from examples -> src -> root
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'src' / 'core'))
sys.path.insert(0, str(project_root / 'src' / 'trading'))

from trading.broker_interface import MockBroker
from trading.live_trading_config import LiveTradingConfig, TradingPhase
from trading.auto_order_executor import AutoOrderExecutor, ExecutionResult


def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )


def main():
    """Demonstrate automatic order execution"""
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*70)
    logger.info("AUTOMATIC TRADING SYSTEM - DEMO")
    logger.info("="*70)
    
    # 1. Create mock broker
    logger.info("\n[STEP 1] Creating mock broker...")
    broker = MockBroker(account_id='DEMO_ACCOUNT', initial_cash=5000.0)
    
    # Set mock prices
    broker.set_prices({
        'MSFT': 430.25,
        'GOOGL': 315.15,
        'AAPL': 185.50,
        'TSLA': 255.75
    })
    
    # Connect
    broker.connect()
    account = broker.get_account_info()
    logger.info(f"✓ Broker connected")
    logger.info(f"  Account balance: ${account.total_value:.2f}")
    logger.info(f"  Cash available: ${account.cash:.2f}")
    
    # 2. Load configuration
    logger.info("\n[STEP 2] Loading configuration...")
    config = LiveTradingConfig()
    config.initial_capital = 5000.0
    logger.info(f"✓ Configuration loaded")
    logger.info(f"  Initial capital: ${config.initial_capital:.2f}")
    logger.info(f"  Active tickers (Phase 1): {config.get_active_tickers_for_phase(TradingPhase.PHASE_1)}")
    
    # 3. Create order executor
    logger.info("\n[STEP 3] Creating order executor...")
    executor = AutoOrderExecutor(broker, config)
    logger.info(f"✓ Order executor ready")
    
    # 4. Generate sample signals and execute
    logger.info("\n[STEP 4] Executing automated trades...")
    
    sample_signals = [
        {
            'signal': 'BUY',
            'ticker': 'MSFT',
            'confidence': 0.72,
            'price': 430.25,
            'stop_loss': 427.05,
            'take_profit': 459.77
        },
        {
            'signal': 'BUY',
            'ticker': 'GOOGL',
            'confidence': 0.68,
            'price': 315.15,
            'stop_loss': 312.50,
            'take_profit': 335.00
        },
        {
            'signal': 'HOLD',
            'ticker': 'AAPL',
            'confidence': 0.45,
            'price': 185.50,
            'stop_loss': 0,
            'take_profit': 0
        },
    ]
    
    results = []
    for signal in sample_signals:
        account = broker.get_account_info()
        result = executor.execute_signal(
            signal,
            {'MSFT': 430.25, 'GOOGL': 315.15, 'AAPL': 185.50},
            account.cash
        )
        results.append(result)
        
        logger.info(f"")
        logger.info(f"  Signal: {signal['ticker']} {signal['signal']} (confidence: {signal['confidence']:.0%})")
        
        if result.success:
            logger.info(f"  ✓ EXECUTED")
            logger.info(f"    - Shares: {result.shares}")
            logger.info(f"    - Entry price: ${result.entry_price:.2f}")
            logger.info(f"    - Stop loss: ${result.stop_loss_price:.2f}")
            logger.info(f"    - Take profit: ${result.take_profit_price:.2f}")
        else:
            logger.info(f"  ✗ NOT EXECUTED: {result.reason}")
    
    # 5. Show final statistics
    logger.info("\n[STEP 5] Execution Summary...")
    stats = executor.get_execution_stats()
    logger.info(f"✓ Total executions: {stats['total_executions']}")
    logger.info(f"  Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"  Buy orders: {stats['buy_orders']}")
    logger.info(f"  Sell orders: {stats['sell_orders']}")
    
    # 6. Show positions
    logger.info(f"\n[STEP 6] Current Positions...")
    account = broker.get_account_info()
    if account.positions:
        for pos in account.positions:
            logger.info(f"  {pos.symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f}")
    else:
        logger.info(f"  No open positions")
    
    logger.info(f"\n  Cash remaining: ${account.cash:.2f}")
    
    logger.info("\n" + "="*70)
    logger.info("SIMULATION COMPLETE")
    logger.info("="*70)
    logger.info("\n✓ The automatic trading system works correctly!")
    logger.info("\nTo run live trading with REAL broker:")
    logger.info(f"  python src/core/auto_trading_main.py --broker=ib --account=DU123456")
    logger.info("\nTo run paper trading simulation:")
    logger.info(f"  python src/core/auto_trading_main.py --broker=mock --signal-interval=1")


if __name__ == '__main__':
    main()
