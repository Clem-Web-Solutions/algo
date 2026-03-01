"""
Abstract Broker Interface - Platform-agnostic broker API abstraction
ÉTAPE 16: Broker API Integration Layer
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class OrderData:
    """Order data structure"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Position:
    """Position data structure"""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float


@dataclass
class Account:
    """Account data structure"""
    cash: float
    total_value: float
    buying_power: float
    leverage: float
    positions: List[Position]


class BrokerInterface(ABC):
    """
    Abstract interface for broker connections
    Implementations: InteractiveBrokers, TD Ameritrade, Alpaca, etc.
    """
    
    def __init__(self, account_id: str):
        """Initialize broker connection"""
        self.account_id = account_id
        self.is_connected = False
        self.order_history: List[OrderData] = []
        
    @abstractmethod
    def connect(self) -> bool:
        """Connect to broker API"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from broker API"""
        pass
    
    @abstractmethod
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Account:
        """Get account information (cash, positions, etc.)"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get specific position"""
        pass
    
    @abstractmethod
    def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        pass
    
    @abstractmethod
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        pass
    
    @abstractmethod
    def place_order(self, order: OrderData) -> str:
        """
        Place order, returns order_id
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Tuple[OrderStatus, float]:
        """
        Get order status and filled quantity
        Returns: (status, filled_qty)
        """
        pass
    
    @abstractmethod
    def close_position(self, symbol: str, quantity: float) -> str:
        """Close position (SELL), returns order_id"""
        pass
    
    @abstractmethod
    def get_order_history(self, limit: int = 100) -> List[OrderData]:
        """Get recent orders"""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate API connection is working"""
        pass


class MockBroker(BrokerInterface):
    """
    Mock broker for testing without real API
    Simulates broker behavior for development and testing
    """
    
    def __init__(self, account_id: str, initial_cash: float = 100000.0):
        """Initialize mock broker"""
        super().__init__(account_id)
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.mock_prices: Dict[str, float] = {}
        self.order_counter = 0
        self.orders: Dict[str, OrderData] = {}
        
    def connect(self) -> bool:
        """Simulate connection"""
        self.is_connected = True
        return True
    
    def disconnect(self) -> bool:
        """Simulate disconnection"""
        self.is_connected = False
        return True
    
    def is_market_open(self) -> bool:
        """Always open in mock"""
        return True
    
    def get_account_info(self) -> Account:
        """Get mock account info"""
        positions = list(self.positions.values())
        total_value = self.cash + sum(p.market_value for p in positions)
        
        return Account(
            cash=self.cash,
            total_value=total_value,
            buying_power=self.cash,
            leverage=1.0,
            positions=positions
        )
    
    def get_positions(self) -> List[Position]:
        """Get mock positions"""
        return list(self.positions.values())
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get mock position"""
        return self.positions.get(symbol)
    
    def get_price(self, symbol: str) -> float:
        """Get mock price"""
        return self.mock_prices.get(symbol, 0.0)
    
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get mock prices"""
        return {s: self.mock_prices.get(s, 0.0) for s in symbols}
    
    def set_prices(self, prices: Dict[str, float]):
        """Set mock prices for testing"""
        self.mock_prices.update(prices)
    
    def place_order(self, order: OrderData) -> str:
        """Place mock order"""
        self.order_counter += 1
        order_id = f"MOCK_{self.account_id}_{self.order_counter}"
        
        # Auto-fill market orders
        if order.order_type == OrderType.MARKET:
            self._execute_order(order, order_id)
        else:
            order.order_id = order_id
            self.orders[order_id] = order
        
        self.order_history.append(order)
        return order_id
    
    def _execute_order(self, order: OrderData, order_id: str):
        """Execute mock order"""
        price = self.mock_prices.get(order.symbol, 100.0)
        cost = order.quantity * price
        
        if order.side == OrderSide.BUY:
            if cost > self.cash:
                order.status = OrderStatus.REJECTED
                return
            self.cash -= cost
            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                total_cost = pos.avg_cost * pos.quantity + cost
                pos.quantity += order.quantity
                pos.avg_cost = total_cost / pos.quantity
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    avg_cost=price,
                    current_price=price,
                    market_value=cost,
                    unrealized_pnl=0.0
                )
        
        elif order.side == OrderSide.SELL:
            if order.symbol not in self.positions:
                order.status = OrderStatus.REJECTED
                return
            pos = self.positions[order.symbol]
            if order.quantity > pos.quantity:
                order.status = OrderStatus.REJECTED
                return
            self.cash += cost
            pos.quantity -= order.quantity
            if pos.quantity == 0:
                del self.positions[order.symbol]
        
        order.order_id = order_id
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = price
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel mock order"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED
            del self.orders[order_id]
            return True
        return False
    
    def get_order_status(self, order_id: str) -> Tuple[OrderStatus, float]:
        """Get mock order status"""
        if order_id in self.orders:
            order = self.orders[order_id]
            return (order.status, order.filled_quantity)
        return (OrderStatus.REJECTED, 0.0)
    
    def close_position(self, symbol: str, quantity: float) -> str:
        """Close mock position"""
        if symbol not in self.positions:
            return ""
        
        order = OrderData(
            order_id="",
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=OrderType.MARKET
        )
        return self.place_order(order)
    
    def get_order_history(self, limit: int = 100) -> List[OrderData]:
        """Get mock order history"""
        return self.order_history[-limit:]
    
    def validate_connection(self) -> bool:
        """Validate mock connection"""
        return self.is_connected
