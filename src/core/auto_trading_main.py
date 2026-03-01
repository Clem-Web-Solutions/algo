"""
Automatic Live Trading Main Entry Point - ÉTAPE 26
==================================================

Launch fully automated trading with:
- Signal generation every N minutes
- Automatic order execution
- Real-time position monitoring
- Risk management enforcement
- Daily reporting

Usage:
    python src/core/auto_trading_main.py --phase=phase_1 --broker=mock
    python src/core/auto_trading_main.py --phase=phase_1 --broker=ib --account=DU123456
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src' / 'core'))
sys.path.insert(0, str(project_root / 'src' / 'trading'))
sys.path.insert(0, str(project_root / 'src' / 'strategies'))
sys.path.insert(0, str(project_root / 'src'))

from error_handler import setup_logger
from trading.broker_manager import BrokerManager
from trading.live_trading_config import LiveTradingConfig, TradingPhase
from trading.trading_orchestrator import TradingOrchestrator


def setup_logging():
    """Setup logging configuration"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    logger = logging.getLogger('auto_trading')
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(log_dir / f'auto_trading_{timestamp}.log')
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


def validate_requirements():
    """Validate that system is ready for live trading"""
    
    logger = logging.getLogger('auto_trading')
    logger.info("Validating system requirements...")
    
    # Check required packages
    try:
        import schedule
        logger.info("✓ schedule package installed")
    except ImportError:
        logger.error("✗ schedule not installed. Install with: pip install schedule")
        return False
    
    # Check broker API package if needed
    try:
        import ibapi
        logger.info("✓ ibapi package installed (Interactive Brokers)")
    except ImportError:
        logger.warning("⚠ ibapi not installed. Paper/Mock trading only.")
    
    # Check models
    models_dir = project_root / 'models'
    models = list(models_dir.glob('model_*.pkl'))
    
    if not models:
        logger.error("✗ No trained models found in models/ directory")
        logger.error("  Run training first: python src/core/production_main.py")
        return False
    
    logger.info(f"✓ Found {len(models)} trained models")
    
    # Check data
    data_dir = project_root / 'data'
    data_files = list(data_dir.glob('*.csv'))
    
    if not data_files:
        logger.error("✗ No data files found in data/ directory")
        return False
    
    logger.info(f"✓ Found {len(data_files)} data files")
    
    return True


def main():
    """Main entry point"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Automated Live Trading with ML Signals'
    )
    parser.add_argument(
        '--phase',
        type=str,
        default='phase_1',
        choices=['phase_1', 'phase_2', 'phase_3'],
        help='Trading phase (phase_1, phase_2, phase_3)'
    )
    parser.add_argument(
        '--broker',
        type=str,
        default='mock',
        choices=['mock', 'ib', 'interactive_brokers'],
        help='Broker type (mock, ib, interactive_brokers)'
    )
    parser.add_argument(
        '--account',
        type=str,
        default='DEMO_ACCOUNT',
        help='Broker account ID (e.g., DU123456 for IB)'
    )
    parser.add_argument(
        '--signal-interval',
        type=int,
        default=60,
        help='Signal generation interval in minutes (default: 60)'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=5000.0,
        help='Starting capital for paper trading (default: 5000)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=7498,
        help='IB API port (7497=live, 7498=paper, default: 7498)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (show what would execute but do not trade)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("="*70)
    logger.info("AUTOMATED LIVE TRADING SYSTEM - ÉTAPE 26")
    logger.info("="*70)
    logger.info(f"Phase: {args.phase}")
    logger.info(f"Broker: {args.broker}")
    logger.info(f"Account: {args.account}")
    logger.info(f"Capital: ${args.capital:.2f}")
    logger.info(f"Signal interval: {args.signal_interval} minutes")
    
    # Validate requirements
    if not validate_requirements():
        logger.error("System validation failed. Cannot continue.")
        return 1
    
    logger.info("System validation passed ✓")
    
    # Load configuration
    logger.info("\nLoading configuration...")
    config = LiveTradingConfig()
    config.initial_capital = args.capital
    logger.info(f"Initial capital: ${config.initial_capital:.2f}")
    
    # Map phase
    phase_map = {
        'phase_1': TradingPhase.PHASE_1,
        'phase_2': TradingPhase.PHASE_2,
        'phase_3': TradingPhase.PHASE_3,
    }
    phase = phase_map.get(args.phase, TradingPhase.PHASE_1)
    active_tickers = config.get_active_tickers_for_phase(phase)
    logger.info(f"Active tickers: {', '.join(active_tickers)}")
    
    # Initialize broker
    logger.info(f"\nInitializing broker: {args.broker}...")
    broker_manager = BrokerManager()
    
    broker = broker_manager.create_broker(
        broker_type=args.broker,
        account_id=args.account,
        initial_cash=args.capital,
        port=args.port,
        client_id=1
    )
    
    if broker is None:
        logger.error("Failed to create broker connection")
        return 1
    
    # Connect broker
    logger.info("Connecting to broker...")
    if not broker.connect():
        logger.error("Failed to connect to broker")
        return 1
    
    logger.info("✓ Broker connected successfully")
    
    # Get account info
    try:
        account = broker.get_account_info()
        logger.info(f"Account balance: ${account.total_value:.2f}")
        logger.info(f"Available cash: ${account.cash:.2f}")
    except Exception as e:
        logger.warning(f"Could not fetch account info: {e}")
    
    # Initialize orchestrator
    logger.info(f"\nInitializing trading orchestrator ({phase.value})...")
    orchestra = TradingOrchestrator(
        broker=broker,
        config=config,
        phase=phase,
        signal_interval_minutes=args.signal_interval
    )
    
    logger.info("✓ Orchestrator initialized")
    
    # Show ready message
    logger.info("\n" + "="*70)
    logger.info("SYSTEM READY FOR LIVE TRADING")
    logger.info("="*70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    logger.info("💡 Tips:")
    logger.info("  - Monitor logs in: logs/")
    logger.info("  - Check positions every 15 minutes")
    logger.info("  - Daily reports saved to: reports/")
    logger.info("  - Press Ctrl+C to stop trading gracefully")
    logger.info("")
    
    # Start trading
    try:
        logger.info("[STARTING AUTOMATED TRADING...]")
        orchestra.start_live_trading()
    
    except KeyboardInterrupt:
        logger.info("\nTrading stopped by user")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        if broker.is_connected:
            broker.disconnect()
            logger.info("✓ Broker disconnected")
    
    logger.info("="*70)
    logger.info("TRADING SESSION ENDED")
    logger.info("="*70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
