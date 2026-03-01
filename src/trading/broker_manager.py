"""
Unified Broker Integration Module
ÉTAPE 16: Seamless broker switching and initialization
"""

import logging
from typing import Optional
from trading.broker_interface import BrokerInterface, MockBroker
from trading.interactive_brokers import InteractiveBrokersConnector


logger = logging.getLogger(__name__)


class BrokerManager:
    """
    Manages broker connections and provides factory methods
    Supports seamless switching between different broker types
    """
    
    SUPPORTED_BROKERS = {
        'mock': 'MockBroker',
        'interactive_brokers': 'InteractiveBrokersConnector',
        'ib': 'InteractiveBrokersConnector',
    }
    
    def __init__(self):
        """Initialize broker manager"""
        self.brokers: dict = {}
        self.active_broker: Optional[BrokerInterface] = None
    
    @staticmethod
    def create_broker(
        broker_type: str,
        account_id: str,
        **kwargs
    ) -> Optional[BrokerInterface]:
        """
        Factory method to create broker instance
        
        Args:
            broker_type: 'mock', 'interactive_brokers', or 'ib'
            account_id: Account ID for the broker
            **kwargs: Additional arguments for broker initialization
        
        Returns:
            BrokerInterface instance or None if failed
        """
        
        broker_type_lower = broker_type.lower()
        
        if broker_type_lower == 'mock':
            logger.info(f"Creating Mock Broker for account {account_id}")
            initial_cash = kwargs.get('initial_cash', 100000.0)
            return MockBroker(account_id, initial_cash)
        
        elif broker_type_lower in ['interactive_brokers', 'ib']:
            logger.info(f"Creating Interactive Brokers connector for account {account_id}")
            port = kwargs.get('port', 7498)
            client_id = kwargs.get('client_id', 1)
            
            try:
                import ibapi  # Check if ibapi is installed
                return InteractiveBrokersConnector(account_id, port, client_id)
            except ImportError:
                logger.error("ibapi not installed. Install with: pip install ibapi")
                return None
        
        else:
            logger.error(f"Unknown broker type: {broker_type}")
            return None
    
    def initialize_broker(
        self,
        broker_type: str,
        account_id: str,
        **kwargs
    ) -> bool:
        """
        Initialize and activate a broker connection
        
        Args:
            broker_type: Type of broker
            account_id: Account ID
            **kwargs: Additional broker-specific arguments
        
        Returns:
            True if successful, False otherwise
        """
        
        # Create broker instance
        broker = self.create_broker(broker_type, account_id, **kwargs)
        
        if broker is None:
            logger.error(f"Failed to create broker: {broker_type}")
            return False
        
        # Connect broker
        if not broker.connect():
            logger.error(f"Failed to connect broker: {broker_type}")
            return False
        
        # Validate connection
        if not broker.validate_connection():
            logger.error(f"Connection validation failed for: {broker_type}")
            broker.disconnect()
            return False
        
        # Store and activate
        self.brokers[broker_type] = broker
        self.active_broker = broker
        
        logger.info(f"✓ Broker initialized and activated: {broker_type}")
        return True
    
    def get_broker(self, broker_type: str = None) -> Optional[BrokerInterface]:
        """
        Get broker instance
        
        Args:
            broker_type: Broker type key, or None for active broker
        
        Returns:
            BrokerInterface instance or None
        """
        
        if broker_type is None:
            return self.active_broker
        
        return self.brokers.get(broker_type)
    
    def switch_broker(self, broker_type: str) -> bool:
        """
        Switch to a different broker
        
        Args:
            broker_type: Broker type key
        
        Returns:
            True if successful
        """
        
        if broker_type not in self.brokers:
            logger.error(f"Broker not initialized: {broker_type}")
            return False
        
        self.active_broker = self.brokers[broker_type]
        logger.info(f"Switched to broker: {broker_type}")
        return True
    
    def disconnect_broker(self, broker_type: str = None):
        """
        Disconnect broker
        
        Args:
            broker_type: Broker type, or None for active broker
        """
        
        if broker_type is None:
            if self.active_broker:
                self.active_broker.disconnect()
                self.active_broker = None
        else:
            if broker_type in self.brokers:
                self.brokers[broker_type].disconnect()
                del self.brokers[broker_type]
    
    def disconnect_all(self):
        """Disconnect all brokers"""
        for broker in self.brokers.values():
            broker.disconnect()
        self.brokers.clear()
        self.active_broker = None
        logger.info("All brokers disconnected")


class BrokerFactory:
    """
    Convenience factory for common broker initialization patterns
    """
    
    @staticmethod
    def create_mock_broker(
        account_id: str = "MOCK_ACCOUNT",
        initial_cash: float = 100000.0
    ) -> MockBroker:
        """Create and connect mock broker for testing"""
        broker = MockBroker(account_id, initial_cash)
        broker.connect()
        return broker
    
    @staticmethod
    def create_paper_trading_broker(
        account_id: str,
        client_id: int = 1
    ) -> Optional[InteractiveBrokersConnector]:
        """
        Create and connect to IB paper trading
        
        Uses port 7498 (paper trading port)
        """
        broker = InteractiveBrokersConnector(account_id, port=7498, client_id=client_id)
        if broker.connect():
            return broker
        return None
    
    @staticmethod
    def create_live_trading_broker(
        account_id: str,
        client_id: int = 1
    ) -> Optional[InteractiveBrokersConnector]:
        """
        Create and connect to IB live trading
        
        ⚠️  USE WITH CAUTION - This is REAL MONEY trading!
        
        Uses port 7497 (live trading port)
        """
        logger.warning("⚠️  LIVE TRADING MODE: This will trade with REAL MONEY!")
        logger.warning(f"⚠️  Account: {account_id}")
        
        broker = InteractiveBrokersConnector(account_id, port=7497, client_id=client_id)
        if broker.connect():
            return broker
        return None


# Global broker manager instance
_global_broker_manager = BrokerManager()


def initialize_broker(
    broker_type: str,
    account_id: str,
    **kwargs
) -> bool:
    """Module-level function to initialize broker"""
    return _global_broker_manager.initialize_broker(broker_type, account_id, **kwargs)


def get_broker(broker_type: str = None) -> Optional[BrokerInterface]:
    """Module-level function to get broker"""
    return _global_broker_manager.get_broker(broker_type)


def disconnect_broker(broker_type: str = None):
    """Module-level function to disconnect broker"""
    _global_broker_manager.disconnect_broker(broker_type)


def disconnect_all():
    """Module-level function to disconnect all brokers"""
    _global_broker_manager.disconnect_all()


# Convenience exports
__all__ = [
    'BrokerManager',
    'BrokerFactory',
    'initialize_broker',
    'get_broker',
    'disconnect_broker',
    'disconnect_all',
]
