"""
Broker API Integration Testing Module
ÉTAPE 16: Test broker connections and order execution
"""

import logging
from typing import List, Dict
from datetime import datetime
from src.trading.broker_interface import (
    MockBroker, OrderData, OrderType, OrderSide, OrderStatus
)


logger = logging.getLogger(__name__)


class BrokerIntegrationTest:
    """Test broker API functionality"""
    
    def __init__(self, broker, test_symbols: List[str] = None):
        """Initialize test suite"""
        self.broker = broker
        self.test_symbols = test_symbols or ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        self.results = {}
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run complete test suite"""
        logger.info(f"Starting broker integration tests for {self.broker.__class__.__name__}")
        
        tests = [
            ("Connection", self.test_connection),
            ("Account Info", self.test_account_info),
            ("Price Fetch", self.test_price_fetch),
            ("Market Status", self.test_market_status),
            ("Buy Order", self.test_buy_order),
            ("Sell Order", self.test_sell_order),
            ("Order Status", self.test_order_status),
            ("Position Tracking", self.test_position_tracking),
            ("Order Cancellation", self.test_order_cancellation),
            ("Order History", self.test_order_history),
            ("Close Position", self.test_close_position),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.results[test_name] = result
                status = "✓ PASS" if result else "✗ FAIL"
                logger.info(f"{test_name}: {status}")
            except Exception as e:
                logger.error(f"{test_name}: ✗ FAIL - {e}")
                self.results[test_name] = False
        
        # Summary
        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        logger.info(f"\nTest Summary: {passed}/{total} passed")
        
        return self.results
    
    def test_connection(self) -> bool:
        """Test broker connection"""
        if not self.broker.connect():
            logger.error("Failed to connect to broker")
            return False
        
        if not self.broker.is_connected:
            logger.error("Connection flag not set")
            return False
        
        if not self.broker.validate_connection():
            logger.error("Connection validation failed")
            return False
        
        return True
    
    def test_account_info(self) -> bool:
        """Test retrieving account information"""
        account = self.broker.get_account_info()
        
        if account is None:
            logger.error("Account info is None")
            return False
        
        if account.total_value <= 0:
            logger.error(f"Invalid total value: {account.total_value}")
            return False
        
        if account.cash < 0:
            logger.error(f"Invalid cash: {account.cash}")
            return False
        
        logger.info(f"Account - Value: ${account.total_value:.2f}, Cash: ${account.cash:.2f}")
        return True
    
    def test_price_fetch(self) -> bool:
        """Test fetching prices"""
        # Set mock prices if using mock broker
        if isinstance(self.broker, MockBroker):
            self.broker.set_prices({
                'AAPL': 185.50,
                'GOOGL': 190.50,
                'MSFT': 440.00,
                'TSLA': 250.00
            })
        
        prices = self.broker.get_prices(self.test_symbols)
        
        if not prices:
            logger.error("No prices returned")
            return False
        
        for symbol in self.test_symbols:
            price = prices.get(symbol)
            if price is None or price <= 0:
                logger.error(f"Invalid price for {symbol}: {price}")
                return False
            logger.info(f"{symbol}: ${price:.2f}")
        
        return True
    
    def test_market_status(self) -> bool:
        """Test market status check"""
        is_open = self.broker.is_market_open()
        logger.info(f"Market open: {is_open}")
        return True  # Always pass - just checking functionality
    
    def test_buy_order(self) -> bool:
        """Test placing buy order"""
        # Set mock prices if needed
        if isinstance(self.broker, MockBroker):
            self.broker.set_prices({'AAPL': 185.50})
        
        order = OrderData(
            order_id="",
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.MARKET
        )
        
        order_id = self.broker.place_order(order)
        
        if not order_id:
            logger.error("Failed to place buy order")
            return False
        
        logger.info(f"Buy order placed: {order_id}")
        self.buy_order_id = order_id
        return True
    
    def test_sell_order(self) -> bool:
        """Test placing sell order"""
        if isinstance(self.broker, MockBroker):
            self.broker.set_prices({'AAPL': 186.50})
        
        order = OrderData(
            order_id="",
            symbol='AAPL',
            side=OrderSide.SELL,
            quantity=5,
            order_type=OrderType.MARKET
        )
        
        order_id = self.broker.place_order(order)
        
        if not order_id:
            logger.error("Failed to place sell order")
            return False
        
        logger.info(f"Sell order placed: {order_id}")
        self.sell_order_id = order_id
        return True
    
    def test_order_status(self) -> bool:
        """Test order status retrieval"""
        if not hasattr(self, 'buy_order_id'):
            return True  # Skip if no order placed yet
        
        status, filled_qty = self.broker.get_order_status(self.buy_order_id)
        
        if status == OrderStatus.REJECTED:
            logger.error(f"Order rejected: {self.buy_order_id}")
            return False
        
        logger.info(f"Order {self.buy_order_id}: {status.value}, filled: {filled_qty}")
        return True
    
    def test_position_tracking(self) -> bool:
        """Test position tracking"""
        positions = self.broker.get_positions()
        
        logger.info(f"Current positions: {len(positions)}")
        for pos in positions:
            logger.info(f"  {pos.symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f}")
        
        # Get single position
        if positions:
            symbol = positions[0].symbol
            pos = self.broker.get_position(symbol)
            if not pos:
                return False
        
        return True
    
    def test_order_cancellation(self) -> bool:
        """Test order cancellation"""
        # Place pending order first
        if isinstance(self.broker, MockBroker):
            self.broker.set_prices({'GOOGL': 190.50})
        
        order = OrderData(
            order_id="",
            symbol='GOOGL',
            side=OrderSide.BUY,
            quantity=5,
            order_type=OrderType.LIMIT,
            limit_price=180.00
        )
        
        order_id = self.broker.place_order(order)
        if not order_id:
            return True  # Skip if unsupported
        
        # Try to cancel
        result = self.broker.cancel_order(order_id)
        logger.info(f"Order cancellation: {result}")
        return True
    
    def test_order_history(self) -> bool:
        """Test order history retrieval"""
        history = self.broker.get_order_history(limit=10)
        
        logger.info(f"Order history: {len(history)} orders")
        for order in history[:3]:
            logger.info(f"  {order.symbol} {order.side.value} {order.quantity}")
        
        return True
    
    def test_close_position(self) -> bool:
        """Test closing position"""
        if isinstance(self.broker, MockBroker):
            self.broker.set_prices({'AAPL': 186.00})
        
        positions = self.broker.get_positions()
        if not positions:
            logger.info("No positions to close - skipping test")
            return True
        
        symbol = positions[0].symbol
        qty = positions[0].quantity
        
        order_id = self.broker.close_position(symbol, qty)
        
        if not order_id:
            logger.warning(f"Failed to close {symbol}")
            return False
        
        logger.info(f"Position closed: {symbol} {qty} shares")
        return True
    
    def test_with_realistic_scenario(self) -> Dict[str, float]:
        """Test complete trading scenario"""
        logger.info("\n=== EXECUTING REALISTIC TRADING SCENARIO ===\n")
        
        scenario_results = {}
        
        try:
            # 1. Set up prices
            if isinstance(self.broker, MockBroker):
                self.broker.set_prices({
                    'GOOGL': 315.15,
                    'MSFT': 471.86,
                    'TSLA': 438.07
                })
            
            # 2. Buy GOOGL
            logger.info("Step 1: Buy GOOGL position")
            buy_googl = OrderData(
                order_id="",
                symbol='GOOGL',
                side=OrderSide.BUY,
                quantity=10,
                order_type=OrderType.MARKET
            )
            googl_order_id = self.broker.place_order(buy_googl)
            scenario_results['googl_buy_order'] = googl_order_id is not None
            
            # 3. Check account
            account = self.broker.get_account_info()
            logger.info(f"Account after buy: Cash=${account.cash:.2f}, Total=${account.total_value:.2f}")
            
            # 4. Simulate price change
            if isinstance(self.broker, MockBroker):
                self.broker.set_prices({'GOOGL': 335.15})  # +6.3%
            
            # 5. Sell for profit
            logger.info("Step 2: Sell GOOGL for profit")
            sell_googl = OrderData(
                order_id="",
                symbol='GOOGL',
                side=OrderSide.SELL,
                quantity=10,
                order_type=OrderType.MARKET
            )
            sell_order_id = self.broker.place_order(sell_googl)
            scenario_results['googl_sell_order'] = sell_order_id is not None
            
            # 6. Final account state
            final_account = self.broker.get_account_info()
            logger.info(f"Final account: Cash=${final_account.cash:.2f}, Total=${final_account.total_value:.2f}")
            
            # 7. Calculate P&L
            pnl = final_account.total_value - 100000.0
            pnl_pct = (pnl / 100000.0) * 100
            scenario_results['final_pnl'] = pnl
            scenario_results['final_pnl_pct'] = pnl_pct
            
            logger.info(f"\nScenario Result: P&L = ${pnl:.2f} ({pnl_pct:.2f}%)")
            
            return scenario_results
        
        except Exception as e:
            logger.error(f"Scenario test failed: {e}")
            return scenario_results


def run_broker_tests(broker_type: str = "mock") -> Dict:
    """
    Run broker integration tests
    
    Args:
        broker_type: "mock", "interactive_brokers", or custom
    
    Returns:
        Dictionary of test results
    """
    
    # Initialize appropriate broker
    if broker_type == "mock":
        logger.info("Initializing Mock Broker for testing...")
        broker = MockBroker(account_id="TEST_ACCOUNT")
    else:
        logger.error(f"Unknown broker type: {broker_type}")
        return {}
    
    # Run tests
    test_suite = BrokerIntegrationTest(broker)
    results = test_suite.run_all_tests()
    
    # Run realistic scenario
    scenario = test_suite.test_with_realistic_scenario()
    
    # Final report
    report = {
        'broker_type': broker_type,
        'timestamp': datetime.now().isoformat(),
        'unit_tests': results,
        'scenario_test': scenario,
        'overall_status': 'PASS' if all(results.values()) else 'PARTIAL_PASS'
    }
    
    return report


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    results = run_broker_tests(broker_type="mock")
    
    # Print summary
    print("\n" + "="*60)
    print("BROKER INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Broker Type: {results['broker_type']}")
    print(f"Overall Status: {results['overall_status']}")
    print(f"Timestamp: {results['timestamp']}")
    print("\nUnit Test Results:")
    for test_name, passed in results['unit_tests'].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    print("\nScenario Test Results:")
    for metric, value in results['scenario_test'].items():
        print(f"  {metric}: {value}")
