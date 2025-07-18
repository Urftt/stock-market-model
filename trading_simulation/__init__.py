"""Stock Pattern Simulation Package."""

from .src.order_book import OrderBook, Order, Trade, OrderSide, OrderType
from .src.traders import RandomTrader, TraderManager, TraderConfig
from .src.simulation import TradingSimulation, SimulationConfig, CandlestickData
from .src.visualization import SimulationVisualizer

__version__ = "0.1.0"
__all__ = [
    "OrderBook", "Order", "Trade", "OrderSide", "OrderType",
    "RandomTrader", "TraderManager", "TraderConfig", 
    "TradingSimulation", "SimulationConfig", "CandlestickData",
    "SimulationVisualizer"
]