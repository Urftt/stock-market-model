"""Real-time visualization for stock trading simulation using Plotly Dash."""

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import time

from .simulation import TradingSimulation, SimulationConfig


class SimulationVisualizer:
    """Real-time visualization for trading simulation."""
    
    def __init__(self, simulation: Optional[TradingSimulation] = None):
        """Initialize visualizer with simulation instance."""
        self.simulation = simulation or TradingSimulation()
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()
        
        # Simulation control
        self.simulation_thread = None
        self.is_simulation_running = False
        self.speed_multiplier = 1.0
        
    def setup_layout(self):
        """Setup the Dash app layout."""
        self.app.layout = html.Div([
            html.Div([
                html.H1("Stock Pattern Simulation", 
                       style={'textAlign': 'center', 'marginBottom': 30}),
                
                # Control panel
                html.Div([
                    html.Div([
                        html.Button('Start Simulation', id='start-btn', 
                                  className='btn btn-success', 
                                  style={'marginRight': 10}),
                        html.Button('Stop Simulation', id='stop-btn', 
                                  className='btn btn-danger',
                                  style={'marginRight': 10}),
                        html.Button('Reset', id='reset-btn', 
                                  className='btn btn-warning',
                                  style={'marginRight': 20}),
                    ], style={'display': 'inline-block'}),
                    
                    html.Div([
                        html.Label('Speed: ', style={'marginRight': 10}),
                        dcc.Slider(
                            id='speed-slider',
                            min=0.1,
                            max=10.0,
                            step=0.1,
                            value=1.0,
                            marks={i: f'{i}x' for i in [0.5, 1, 2, 5, 10]},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'display': 'inline-block', 'width': '300px', 'marginLeft': 20})
                ], style={'textAlign': 'center', 'marginBottom': 20}),
                
                # Status display
                html.Div(id='status-display', 
                        style={'textAlign': 'center', 'marginBottom': 20}),
                
                # Main chart
                dcc.Graph(id='candlestick-chart', 
                         style={'height': '500px'}),
                
                # Market data row
                html.Div([
                    # Order book
                    html.Div([
                        html.H4("Order Book"),
                        html.Div(id='order-book-display')
                    ], className='col-md-4', style={'padding': 10}),
                    
                    # Recent trades
                    html.Div([
                        html.H4("Recent Trades"),
                        html.Div(id='recent-trades-display')
                    ], className='col-md-4', style={'padding': 10}),
                    
                    # Statistics
                    html.Div([
                        html.H4("Statistics"),
                        html.Div(id='stats-display')
                    ], className='col-md-4', style={'padding': 10})
                ], className='row', style={'marginTop': 20}),
                
            ], style={'margin': '20px'}),
            
            # Hidden div to store simulation state
            html.Div(id='simulation-state', style={'display': 'none'}),
            
            # Interval component for real-time updates
            dcc.Interval(
                id='interval-component',
                interval=1000,  # Update every second
                n_intervals=0,
                disabled=True
            )
        ])
    
    def setup_callbacks(self):
        """Setup Dash callbacks for interactivity."""
        
        @self.app.callback(
            [Output('interval-component', 'disabled'),
             Output('simulation-state', 'children')],
            [Input('start-btn', 'n_clicks'),
             Input('stop-btn', 'n_clicks'),
             Input('reset-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def control_simulation(start_clicks, stop_clicks, reset_clicks):
            """Handle simulation control buttons."""
            ctx = dash.callback_context
            if not ctx.triggered:
                return True, "stopped"
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'start-btn':
                self.start_simulation()
                return False, "running"
            elif button_id == 'stop-btn':
                self.stop_simulation()
                return True, "stopped"
            elif button_id == 'reset-btn':
                self.reset_simulation()
                return True, "reset"
            
            return True, "stopped"
        
        @self.app.callback(
            Output('speed-slider', 'value'),
            [Input('speed-slider', 'value')]
        )
        def update_speed(speed):
            """Update simulation speed."""
            self.speed_multiplier = speed
            return speed
        
        @self.app.callback(
            [Output('candlestick-chart', 'figure'),
             Output('status-display', 'children'),
             Output('order-book-display', 'children'),
             Output('recent-trades-display', 'children'),
             Output('stats-display', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('simulation-state', 'children')]
        )
        def update_displays(n_intervals, simulation_state):
            """Update all displays with current simulation data."""
            # Get current market data
            market_data = self.simulation.get_current_market_data()
            stats = self.simulation.get_simulation_stats()
            
            # Create candlestick chart
            fig = self.create_candlestick_chart()
            
            # Create status display
            status = self.create_status_display(market_data, stats)
            
            # Create order book display
            order_book = self.create_order_book_display(market_data)
            
            # Create recent trades display
            recent_trades = self.create_recent_trades_display(market_data)
            
            # Create statistics display
            statistics = self.create_statistics_display(stats)
            
            return fig, status, order_book, recent_trades, statistics
    
    def create_candlestick_chart(self):
        """Create the main candlestick chart."""
        df = self.simulation.get_candlestick_dataframe()
        
        if len(df) == 0:
            # Empty chart
            fig = go.Figure()
            fig.update_layout(
                title="Waiting for simulation data...",
                xaxis_title="Time",
                yaxis_title="Price ($)",
                height=500
            )
            return fig
        
        # Convert to Python lists for plotly compatibility
        timestamps = df['Timestamp'].to_list()
        opens = df['Open'].to_list()
        highs = df['High'].to_list()
        lows = df['Low'].to_list()
        closes = df['Close'].to_list()
        volumes = df['Volume'].to_list()
        
        # Create subplots for price and volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('Price', 'Volume'),
            row_heights=[0.7, 0.3]
        )
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=timestamps,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name="OHLC"
            ),
            row=1, col=1
        )
        
        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=timestamps,
                y=volumes,
                name="Volume",
                marker_color='rgba(0,100,200,0.7)'
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=f"Stock Simulation - Current Price: ${self.simulation.order_book.current_price:.2f}",
            xaxis_rangeslider_visible=False,
            height=500,
            showlegend=False
        )
        
        # Update axes
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
    
    def create_status_display(self, market_data: Dict, stats: Dict):
        """Create status display component."""
        current_price = market_data['current_price']
        spread = market_data['spread']
        best_bid = market_data['best_bid']
        best_ask = market_data['best_ask']
        
        return html.Div([
            html.Span(f"Price: ${current_price:.2f} | ", 
                     style={'fontSize': '18px', 'fontWeight': 'bold'}),
            html.Span(f"Bid: ${best_bid:.2f} " if best_bid else "Bid: N/A ",
                     style={'color': 'green'}),
            html.Span(f"Ask: ${best_ask:.2f} " if best_ask else "Ask: N/A ",
                     style={'color': 'red'}),
            html.Span(f"Spread: ${spread:.4f} | " if spread else "Spread: N/A | "),
            html.Span(f"Step: {stats['simulation']['step_count']} | "),
            html.Span(f"Trades: {stats['trading']['total_trades']}")
        ])
    
    def create_order_book_display(self, market_data: Dict):
        """Create order book display."""
        bids = market_data['bids'][:5]  # Top 5 bids
        asks = market_data['asks'][:5]  # Top 5 asks
        
        # Create table
        table_rows = []
        
        # Header
        table_rows.append(html.Tr([
            html.Th("Quantity", style={'textAlign': 'center'}),
            html.Th("Bid", style={'textAlign': 'center', 'color': 'green'}),
            html.Th("Ask", style={'textAlign': 'center', 'color': 'red'}),
            html.Th("Quantity", style={'textAlign': 'center'})
        ]))
        
        # Data rows
        max_rows = max(len(bids), len(asks))
        for i in range(max_rows):
            bid_qty = bids[i][1] if i < len(bids) else ""
            bid_price = f"${bids[i][0]:.2f}" if i < len(bids) else ""
            ask_price = f"${asks[i][0]:.2f}" if i < len(asks) else ""
            ask_qty = asks[i][1] if i < len(asks) else ""
            
            table_rows.append(html.Tr([
                html.Td(bid_qty, style={'textAlign': 'center'}),
                html.Td(bid_price, style={'textAlign': 'center', 'color': 'green'}),
                html.Td(ask_price, style={'textAlign': 'center', 'color': 'red'}),
                html.Td(ask_qty, style={'textAlign': 'center'})
            ]))
        
        return html.Table(table_rows, style={'width': '100%', 'fontSize': '12px'})
    
    def create_recent_trades_display(self, market_data: Dict):
        """Create recent trades display."""
        recent_trades = market_data['recent_trades'][-10:]  # Last 10 trades
        
        if not recent_trades:
            return html.Div("No trades yet")
        
        trade_rows = []
        for trade in reversed(recent_trades):  # Most recent first
            trade_rows.append(html.Div([
                html.Span(f"${trade['price']:.2f}", 
                         style={'fontWeight': 'bold', 'marginRight': 10}),
                html.Span(f"{trade['quantity']}", 
                         style={'marginRight': 10}),
                html.Span(trade['timestamp'].strftime("%H:%M:%S"),
                         style={'fontSize': '10px', 'color': 'gray'})
            ], style={'marginBottom': 2}))
        
        return html.Div(trade_rows, style={'height': '200px', 'overflowY': 'scroll'})
    
    def create_statistics_display(self, stats: Dict):
        """Create statistics display."""
        return html.Div([
            html.P(f"Traders: {stats['traders']['total_traders']}"),
            html.P(f"Total Orders: {stats['traders']['total_orders_placed']}"),
            html.P(f"Orders/sec: {stats['trading']['performance']['orders_per_second']:.1f}"),
            html.P(f"Trades/sec: {stats['trading']['performance']['trades_per_second']:.1f}"),
            html.P(f"Total Volume: {stats['market_data']['total_volume']:,}"),
            html.P(f"Price Range: ${stats['market_data']['price_range']['min']:.2f} - ${stats['market_data']['price_range']['max']:.2f}")
        ])
    
    def start_simulation(self):
        """Start the simulation in a separate thread."""
        if not self.is_simulation_running:
            self.simulation.start()
            self.is_simulation_running = True
            self.simulation_thread = threading.Thread(target=self._run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop the simulation."""
        self.is_simulation_running = False
        self.simulation.stop()
    
    def reset_simulation(self):
        """Reset the simulation."""
        self.stop_simulation()
        time.sleep(0.1)  # Brief pause
        self.simulation.reset()
    
    def _run_simulation(self):
        """Run simulation steps in background thread."""
        while self.is_simulation_running:
            step_start = time.time()
            
            # Execute simulation step
            self.simulation.step()
            
            # Calculate sleep time based on speed multiplier
            step_duration = time.time() - step_start
            target_duration = self.simulation.config.time_step_seconds / self.speed_multiplier
            sleep_time = max(0, target_duration - step_duration)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def run(self, debug=False, host='127.0.0.1', port=8050):
        """Run the Dash app."""
        print(f"Starting Stock Pattern Simulation Dashboard...")
        print(f"Open http://{host}:{port} in your browser")
        self.app.run(debug=debug, host=host, port=port)