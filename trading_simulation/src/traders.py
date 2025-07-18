"""Trader implementations for stock trading simulation."""

import random
import numpy as np
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from .order_book import Order, OrderSide, OrderType


@dataclass
class TraderConfig:
    """Configuration for trader behavior."""
    maker_probability: float = 0.2  # 20% makers, 80% takers
    buy_probability: float = 0.5    # 50% buy, 50% sell
    price_variance: float = 0.01    # ±1% price variance
    
    # Order size distribution
    small_order_probability: float = 0.7   # 70% small orders
    medium_order_probability: float = 0.25 # 25% medium orders
    large_order_probability: float = 0.05  # 5% large orders
    
    small_order_range: tuple = (1, 10)      # 1-10 shares
    medium_order_range: tuple = (11, 100)   # 11-100 shares
    large_order_range: tuple = (101, 1000)  # 101-1000 shares


class RandomTrader:
    """A trader that makes random trading decisions based on mathematical rules."""
    
    def __init__(self, trader_id: str, config: Optional[TraderConfig] = None):
        """Initialize trader with ID and configuration."""
        self.trader_id = trader_id
        self.config = config or TraderConfig()
        self.order_counter = 0
        
        # Initialize random seed for reproducible behavior if needed
        self.random_state = random.Random()
        self.np_random = np.random.RandomState()
    
    def decide_action(self, current_price: float) -> Optional[Order]:
        """Decide whether to place an order and return it if so."""
        # Decide if this trader acts this time step (could add probability here)
        if not self._should_trade():
            return None
        
        # Decide maker vs taker
        is_maker = self.random_state.random() < self.config.maker_probability
        
        # Decide buy vs sell
        is_buy = self.random_state.random() < self.config.buy_probability
        
        # Generate order size
        quantity = self._generate_order_size()
        
        # Generate order price
        price = self._generate_order_price(current_price, is_maker)
        
        # Determine order type
        order_type = OrderType.LIMIT if is_maker else OrderType.MARKET
        
        # Create order
        self.order_counter += 1
        order = Order(
            order_id=f"{self.trader_id}_order_{self.order_counter}",
            trader_id=self.trader_id,
            side=OrderSide.BUY if is_buy else OrderSide.SELL,
            quantity=quantity,
            price=price,
            order_type=order_type
        )
        
        return order
    
    def _should_trade(self) -> bool:
        """Determine if trader should trade this time step."""
        # For now, always trade when called
        # Could add randomness here for more realistic behavior
        return True
    
    def _generate_order_size(self) -> int:
        """Generate order size based on distribution."""
        rand = self.random_state.random()
        
        if rand < self.config.small_order_probability:
            # Small order
            return self.random_state.randint(*self.config.small_order_range)
        elif rand < self.config.small_order_probability + self.config.medium_order_probability:
            # Medium order
            return self.random_state.randint(*self.config.medium_order_range)
        else:
            # Large order
            return self.random_state.randint(*self.config.large_order_range)
    
    def _generate_order_price(self, current_price: float, is_maker: bool) -> float:
        """Generate order price based on current price and trader type."""
        if is_maker:
            # Makers place limit orders within ±1% of current price
            variance = self.np_random.uniform(-self.config.price_variance, self.config.price_variance)
            price = current_price * (1 + variance)
        else:
            # Takers use market orders, but we still need a price for reference
            # Market orders will match at the best available price
            price = current_price
        
        # Ensure price is positive and reasonable
        return max(price, 0.01)
    
    def get_stats(self) -> dict:
        """Get trader statistics."""
        return {
            "trader_id": self.trader_id,
            "orders_placed": self.order_counter,
            "config": self.config
        }


class TraderManager:
    """Manages a collection of traders."""
    
    def __init__(self, num_traders: int = 1000, config: Optional[TraderConfig] = None):
        """Initialize trader manager with specified number of traders."""
        self.num_traders = num_traders
        self.config = config or TraderConfig()
        self.traders = []
        
        # Create traders
        for i in range(num_traders):
            trader = RandomTrader(f"trader_{i+1}", self.config)
            self.traders.append(trader)
    
    def get_all_orders(self, current_price: float) -> list[Order]:
        """Get orders from all traders for current time step."""
        orders = []
        
        for trader in self.traders:
            order = trader.decide_action(current_price)
            if order is not None:
                orders.append(order)
        
        return orders
    
    def get_trader_stats(self) -> dict:
        """Get statistics for all traders."""
        stats = {
            "total_traders": len(self.traders),
            "config": self.config,
            "individual_stats": [trader.get_stats() for trader in self.traders[:10]]  # First 10 for brevity
        }
        
        # Aggregate statistics
        total_orders = sum(trader.order_counter for trader in self.traders)
        stats["total_orders_placed"] = total_orders
        stats["average_orders_per_trader"] = total_orders / len(self.traders) if self.traders else 0
        
        return stats
    
    def reset_traders(self):
        """Reset all trader counters."""
        for trader in self.traders:
            trader.order_counter = 0