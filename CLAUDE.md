# Stock Pattern Simulation Project

## Project Overview
Real-time stock market simulation demonstrating how realistic trading patterns emerge from simple mathematical rules. Based on research showing random trading behavior can reproduce real market patterns.

## Technical Stack
- **Package Manager**: UV
- **Data Manipulation**: Polars
- **Visualization**: Plotly (real-time candlestick charts)
- **Architecture**: Clean OOP with separated responsibilities

## Project Structure
```
trading_simulation/
├── src/
│   ├── order_book.py      # Order book mechanics
│   ├── traders.py         # Trader behavior classes
│   ├── simulation.py      # Main simulation engine
│   └── visualization.py   # Plotly real-time charts
├── main.py                # Entry point
└── pyproject.toml         # UV configuration
```

## Core Mathematical Model

### Price Generation
- Current price: P
- New trader orders: P ± random(0%, 1%)
- Example: If P = $100, orders range from $99.00 to $101.00

### Order Book Mechanics
- **Makers**: Place orders in book (20% of traders)
- **Takers**: Execute against existing orders (80% of traders)
- Price moves when takers execute against makers

### Trader Behavior (1000 traders)
Each trader every second:
1. Decides: Maker vs Taker (20%/80% split)
2. Decides: Buy vs Sell (50/50 probability)
3. Generates order size from distribution
4. Places order at current_price ± random(0%, 1%)

### Order Size Distribution
- 70% small orders (1-10 shares)
- 25% medium orders (11-100 shares)
- 5% large orders (101-1000 shares)

## Key Classes
- **OrderBook**: Manages orders, matches trades, tracks price
- **Trader**: Random behavior following mathematical rules
- **Simulation**: Orchestrates traders, order book, time steps
- **Visualization**: Real-time Plotly candlestick charts

## Features
- Real-time animated candlestick chart
- Speed control slider (1x to 10x)
- Current price, volume, order book depth display
- 1000 traders simulation
- 1-second time intervals
- Natural support/resistance level formation

## Commands
```bash
# Install dependencies
uv install

# Run simulation
uv run python main.py

# Run tests (when available)
uv run pytest

# Format code
uv run black src/ main.py

# Lint code  
uv run ruff check src/ main.py
```

## Development Notes
- Use PascalCase for DataFrame column names
- Follow PEP8 compliance
- Clean separation of concerns
- Proper error handling required
- Generate realistic market patterns through pure mathematics