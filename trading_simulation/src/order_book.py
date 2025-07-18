"""Order book implementation for stock trading simulation."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import polars as pl
from datetime import datetime


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    """Represents a trading order."""
    order_id: str
    trader_id: str
    side: OrderSide
    quantity: int
    price: float
    order_type: OrderType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Trade:
    """Represents an executed trade."""
    trade_id: str
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: int
    timestamp: datetime = field(default_factory=datetime.now)


class OrderBook:
    """Order book for managing and matching trading orders."""
    
    def __init__(self, initial_price: float = 100.0):
        """Initialize order book with initial price."""
        self.current_price = initial_price
        self.buy_orders: Dict[float, List[Order]] = {}
        self.sell_orders: Dict[float, List[Order]] = {}
        self.trades: List[Trade] = []
        self.order_counter = 0
        self.trade_counter = 0
    
    def add_order(self, order: Order) -> List[Trade]:
        """Add order to book and return any resulting trades."""
        if order.order_type == OrderType.MARKET:
            return self._process_market_order(order)
        else:
            return self._process_limit_order(order)
    
    def _process_market_order(self, order: Order) -> List[Trade]:
        """Process a market order by matching against best available prices."""
        trades = []
        remaining_quantity = order.quantity
        
        if order.side == OrderSide.BUY:
            # Match against sell orders (ascending price order)
            sell_prices = sorted(self.sell_orders.keys())
            for price in sell_prices:
                if remaining_quantity <= 0:
                    break
                    
                orders_at_price = self.sell_orders[price]
                while orders_at_price and remaining_quantity > 0:
                    sell_order = orders_at_price[0]
                    trade_quantity = min(remaining_quantity, sell_order.quantity)
                    
                    trade = self._create_trade(order, sell_order, price, trade_quantity)
                    trades.append(trade)
                    
                    remaining_quantity -= trade_quantity
                    sell_order.quantity -= trade_quantity
                    
                    if sell_order.quantity == 0:
                        orders_at_price.pop(0)
                
                if not orders_at_price:
                    del self.sell_orders[price]
        
        else:  # SELL order
            # Match against buy orders (descending price order)
            buy_prices = sorted(self.buy_orders.keys(), reverse=True)
            for price in buy_prices:
                if remaining_quantity <= 0:
                    break
                    
                orders_at_price = self.buy_orders[price]
                while orders_at_price and remaining_quantity > 0:
                    buy_order = orders_at_price[0]
                    trade_quantity = min(remaining_quantity, buy_order.quantity)
                    
                    trade = self._create_trade(buy_order, order, price, trade_quantity)
                    trades.append(trade)
                    
                    remaining_quantity -= trade_quantity
                    buy_order.quantity -= trade_quantity
                    
                    if buy_order.quantity == 0:
                        orders_at_price.pop(0)
                
                if not orders_at_price:
                    del self.buy_orders[price]
        
        # Update current price if trades occurred
        if trades:
            self.current_price = trades[-1].price
        
        return trades
    
    def _process_limit_order(self, order: Order) -> List[Trade]:
        """Process a limit order."""
        trades = []
        remaining_quantity = order.quantity
        
        if order.side == OrderSide.BUY:
            # Check if we can match against existing sell orders
            sell_prices = sorted([p for p in self.sell_orders.keys() if p <= order.price])
            
            for price in sell_prices:
                if remaining_quantity <= 0:
                    break
                    
                orders_at_price = self.sell_orders[price]
                while orders_at_price and remaining_quantity > 0:
                    sell_order = orders_at_price[0]
                    trade_quantity = min(remaining_quantity, sell_order.quantity)
                    
                    trade = self._create_trade(order, sell_order, price, trade_quantity)
                    trades.append(trade)
                    
                    remaining_quantity -= trade_quantity
                    sell_order.quantity -= trade_quantity
                    
                    if sell_order.quantity == 0:
                        orders_at_price.pop(0)
                
                if not orders_at_price:
                    del self.sell_orders[price]
            
            # Add remaining quantity to order book
            if remaining_quantity > 0:
                remaining_order = Order(
                    order_id=order.order_id,
                    trader_id=order.trader_id,
                    side=order.side,
                    quantity=remaining_quantity,
                    price=order.price,
                    order_type=order.order_type,
                    timestamp=order.timestamp
                )
                
                if order.price not in self.buy_orders:
                    self.buy_orders[order.price] = []
                self.buy_orders[order.price].append(remaining_order)
        
        else:  # SELL order
            # Check if we can match against existing buy orders
            buy_prices = sorted([p for p in self.buy_orders.keys() if p >= order.price], reverse=True)
            
            for price in buy_prices:
                if remaining_quantity <= 0:
                    break
                    
                orders_at_price = self.buy_orders[price]
                while orders_at_price and remaining_quantity > 0:
                    buy_order = orders_at_price[0]
                    trade_quantity = min(remaining_quantity, buy_order.quantity)
                    
                    trade = self._create_trade(buy_order, order, price, trade_quantity)
                    trades.append(trade)
                    
                    remaining_quantity -= trade_quantity
                    buy_order.quantity -= trade_quantity
                    
                    if buy_order.quantity == 0:
                        orders_at_price.pop(0)
                
                if not orders_at_price:
                    del self.buy_orders[price]
            
            # Add remaining quantity to order book
            if remaining_quantity > 0:
                remaining_order = Order(
                    order_id=order.order_id,
                    trader_id=order.trader_id,
                    side=order.side,
                    quantity=remaining_quantity,
                    price=order.price,
                    order_type=order.order_type,
                    timestamp=order.timestamp
                )
                
                if order.price not in self.sell_orders:
                    self.sell_orders[order.price] = []
                self.sell_orders[order.price].append(remaining_order)
        
        # Update current price if trades occurred
        if trades:
            self.current_price = trades[-1].price
        
        return trades
    
    def _create_trade(self, buy_order: Order, sell_order: Order, price: float, quantity: int) -> Trade:
        """Create a trade record."""
        self.trade_counter += 1
        trade = Trade(
            trade_id=f"trade_{self.trade_counter}",
            buy_order_id=buy_order.order_id,
            sell_order_id=sell_order.order_id,
            price=price,
            quantity=quantity
        )
        self.trades.append(trade)
        return trade
    
    def get_best_bid(self) -> Optional[float]:
        """Get the highest buy order price."""
        if not self.buy_orders:
            return None
        return max(self.buy_orders.keys())
    
    def get_best_ask(self) -> Optional[float]:
        """Get the lowest sell order price."""
        if not self.sell_orders:
            return None
        return min(self.sell_orders.keys())
    
    def get_spread(self) -> Optional[float]:
        """Get the bid-ask spread."""
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid is None or ask is None:
            return None
        return ask - bid
    
    def get_order_book_depth(self, levels: int = 5) -> Tuple[List[Tuple[float, int]], List[Tuple[float, int]]]:
        """Get order book depth for specified number of levels."""
        # Buy side (bids) - highest prices first
        buy_levels = []
        buy_prices = sorted(self.buy_orders.keys(), reverse=True)[:levels]
        for price in buy_prices:
            total_quantity = sum(order.quantity for order in self.buy_orders[price])
            buy_levels.append((price, total_quantity))
        
        # Sell side (asks) - lowest prices first
        sell_levels = []
        sell_prices = sorted(self.sell_orders.keys())[:levels]
        for price in sell_prices:
            total_quantity = sum(order.quantity for order in self.sell_orders[price])
            sell_levels.append((price, total_quantity))
        
        return buy_levels, sell_levels
    
    def get_recent_trades(self, count: int = 10) -> List[Trade]:
        """Get most recent trades."""
        return self.trades[-count:] if self.trades else []
    
    def clear_old_trades(self, keep_count: int = 1000):
        """Keep only the most recent trades to manage memory."""
        if len(self.trades) > keep_count:
            self.trades = self.trades[-keep_count:]