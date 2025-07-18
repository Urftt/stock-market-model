#!/usr/bin/env python3
"""
Stock Pattern Simulation - Main Entry Point

A real-time stock market simulation demonstrating how realistic trading patterns 
emerge from simple mathematical rules.
"""

import argparse
import sys
from typing import Optional

from trading_simulation import (
    TradingSimulation, 
    SimulationConfig, 
    SimulationVisualizer,
    TraderConfig
)


def create_simulation_config(args) -> SimulationConfig:
    """Create simulation configuration from command line arguments."""
    return SimulationConfig(
        initial_price=args.initial_price,
        num_traders=args.num_traders,
        time_step_seconds=args.time_step,
        candlestick_interval_seconds=args.candle_interval,
        max_history_length=args.max_history
    )


def run_console_simulation(config: SimulationConfig, steps: int = 100):
    """Run simulation in console mode for testing."""
    print("Starting console simulation...")
    print(f"Configuration: {config}")
    
    simulation = TradingSimulation(config)
    simulation.start()
    
    try:
        for i in range(steps):
            step_data = simulation.step()
            
            if i % 10 == 0:  # Print every 10th step
                print(f"Step {step_data['step']}: "
                      f"Price=${step_data['current_price']:.2f}, "
                      f"Orders={step_data['orders_placed']}, "
                      f"Trades={step_data['trades_executed']}, "
                      f"Volume={step_data['total_volume']}")
            
            # Brief pause to make it readable
            import time
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    
    finally:
        simulation.stop()
        stats = simulation.get_simulation_stats()
        print(f"\nFinal Statistics:")
        print(f"Total Steps: {stats['simulation']['step_count']}")
        print(f"Final Price: ${stats['simulation']['current_price']:.2f}")
        print(f"Total Trades: {stats['trading']['total_trades']}")
        print(f"Total Volume: {stats['market_data']['total_volume']:,}")
        print(f"Price Range: ${stats['market_data']['price_range']['min']:.2f} - ${stats['market_data']['price_range']['max']:.2f}")


def run_web_simulation(config: SimulationConfig, host: str = '127.0.0.1', port: int = 8050, debug: bool = False):
    """Run simulation with web interface."""
    print("Starting web-based simulation...")
    
    # Create simulation and visualizer
    simulation = TradingSimulation(config)
    visualizer = SimulationVisualizer(simulation)
    
    # Run the web app
    visualizer.run(debug=debug, host=host, port=port)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Stock Pattern Simulation - Realistic market patterns from random trading",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation parameters
    parser.add_argument('--initial-price', type=float, default=100.0,
                       help='Initial stock price')
    parser.add_argument('--num-traders', type=int, default=1000,
                       help='Number of traders in the simulation')
    parser.add_argument('--time-step', type=float, default=1.0,
                       help='Time step in seconds')
    parser.add_argument('--candle-interval', type=int, default=60,
                       help='Candlestick interval in seconds')
    parser.add_argument('--max-history', type=int, default=1000,
                       help='Maximum number of candlesticks to keep in history')
    
    # Execution mode
    parser.add_argument('--mode', choices=['web', 'console'], default='web',
                       help='Execution mode: web interface or console output')
    parser.add_argument('--steps', type=int, default=100,
                       help='Number of steps to run in console mode')
    
    # Web server options
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Host address for web server')
    parser.add_argument('--port', type=int, default=8050,
                       help='Port for web server')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode for web server')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create configuration
    config = create_simulation_config(args)
    
    try:
        if args.mode == 'console':
            run_console_simulation(config, args.steps)
        else:
            run_web_simulation(config, args.host, args.port, args.debug)
    
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()