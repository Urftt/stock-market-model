"""Main simulation engine for stock trading simulation."""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import polars as pl
import numpy as np

from .order_book import OrderBook, Trade
from .traders import TraderManager, TraderConfig


@dataclass
class CandlestickData:
    """Represents OHLCV candlestick data for a time period."""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    trade_count: int


@dataclass
class SimulationConfig:
    """Configuration for the simulation."""
    initial_price: float = 100.0
    num_traders: int = 1000
    time_step_seconds: float = 0.1  # Faster time steps for quicker trading
    candlestick_interval_seconds: int = 60  # 1-minute candles
    max_history_length: int = 1000  # Keep last 1000 candles
    

class TradingSimulation:
    """Main simulation engine that orchestrates traders and order book."""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        """Initialize the trading simulation."""
        self.config = config or SimulationConfig()
        
        # Initialize components
        self.order_book = OrderBook(initial_price=self.config.initial_price)
        self.trader_manager = TraderManager(
            num_traders=self.config.num_traders,
            config=TraderConfig()
        )
        
        # Simulation state
        self.current_time = datetime.now()
        self.is_running = False
        self.step_count = 0
        
        # Data storage
        self.candlestick_data: List[CandlestickData] = []
        self.current_candle_data = {
            'timestamp': self.current_time,
            'open': self.config.initial_price,
            'high': self.config.initial_price,
            'low': self.config.initial_price,
            'close': self.config.initial_price,
            'volume': 0,
            'trade_count': 0,
            'trades': []
        }
        
        # Performance tracking
        self.performance_stats = {
            'total_trades': 0,
            'total_volume': 0,
            'orders_per_second': 0,
            'trades_per_second': 0
        }
    
    def start(self):
        """Start the simulation."""
        self.is_running = True
        self.current_time = datetime.now()
        print(f"Starting simulation at {self.current_time}")
        print(f"Initial price: ${self.config.initial_price:.2f}")
        print(f"Number of traders: {self.config.num_traders}")
    
    def stop(self):
        """Stop the simulation."""
        self.is_running = False
        print(f"Simulation stopped at step {self.step_count}")
    
    def step(self) -> Dict:
        """Execute one simulation time step."""
        if not self.is_running:
            return {}
        
        step_start_time = time.time()
        self.step_count += 1
        self.current_time += timedelta(seconds=self.config.time_step_seconds)
        
        # Get orders from all traders
        orders = self.trader_manager.get_all_orders(self.order_book.current_price)
        
        # Process orders through order book
        step_trades = []
        for order in orders:
            trades = self.order_book.add_order(order)
            step_trades.extend(trades)
        
        # Update current candle data
        self._update_candle_data(step_trades)
        
        # Check if we need to finalize current candle and start new one
        self._check_candle_completion()
        
        # Update performance stats
        self._update_performance_stats(len(orders), len(step_trades))
        
        # Clean up old data periodically
        if self.step_count % 100 == 0:
            self.order_book.clear_old_trades()
        
        step_end_time = time.time()
        processing_time = step_end_time - step_start_time
        
        # Return step summary
        return {
            'step': self.step_count,
            'timestamp': self.current_time,
            'current_price': self.order_book.current_price,
            'orders_placed': len(orders),
            'trades_executed': len(step_trades),
            'total_volume': sum(trade.quantity for trade in step_trades),
            'best_bid': self.order_book.get_best_bid(),
            'best_ask': self.order_book.get_best_ask(),
            'spread': self.order_book.get_spread(),
            'processing_time_ms': processing_time * 1000
        }
    
    def _update_candle_data(self, trades: List[Trade]):
        """Update current candle with new trade data."""
        if not trades:
            return
        
        for trade in trades:
            # Update OHLC
            if not self.current_candle_data['trades']:  # First trade of candle
                self.current_candle_data['open'] = trade.price
            
            self.current_candle_data['high'] = max(self.current_candle_data['high'], trade.price)
            self.current_candle_data['low'] = min(self.current_candle_data['low'], trade.price)
            self.current_candle_data['close'] = trade.price
            
            # Update volume and trade count
            self.current_candle_data['volume'] += trade.quantity
            self.current_candle_data['trade_count'] += 1
            self.current_candle_data['trades'].append(trade)
    
    def _check_candle_completion(self):
        """Check if current candle should be finalized and new one started."""
        candle_start_time = self.current_candle_data['timestamp']
        elapsed_seconds = (self.current_time - candle_start_time).total_seconds()
        
        if elapsed_seconds >= self.config.candlestick_interval_seconds:
            # Finalize current candle
            candle = CandlestickData(
                timestamp=self.current_candle_data['timestamp'],
                open_price=self.current_candle_data['open'],
                high_price=self.current_candle_data['high'],
                low_price=self.current_candle_data['low'],
                close_price=self.current_candle_data['close'],
                volume=self.current_candle_data['volume'],
                trade_count=self.current_candle_data['trade_count']
            )
            
            self.candlestick_data.append(candle)
            
            # Limit history length
            if len(self.candlestick_data) > self.config.max_history_length:
                self.candlestick_data = self.candlestick_data[-self.config.max_history_length:]
            
            # Start new candle
            self.current_candle_data = {
                'timestamp': self.current_time,
                'open': self.order_book.current_price,
                'high': self.order_book.current_price,
                'low': self.order_book.current_price,
                'close': self.order_book.current_price,
                'volume': 0,
                'trade_count': 0,
                'trades': []
            }
    
    def _update_performance_stats(self, num_orders: int, num_trades: int):
        """Update performance statistics."""
        self.performance_stats['total_trades'] += num_trades
        if num_trades > 0:
            recent_trades = self.order_book.get_recent_trades(num_trades)
            step_volume = sum(trade.quantity for trade in recent_trades)
            self.performance_stats['total_volume'] += step_volume
        
        # Calculate rates (smoothed over last 10 steps)
        if self.step_count > 0:
            self.performance_stats['orders_per_second'] = num_orders / self.config.time_step_seconds
            self.performance_stats['trades_per_second'] = num_trades / self.config.time_step_seconds
    
    def get_candlestick_dataframe(self) -> pl.DataFrame:
        """Get candlestick data as Polars DataFrame."""
        if not self.candlestick_data:
            return pl.DataFrame()
        
        data = {
            'Timestamp': [candle.timestamp for candle in self.candlestick_data],
            'Open': [candle.open_price for candle in self.candlestick_data],
            'High': [candle.high_price for candle in self.candlestick_data],
            'Low': [candle.low_price for candle in self.candlestick_data],
            'Close': [candle.close_price for candle in self.candlestick_data],
            'Volume': [candle.volume for candle in self.candlestick_data],
            'TradeCount': [candle.trade_count for candle in self.candlestick_data]
        }
        
        return pl.DataFrame(data)
    
    def get_current_market_data(self) -> Dict:
        """Get current market state for visualization."""
        bids, asks = self.order_book.get_order_book_depth(levels=10)
        recent_trades = self.order_book.get_recent_trades(count=20)
        
        return {
            'current_price': self.order_book.current_price,
            'timestamp': self.current_time,
            'best_bid': self.order_book.get_best_bid(),
            'best_ask': self.order_book.get_best_ask(),
            'spread': self.order_book.get_spread(),
            'bids': bids,
            'asks': asks,
            'recent_trades': [
                {
                    'price': trade.price,
                    'quantity': trade.quantity,
                    'timestamp': trade.timestamp
                } for trade in recent_trades
            ],
            'current_candle': self.current_candle_data,
            'performance': self.performance_stats
        }
    
    def get_simulation_stats(self) -> Dict:
        """Get comprehensive simulation statistics."""
        trader_stats = self.trader_manager.get_trader_stats()
        df = self.get_candlestick_dataframe()
        
        stats = {
            'simulation': {
                'step_count': self.step_count,
                'current_time': self.current_time,
                'is_running': self.is_running,
                'current_price': self.order_book.current_price
            },
            'trading': {
                'total_candles': len(self.candlestick_data),
                'total_trades': len(self.order_book.trades),
                'performance': self.performance_stats
            },
            'traders': trader_stats,
            'market_data': {
                'price_range': {
                    'min': float(df['Low'].min()) if len(df) > 0 else self.config.initial_price,
                    'max': float(df['High'].max()) if len(df) > 0 else self.config.initial_price
                },
                'total_volume': int(df['Volume'].sum()) if len(df) > 0 else 0
            }
        }
        
        return stats
    
    def reset(self):
        """Reset the simulation to initial state."""
        self.order_book = OrderBook(initial_price=self.config.initial_price)
        self.trader_manager.reset_traders()
        self.current_time = datetime.now()
        self.is_running = False
        self.step_count = 0
        self.candlestick_data = []
        self.current_candle_data = {
            'timestamp': self.current_time,
            'open': self.config.initial_price,
            'high': self.config.initial_price,
            'low': self.config.initial_price,
            'close': self.config.initial_price,
            'volume': 0,
            'trade_count': 0,
            'trades': []
        }
        self.performance_stats = {
            'total_trades': 0,
            'total_volume': 0,
            'orders_per_second': 0,
            'trades_per_second': 0
        }
        print("Simulation reset to initial state")