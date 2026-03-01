"""
Interactive Brokers API Integration
ÉTAPE 16: Broker API Implementation
Requires: pip install ibapi
"""

from .broker_interface import (
    BrokerInterface, OrderData, Position, Account, 
    OrderType, OrderStatus, OrderSide
)
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import time


logger = logging.getLogger(__name__)


class InteractiveBrokersConnector(BrokerInterface):
    """
    Interactive Brokers TWS API integration
    
    Setup required:
    1. Download TWS (Trader Workstation) from IBKR website
    2. Install ibapi: pip install ibapi
    3. Configure TWS API settings:
       - Settings -> API -> Enable ActiveX and Socket Clients
       - Settings -> API -> Socket Port: 7497 (live) or 7498 (paper)
    4. Set account_id to your IB account number
    
    Paper Trading Setup:
    - Login to IB Account Management
    - Select Paper Trading account
    - Run TWS with paper account
    - Connect via port 7498
    """
    
    def __init__(self, account_id: str, port: int = 7498, client_id: int = 1):
        """
        Initialize Interactive Brokers connector
        
        Args:
            account_id: IB Account ID (e.g., 'DU123456')
            port: Socket port (7497=live, 7498=paper/simulator)
            client_id: Client ID for API connection
        """
        super().__init__(account_id)
        self.port = port
        self.client_id = client_id
        self.host = "127.0.0.1"
        
        # These will be set after ibapi is imported
        self.ib_client = None
        self.ib_wrapper = None
        
        # Price cache
        self.price_cache: Dict[str, float] = {}
        self.last_price_update = {}
        
        logger.info(f"Interactive Brokers connector initialized for {account_id}")
    
    def connect(self) -> bool:
        """Connect to Interactive Brokers TWS API"""
        try:
            from ibapi.client import EClient
            from ibapi.wrapper import EWrapper
            from ibapi.contract import Contract
            from ibapi.common import TickAttrib
            import threading
            
            # Define wrapper class
            class IBWrapper(EWrapper):
                def __init__(self, connector):
                    super().__init__()
                    self.connector = connector
                
                def nextValidId(self, order_id):
                    self.connector.next_order_id = order_id
                
                def tickPrice(self, req_id, tick_type, price, attrib: TickAttrib):
                    if tick_type == 4:  # LAST price
                        symbol = self.connector.req_to_symbol.get(req_id)
                        if symbol:
                            self.connector.price_cache[symbol] = price
                            self.connector.last_price_update[symbol] = datetime.now()
                
                def orderStatus(self, order_id, status, filled, remaining, avg_fill_price, 
                               perm_id, parent_id, last_fill_price, client_id, why_held, mkt_cap_price):
                    if order_id in self.connector.orders:
                        order = self.connector.orders[order_id]
                        if status == "Filled":
                            order.status = OrderStatus.FILLED
                            order.filled_quantity = filled
                            order.filled_price = avg_fill_price
                        elif status == "PartiallyFilled":
                            order.status = OrderStatus.PARTIALLY_FILLED
                            order.filled_quantity = filled
                        elif status == "Cancelled":
                            order.status = OrderStatus.CANCELLED
                        elif status == "Rejected":
                            order.status = OrderStatus.REJECTED
                
                def accountSummary(self, req_id, account, tag, value, currency):
                    self.connector.account_summary[tag] = {
                        'value': value,
                        'currency': currency
                    }
                
                def error(self, req_id, error_code, error_string):
                    logger.error(f"IB API Error {error_code}: {error_string}")
            
            # Define client class
            class IBClient(EClient):
                def __init__(self, wrapper):
                    super().__init__(wrapper)
            
            self.ib_wrapper = IBWrapper(self)
            self.ib_client = IBClient(self.ib_wrapper)
            
            # Connect to TWS
            self.ib_client.connect(self.host, self.port, self.client_id)
            
            # Start reader thread
            reader_thread = threading.Thread(target=self.ib_client.run)
            reader_thread.daemon = True
            reader_thread.start()
            
            # Wait for connection
            time.sleep(2)
            
            if self.ib_client.isConnected():
                self.is_connected = True
                logger.info(f"Connected to IB API on {self.host}:{self.port}")
                return True
            else:
                logger.error("Failed to connect to IB API")
                return False
        
        except ImportError:
            logger.error("ibapi not installed. Run: pip install ibapi")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Interactive Brokers"""
        try:
            if self.ib_client and self.ib_client.isConnected():
                self.ib_client.disconnect()
                self.is_connected = False
                logger.info("Disconnected from IB API")
                return True
        except Exception as e:
            logger.error(f"Disconnection error: {e}")
        return False
    
    def is_market_open(self) -> bool:
        """Check if US stock market is currently open"""
        from datetime import datetime
        import pytz
        
        try:
            # Use US Eastern time
            eastern = pytz.timezone('America/New_York')
            now = datetime.now(eastern)
            
            # Market hours: 9:30 AM - 4:00 PM, Mon-Fri
            is_weekday = now.weekday() < 5
            is_trading_hours = 9.5 <= now.hour + now.minute/60 < 16.0
            
            return is_weekday and is_trading_hours
        except:
            return True  # Assume open if can't determine
    
    def get_account_info(self) -> Account:
        """Get account information from Interactive Brokers"""
        try:
            if not self.is_connected:
                return None
            
            # Request account summary
            self.account_summary = {}
            self.ib_client.reqAccountSummary(
                req_id=9999,
                group_name="All",
                tags="NetLiquidation,TotalCashValue,BuyingPower"
            )
            
            time.sleep(1)  # Wait for response
            
            # Parse response
            total_val = float(self.account_summary.get('NetLiquidation', {}).get('value', '0'))
            cash = float(self.account_summary.get('TotalCashValue', {}).get('value', '0'))
            buying_power = float(self.account_summary.get('BuyingPower', {}).get('value', '0'))
            
            positions = self.get_positions()
            
            return Account(
                cash=cash,
                total_value=total_val,
                buying_power=buying_power,
                leverage=total_val / cash if cash > 0 else 1.0,
                positions=positions
            )
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_positions(self) -> List[Position]:
        """Get current positions from Interactive Brokers"""
        try:
            # This would require implementing portfolio request
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get specific position"""
        positions = self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            from ibapi.contract import Contract
            
            # Check cache first
            if symbol in self.price_cache:
                # Refresh if older than 5 seconds
                last_update = self.last_price_update.get(symbol, datetime.now())
                if (datetime.now() - last_update).seconds < 5:
                    return self.price_cache[symbol]
            
            # Request realtime price
            req_id = hash(symbol) % 10000
            self.req_to_symbol = getattr(self, 'req_to_symbol', {})
            self.req_to_symbol[req_id] = symbol
            
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            
            self.ib_client.reqMktData(req_id, contract, "", False, False, [])
            
            # Wait briefly for price
            time.sleep(0.5)
            
            return self.price_cache.get(symbol, 0.0)
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0
    
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        prices = {}
        for symbol in symbols:
            prices[symbol] = self.get_price(symbol)
        return prices
    
    def place_order(self, order: OrderData) -> str:
        """Place order with Interactive Brokers"""
        try:
            from ibapi.contract import Contract
            from ibapi.order import Order
            
            if not self.is_connected:
                logger.error("Not connected to IB API")
                return ""
            
            # Create contract
            contract = Contract()
            contract.symbol = order.symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            
            # Create order
            ib_order = Order()
            ib_order.action = "BUY" if order.side == OrderSide.BUY else "SELL"
            ib_order.totalQuantity = int(order.quantity)
            
            # Set order type
            if order.order_type == OrderType.MARKET:
                ib_order.orderType = "MKT"
            elif order.order_type == OrderType.LIMIT:
                ib_order.orderType = "LMT"
                ib_order.lmtPrice = order.limit_price
            elif order.order_type == OrderType.STOP:
                ib_order.orderType = "STP"
                ib_order.auxPrice = order.stop_price
            
            ib_order.eTradeOnly = False
            ib_order.goodAfterTime = ""
            
            # Place order
            order_id = self.next_order_id
            self.next_order_id += 1
            
            self.orders = getattr(self, 'orders', {})
            self.orders[order_id] = order
            
            self.ib_client.placeOrder(order_id, contract, ib_order)
            logger.info(f"Order placed: {order.symbol} {order.side.value} {order.quantity} @ order_id={order_id}")
            
            return str(order_id)
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return ""
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order with Interactive Brokers"""
        try:
            self.ib_client.cancelOrder(int(order_id))
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Tuple[OrderStatus, float]:
        """Get order status from Interactive Brokers"""
        try:
            if int(order_id) in self.orders:
                order = self.orders[int(order_id)]
                return (order.status, order.filled_quantity)
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
        return (OrderStatus.REJECTED, 0.0)
    
    def close_position(self, symbol: str, quantity: float) -> str:
        """Close position on Interactive Brokers"""
        order = OrderData(
            order_id="",
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=OrderType.MARKET
        )
        return self.place_order(order)
    
    def get_order_history(self, limit: int = 100) -> List[OrderData]:
        """Get order history"""
        return self.order_history[-limit:]
    
    def validate_connection(self) -> bool:
        """Validate connection to Interactive Brokers"""
        try:
            return self.ib_client.isConnected() if self.ib_client else False
        except:
            return False
