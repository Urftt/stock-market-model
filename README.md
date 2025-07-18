# Stock Pattern Simulation

A real-time stock market simulation that demonstrates how realistic trading patterns emerge from simple mathematical rules.

## Overview

This project creates a simulated trading environment where 1000 random traders interact through an order book system. Despite the completely random nature of individual trading decisions, the simulation produces realistic stock market patterns including support/resistance levels, candlestick formations, and price movements that visually resemble real market data.

## Key Features

- **Real-time Visualization**: Interactive candlestick charts with Plotly
- **Order Book Mechanics**: Realistic maker/taker dynamics
- **Speed Control**: Adjustable simulation speed (1x to 10x)
- **Market Patterns**: Natural emergence of support/resistance levels
- **1000 Traders**: Each making random decisions every second

## Mathematical Foundation

The simulation is based on simple rules:
- 80% of traders are "takers" (execute against existing orders)
- 20% of traders are "makers" (place orders in the book)
- All orders placed within ±1% of current price
- Order sizes follow realistic distribution (mostly small, some large)
- 50/50 buy/sell probability for each trader

## Installation

This project uses [UV](https://docs.astral.sh/uv/) as the package manager.

```bash
# Clone the repository
git clone <repository-url>
cd stock-market-model

# Install dependencies
uv install

# Run the simulation
uv run python main.py
```

## Project Structure

```
trading_simulation/
├── src/
│   ├── order_book.py      # Order book mechanics and trade matching
│   ├── traders.py         # Trader behavior and decision logic
│   ├── simulation.py      # Main simulation engine
│   └── visualization.py   # Real-time Plotly charts
├── main.py                # Application entry point
├── pyproject.toml         # UV configuration and dependencies
├── CLAUDE.md              # Development context and commands
└── README.md              # This file
```

## How It Works

1. **Initialization**: Start with 1000 traders and an initial stock price
2. **Time Steps**: Every second, each trader makes a decision
3. **Order Placement**: Traders place buy/sell orders within ±1% of current price
4. **Trade Execution**: Takers execute against makers in the order book
5. **Price Discovery**: Price updates based on executed trades
6. **Visualization**: Real-time candlestick chart updates

## Expected Outcomes

The simulation demonstrates that:
- Random trading can produce realistic market patterns
- Support and resistance levels emerge naturally
- Candlestick formations appear without being programmed
- Price movements look similar to real stock charts
- Volume patterns follow realistic distributions

## Development

```bash
# Format code
uv run black src/ main.py

# Lint code
uv run ruff check src/ main.py

# Run tests (when implemented)
uv run pytest
```

## Technical Details

- **Data Processing**: Polars for efficient data manipulation
- **Visualization**: Plotly for interactive real-time charts
- **Architecture**: Clean OOP design with separated concerns
- **Performance**: Optimized for real-time simulation of 1000 traders

## Contributing

This project follows PEP8 standards and uses:
- PascalCase for DataFrame column names
- Clear separation of concerns between classes
- Proper error handling and documentation

## License

[Add license information here]