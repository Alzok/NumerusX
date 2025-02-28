from nicegui import ui
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
import asyncio
import time
import psutil
import logging
from collections import deque

from app.dex_bot import DexBot, PerformanceMonitor
from app.database import EnhancedDatabase
from app.dex_api import DexAPI
from app.config import Config
from app.analytics_engine import AdvancedTradingStrategy

logger = logging.getLogger('dashboard')

class NumerusXDashboard:
    """Enhanced dashboard for NumerusX trading bot with comprehensive monitoring and control."""
    
    def __init__(self, bot: DexBot):
        """
        Initialize the dashboard with a reference to the trading bot.
        
        Args:
            bot: Instance of DexBot to monitor and control
        """
        self.bot = bot
        self.db = EnhancedDatabase()
        self.dex_api = DexAPI()
        self.analytics = AdvancedTradingStrategy()
        
        # Performance monitoring
        self.performance = PerformanceMonitor()
        self.system_metrics = {
            'cpu': deque(maxlen=60),
            'memory': deque(maxlen=60),
            'uptime': 0,
            'api_latency': deque(maxlen=30),
            'error_count': 0
        }
        
        # UI components
        self.status_indicator = None
        self.portfolio_value_card = None
        self.portfolio_change_card = None
        self.portfolio_chart = None
        self.trades_table = None
        self.market_condition_indicator = None
        self.toggle_btn = None
        self.risk_slider = None
        
        # State
        self.selected_token = None
        self.refresh_rate = 2.0  # seconds
        self.theme = 'light'
        self.asset_data = {}
        self.error_log = deque(maxlen=100)
        
        # Start monitoring tasks
        self.is_running = True
        self.start_time = time.time()
        
        # Initialize UI
        self.init_ui()
        
        # Start update tasks
        ui.timer(self.refresh_rate, self.update_dashboard)
        ui.timer(5.0, self.update_system_metrics)
        ui.timer(60.0, self.update_historical_data)

    def init_ui(self):
        """Initialize the comprehensive dashboard UI."""
        # Apply theme based on preference
        ui.dark_mode().enable() if self.theme == 'dark' else ui.dark_mode().disable()
        
        # Header with bot status and controls
        with ui.header().classes('bg-primary text-white p-3 flex items-center justify-between'):
            with ui.row().classes('items-center'):
                ui.icon('currency_bitcoin', size='lg').classes('mr-2')
                ui.label('NumerusX Trading Dashboard').classes('text-xl font-bold')
            
            with ui.row().classes('items-center'):
                self.status_indicator = ui.icon('circle', size='sm', color='red').tooltip('Bot Status')
                ui.space()
                ui.button(icon='refresh', on_click=self.update_dashboard).props('flat')
                with ui.button(icon='settings', color='white').props('flat').tooltip('Settings'):
                    with ui.menu().classes('w-72'):
                        ui.label('Settings').classes('text-lg font-bold px-4 py-2')
                        ui.separator()
                        ui.switch('Dark Mode', value=self.theme == 'dark').bind_value_to(self, 'theme_enabled').on('change', self.toggle_theme)
                        ui.number('Refresh Rate (seconds)', value=self.refresh_rate, min=1, max=10).bind_value_to(self, 'refresh_rate')
                        ui.button('Reset Performance Data', on_click=self.reset_performance_data).props('outline')

        # Main container with tabs
        with ui.tabs().classes('w-full') as tabs:
            portfolio_tab = ui.tab('Portfolio')
            trading_tab = ui.tab('Trading Activity')
            market_tab = ui.tab('Market Analysis')
            control_tab = ui.tab('Control Center')
            monitor_tab = ui.tab('System Monitor')
            
        with ui.tab_panels(tabs, value=portfolio_tab).classes('w-full p-4'):
            with ui.tab_panel(portfolio_tab):
                self._build_portfolio_panel()
                
            with ui.tab_panel(trading_tab):
                self._build_trading_activity_panel()
                
            with ui.tab_panel(market_tab):
                self._build_market_analysis_panel()
                
            with ui.tab_panel(control_tab):
                self._build_control_panel()
                
            with ui.tab_panel(monitor_tab):
                self._build_system_monitor_panel()
        
        # Footer with version and status info
        with ui.footer().classes('bg-gray-100 p-2 text-center text-xs'):
            ui.label(f'NumerusX v1.0.0 - {datetime.now().strftime("%Y-%m-%d")}')

    def _build_portfolio_panel(self):
        """Build the portfolio overview panel."""
        with ui.row().classes('w-full justify-between gap-4'):
            # Portfolio value and change cards
            with ui.column().classes('w-full md:w-1/3 gap-4'):
                with ui.card().classes('w-full'):
                    ui.label('Portfolio Value').classes('text-lg font-bold')
                    self.portfolio_value_card = ui.label('$0.00').classes('text-3xl font-bold')
                    self.portfolio_change_card = ui.label('0.00%').classes('text-lg')
                
                with ui.card().classes('w-full'):
                    ui.label('Asset Allocation').classes('text-lg font-bold mb-2')
                    self.asset_allocation_chart = ui.plotly({}).classes('w-full h-64')
            
            # Performance chart
            with ui.card().classes('w-full md:w-2/3'):
                ui.label('Portfolio Performance').classes('text-lg font-bold')
                with ui.row().classes('ml-auto gap-2'):
                    ui.button('1D', on_click=lambda: self.update_performance_chart('1d')).props('flat')
                    ui.button('1W', on_click=lambda: self.update_performance_chart('1w')).props('flat')
                    ui.button('1M', on_click=lambda: self.update_performance_chart('1m')).props('flat')
                
                self.portfolio_chart = ui.plotly({}).classes('w-full h-64')
                
        # Top holdings table
        with ui.card().classes('w-full mt-4'):
            ui.label('Top Holdings').classes('text-lg font-bold')
            self.holdings_table = ui.table(
                columns=[
                    {'name': 'asset', 'label': 'Asset', 'field': 'asset', 'align': 'left'},
                    {'name': 'amount', 'label': 'Amount', 'field': 'amount', 'align': 'right'},
                    {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'right'},
                    {'name': 'value', 'label': 'Value', 'field': 'value', 'align': 'right'},
                    {'name': 'change', 'label': '24h Change', 'field': 'change', 'align': 'right'},
                ],
                rows=[]
            ).classes('w-full')

    def _build_trading_activity_panel(self):
        """Build the trading activity center panel."""
        with ui.row().classes('w-full gap-4'):
            # Recent trades table
            with ui.card().classes('w-full md:w-2/3'):
                ui.label('Recent Trades').classes('text-lg font-bold')
                self.trades_table = ui.table(
                    columns=[
                        {'name': 'time', 'label': 'Time', 'field': 'time', 'align': 'left'},
                        {'name': 'pair', 'label': 'Pair', 'field': 'pair', 'align': 'left'},
                        {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'center'},
                        {'name': 'amount', 'label': 'Amount', 'field': 'amount', 'align': 'right'},
                        {'name': 'price', 'label': 'Price', 'field': 'price', 'align': 'right'},
                        {'name': 'pnl', 'label': 'P&L', 'field': 'pnl', 'align': 'right'},
                        {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
                    ],
                    rows=[]
                ).classes('w-full')
                
            # Trade metrics cards
            with ui.column().classes('w-full md:w-1/3 gap-4'):
                with ui.card().classes('w-full'):
                    ui.label('Trade Success Rate').classes('text-lg font-bold')
                    self.success_rate_chart = ui.plotly({}).classes('w-full h-40')
                
                with ui.card().classes('w-full'):
                    ui.label('Daily Volume').classes('text-lg font-bold')
                    self.volume_chart = ui.plotly({}).classes('w-full h-40')
        
        # Trade distribution
        with ui.card().classes('w-full mt-4'):
            ui.label('Trade Distribution').classes('text-lg font-bold')
            with ui.row().classes('w-full gap-4'):
                self.trade_distribution_chart = ui.plotly({}).classes('w-full md:w-1/2 h-64')
                self.trade_time_distribution = ui.plotly({}).classes('w-full md:w-1/2 h-64')

    def _build_market_analysis_panel(self):
        """Build the market analysis section."""
        with ui.row().classes('w-full gap-4'):
            # Market condition indicator
            with ui.column().classes('w-full md:w-1/3 gap-4'):
                with ui.card().classes('w-full'):
                    ui.label('Market Condition').classes('text-lg font-bold')
                    with ui.row().classes('items-center justify-center p-4'):
                        self.market_condition_indicator = ui.icon('trending_up', size='xl')
                        self.market_condition_label = ui.label('Bullish').classes('text-xl ml-2')
                
                with ui.card().classes('w-full'):
                    ui.label('Trading Opportunities').classes('text-lg font-bold')
                    self.watchlist_table = ui.table(
                        columns=[
                            {'name': 'token', 'label': 'Token', 'field': 'token', 'align': 'left'},
                            {'name': 'score', 'label': 'Score', 'field': 'score', 'align': 'center'},
                            {'name': 'action', 'label': 'Action', 'field': 'action', 'align': 'center'},
                        ],
                        rows=[]
                    ).classes('w-full')
            
            # Price chart for selected asset
            with ui.card().classes('w-full md:w-2/3'):
                with ui.row().classes('items-center justify-between'):
                    ui.label('Price Chart').classes('text-lg font-bold')
                    ui.select(
                        options=[],
                        label='Select Token',
                        on_change=self.update_selected_token
                    ).classes('w-48').bind_value_to(self, 'selected_token')
                
                with ui.row().classes('ml-auto gap-2'):
                    ui.button('1H', on_click=lambda: self.update_price_chart('1h')).props('flat')
                    ui.button('4H', on_click=lambda: self.update_price_chart('4h')).props('flat')
                    ui.button('1D', on_click=lambda: self.update_price_chart('1d')).props('flat')
                
                self.price_chart = ui.plotly({}).classes('w-full h-64')
        
        # Technical indicators
        with ui.card().classes('w-full mt-4'):
            ui.label('Technical Indicators').classes('text-lg font-bold')
            with ui.tabs().classes('w-full') as indicator_tabs:
                rsi_tab = ui.tab('RSI')
                macd_tab = ui.tab('MACD')
                bb_tab = ui.tab('Bollinger Bands')
            
            with ui.tab_panels(indicator_tabs, value=rsi_tab).classes('w-full'):
                with ui.tab_panel(rsi_tab):
                    self.rsi_chart = ui.plotly({}).classes('w-full h-48')
                
                with ui.tab_panel(macd_tab):
                    self.macd_chart = ui.plotly({}).classes('w-full h-48')
                
                with ui.tab_panel(bb_tab):
                    self.bb_chart = ui.plotly({}).classes('w-full h-48')

    def _build_control_panel(self):
        """Build the control center panel."""
        with ui.row().classes('w-full gap-4'):
            # Main controls
            with ui.card().classes('w-full md:w-1/3'):
                ui.label('Bot Controls').classes('text-lg font-bold')
                
                self.toggle_btn = ui.button(
                    'Start Bot',
                    on_click=self.toggle_bot,
                    icon='play_arrow'
                ).props('unelevated color=green').classes('w-full mb-4')
                
                ui.button(
                    'Emergency Stop',
                    on_click=self.emergency_stop,
                    icon='emergency'
                ).props('unelevated color=red').classes('w-full mb-4')
                
                ui.label('Risk Level').classes('text-md mt-4')
                self.risk_slider = ui.slider(
                    min=0.1,
                    max=1.0,
                    step=0.05,
                    value=Config.TRADE_THRESHOLD
                ).props('label label-always').on('change', self.update_risk_level)
                
                ui.label('Strategy').classes('text-md mt-4')
                ui.select(
                    options=[
                        {'label': 'Conservative', 'value': 'conservative'},
                        {'label': 'Balanced', 'value': 'balanced'},
                        {'label': 'Aggressive', 'value': 'aggressive'}
                    ],
                    value='balanced',
                    on_change=self.update_strategy
                ).classes('w-full')
            
            # Manual trade form
            with ui.card().classes('w-full md:w-2/3'):
                ui.label('Manual Trade').classes('text-lg font-bold')
                
                with ui.row().classes('w-full items-end gap-4'):
                    with ui.column().classes('w-1/3'):
                        ui.select(
                            options=[],
                            label='Input Token',
                            value='USDC'
                        ).classes('w-full').bind_value_to(self, 'input_token')
                    
                    ui.icon('swap_horiz', size='lg').classes('mb-2')
                    
                    with ui.column().classes('w-1/3'):
                        ui.select(
                            options=[],
                            label='Output Token'
                        ).classes('w-full').bind_value_to(self, 'output_token')
                    
                    with ui.column().classes('w-1/5'):
                        ui.number(label='Amount', format='%.2f').classes('w-full').bind_value_to(self, 'trade_amount')
                
                with ui.row().classes('w-full justify-between mt-4'):
                    ui.label('Estimated Fee: ').classes('text-sm')
                    self.estimated_fee_label = ui.label('0.00 SOL').classes('text-sm')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Preview', on_click=self.preview_trade).props('outline')
                    ui.button('Execute', on_click=self.execute_trade).props('unelevated color=primary')
        
        # Trading parameters
        with ui.card().classes('w-full mt-4'):
            ui.label('Trading Parameters').classes('text-lg font-bold')
            
            with ui.grid(columns=2).classes('w-full gap-4'):
                # Column 1
                with ui.card().classes('p-4'):
                    ui.label('Slippage Tolerance').classes('font-bold')
                    ui.slider(min=0.1, max=3.0, step=0.1, value=Config.SLIPPAGE * 100).classes('w-full')
                    ui.label('Applies to all trades').classes('text-xs text-gray-500')
                
                # Column 2
                with ui.card().classes('p-4'):
                    ui.label('Max Position Size').classes('font-bold')
                    ui.number(value=Config.MAX_ORDER_SIZE, format='%.2f').classes('w-full')
                    ui.label('Maximum order size in USD').classes('text-xs text-gray-500')
                
                # Column 3  
                with ui.card().classes('p-4'):
                    ui.label('Max Positions').classes('font-bold')
                    ui.number(value=Config.MAX_POSITIONS, format='%d', min=1, max=20).classes('w-full')
                    ui.label('Maximum number of concurrent positions').classes('text-xs text-gray-500')
                
                # Column 4
                with ui.card().classes('p-4'):
                    ui.label('Update Interval').classes('font-bold')
                    ui.number(value=Config.UPDATE_INTERVAL, format='%d', min=5, max=300).classes('w-full')
                    ui.label('Time between bot cycles in seconds').classes('text-xs text-gray-500')

    def _build_system_monitor_panel(self):
        """Build the system monitoring panel."""
        with ui.row().classes('w-full gap-4'):
            # System status cards
            with ui.column().classes('w-full md:w-1/3 gap-4'):
                # Uptime card
                with ui.card().classes('w-full'):
                    ui.label('System Uptime').classes('text-lg font-bold')
                    self.uptime_label = ui.label('0h 0m 0s').classes('text-3xl font-bold text-center p-4')
                
                # Status indicators
                with ui.card().classes('w-full'):
                    ui.label('Component Status').classes('text-lg font-bold')
                    
                    with ui.row().classes('items-center justify-between p-2'):
                        ui.label('Trading Engine')
                        self.engine_status = ui.icon('check_circle', color='green')
                    
                    with ui.row().classes('items-center justify-between p-2'):
                        ui.label('Market Data API')
                        self.market_api_status = ui.icon('check_circle', color='green')
                    
                    with ui.row().classes('items-center justify-between p-2'):
                        ui.label('Database')
                        self.db_status = ui.icon('check_circle', color='green')
            
            # Resource usage charts
            with ui.card().classes('w-full md:w-2/3'):
                ui.label('Resource Usage').classes('text-lg font-bold')
                with ui.tabs().classes('w-full') as resource_tabs:
                    cpu_tab = ui.tab('CPU')
                    memory_tab = ui.tab('Memory')
                    latency_tab = ui.tab('API Latency')
                
                with ui.tab_panels(resource_tabs, value=cpu_tab).classes('w-full'):
                    with ui.tab_panel(cpu_tab):
                        self.cpu_chart = ui.plotly({}).classes('w-full h-64')
                    
                    with ui.tab_panel(memory_tab):
                        self.memory_chart = ui.plotly({}).classes('w-full h-64')
                    
                    with ui.tab_panel(latency_tab):
                        self.latency_chart = ui.plotly({}).classes('w-full h-64')
        
        # Error log
        with ui.card().classes('w-full mt-4'):
            ui.label('Error Log').classes('text-lg font-bold')
            self.error_log_area = ui.log().classes('w-full h-64 font-mono text-xs')

    async def update_dashboard(self):
        """Update all dashboard components with latest data."""
        try:
            # Update bot status indicator
            self.status_indicator.props(f'color={"green" if self.bot.active else "red"}')
            
            # Update portfolio data
            await self.update_portfolio_data()
            
            # Update trading activity
            await self.update_trading_activity()
            
            # Update market analysis
            await self.update_market_analysis()
            
            # Update control center
            self.update_control_center()
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {str(e)}")
            self.error_log.append(f"{datetime.now().strftime('%H:%M:%S')} - Dashboard update error: {str(e)}")
            self.error_log_area.push(f"ERROR: Dashboard update failed: {str(e)}")
            self.system_metrics['error_count'] += 1
    
    async def update_portfolio_data(self):
        """Update portfolio overview data."""
        try:
            # Get portfolio value from bot
            portfolio_value = self.bot.portfolio.current_balance
            
            # Update portfolio value card
            self.portfolio_value_card.text = f"${portfolio_value:,.2f}"
            
            # Get historical portfolio values for change calculation
            yesterday_value = portfolio_value * 0.98  # Placeholder - should be from actual historical data
            change_pct = ((portfolio_value - yesterday_value) / yesterday_value) * 100
            change_color = "green" if change_pct >= 0 else "red"
            
            # Update change card
            self.portfolio_change_card.text = f"{change_pct:+.2f}%"
            self.portfolio_change_card.style(f"color: {change_color}")
            
            # Get asset allocation data
            holdings = await self.get_holdings()
            
            # Update asset allocation chart
            self.update_asset_allocation_chart(holdings)
            
            # Update holdings table
            holdings_rows = []
            for asset in holdings:
                holdings_rows.append({
                    'asset': asset['symbol'],
                    'amount': f"{asset['amount']:.4f}",
                    'price': f"${asset['price']:.4f}",
                    'value': f"${asset['value']:.2f}",
                    'change': f"{asset['change']:+.2f}%"
                })
            self.holdings_table.rows = holdings_rows
            
            # Update performance chart
            self.update_performance_chart('1d')
            
        except Exception as e:
            logger.error(f"Error updating portfolio data: {str(e)}")
            self.error_log.append(f"{datetime.now().strftime('%H:%M:%S')} - Portfolio update error: {str(e)}")
    
    async def update_trading_activity(self):
        """Update trading activity data."""
        try:
            # Get recent trades from database
            trades = self.db.get_active_trades()
            
            # Update trades table
            trades_rows = []
            for trade in trades:
                # Get current price
                current_price = self.dex_api.get_price(trade['pair_address'])
                
                # Calculate P&L
                entry_price = trade.get('entry_price', 0)
                if entry_price and current_price:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    pnl_color = "green" if pnl_pct >= 0 else "red"
                    pnl_text = f"<span style='color:{pnl_color}'>{pnl_pct:+.2f}%</span>"
                else:
                    pnl_text = "N/A"
                
                # Format timestamp
                timestamp = datetime.fromtimestamp(trade.get('timestamp', time.time()))
                
                trades_rows.append({
                    'time': timestamp.strftime('%H:%M:%S'),
                    'pair': trade['pair_address'],
                    'type': 'BUY',  # Placeholder - should determine from actual data
                    'amount': f"${trade['amount']:.2f}",
                    'price': f"${entry_price:.4f}",
                    'pnl': pnl_text,
                    'status': trade.get('status', 'open')
                })
            self.trades_table.rows = trades_rows
            
            # Update success rate chart
            self.update_success_rate_chart()
            
            # Update volume chart
            self.update_volume_chart()
            
            # Update trade distribution charts
            self.update_trade_distribution_charts()
            
        except Exception as e:
            logger.error(f"Error updating trading activity: {str(e)}")
            self.error_log.append(f"{datetime.now().strftime('%H:%M:%S')} - Trading activity update error: {str(e)}")
    
    async def update_market_analysis(self):
        """Update market analysis data."""
        try:
            # Update market condition indicator
            market_condition = await self.get_market_condition()
            if market_condition == 'bullish':
                self.market_condition_indicator.props('icon=trending_up color=green')
                self.market_condition_label.text = 'Bullish'
                self.market_condition_label.style('color: green')
            elif market_condition == 'bearish':
                self.market_condition_indicator.props('icon=trending_down color=red')
                self.market_condition_label.text = 'Bearish'
                self.market_condition_label.style('color: red')
            else:
                self.market_condition_indicator.props('icon=trending_flat color=gray')
                self.market_condition_label.text = 'Neutral'
                self.market_condition_label.style('color: gray')
            
            # Update trading opportunities table
            opportunities = await self.get_trading_opportunities()
            opportunity_rows = []
            for opp in opportunities:
                opportunity_rows.append({
                    'token': opp['symbol'],
                    'score': f"{opp['score']:.2f}",
                    'action': opp['action']
                })
            self.watchlist_table.rows = opportunity_rows
            
            # Update price chart if token is selected
            if self.selected_token:
                self.update_price_chart('4h')
                
            # Update technical indicators
            self.update_technical_indicators()
            
        except Exception as e:
            logger.error(f"Error updating market analysis: {str(e)}")
            self.error_log.append(f"{datetime.now().strftime('%H:%M:%S')} - Market analysis update error: {str(e)}")
    
    def update_control_center(self):
        """Update control center data."""
        try:
            # Update bot control button
            if self.bot.active:
                self.toggle_btn.text = 'Stop Bot'
                self.toggle_btn.props('color=red icon=stop')
            else:
                self.toggle_btn.text = 'Start Bot'
                self.toggle_btn.props('color=green icon=play_arrow')
            
            # Update risk level slider value if it changed in Config
            self.risk_slider.value = Config.TRADE_THRESHOLD
            
            # Update estimated fee for manual trade (if tokens are selected)
            if hasattr(self, 'input_token') and hasattr(self, 'output_token') and hasattr(self, 'trade_amount'):
                # Placeholder for actual fee calculation
                estimated_fee = 0.000005 * self.trade_amount if self.trade_amount else 0
                self.estimated_fee_label.text = f"{estimated_fee:.6f} SOL"
            
        except Exception as e:
            logger.error(f"Error updating control center: {str(e)}")
            self.error_log.append(f"{datetime.now().strftime('%H:%M:%S')} - Control center update error: {str(e)}")
    
    def update_system_metrics(self):
        """Update system monitoring metrics."""
        try:
            # Update uptime
            uptime_seconds = time.time() - self.start_time
            hours, remainder = divmod(int(uptime_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.text = f"{hours}h {minutes}m {seconds}s"
            self.system_metrics['uptime'] = uptime_seconds
            
            # Update CPU and memory usage
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            self.system_metrics['cpu'].append((time.time(), cpu_usage))
            self.system_metrics['memory'].append((time.time(), memory_usage))
            
            # Update API latency (placeholder - should be actual API call timing)
            api_latency = 50 + 20 * (0.5 - (0.5 * (time.time() % 10) / 10))  # Simulated value
            self.system_metrics['api_latency'].append((time.time(), api_latency))
            
            # Update component status indicators
            engine_ok = True  # Placeholder - should check actual component status
            market_api_ok = True
            db_ok = True
            
            self.engine_status.props(f'color={"green" if engine_ok else "red"}')
            self.market_api_status.props(f'color={"green" if market_api_ok else "red"}')
            self.db_status.props(f'color={"green" if db_ok else "red"}')
            
            # Update resource charts
            self.update_resource_charts()
            
            # Update error log
            for error in self.error_log:
                self.error_log_area.push(error)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")
            self.error_log_area.push(f"ERROR: System metrics update failed: {str(e)}")
    
    def update_historical_data(self):
        """Update historical data for charts (runs less frequently)."""
        try:
            # This method can fetch historical data that doesn't change as frequently
            # Such as daily candles, historical portfolio value, etc.
            pass
        except Exception as e:
            logger.error(f"Error updating historical data: {str(e)}")
            self.error_log.append(f"{datetime.now().strftime('%H:%M:%S')} - Historical data update error: {str(e)}")
    
    def toggle_bot(self):
        """Toggle bot active state."""
        if self.bot.active:
            self.bot.stop()
            self.toggle_btn.text = 'Start Bot'
            self.toggle_btn.props('color=green icon=play_arrow')
            self.error_log_area.push(f"INFO: Bot stopped at {datetime.now().strftime('%H:%M:%S')}")
        else:
            self.bot.run()
            self.toggle_btn.text = 'Stop Bot'
            self.toggle_btn.props('color=red icon=stop')
            self.error_log_area.push(f"INFO: Bot started at {datetime.now().strftime('%H:%M:%S')}")
    
    def emergency_stop(self):
        """Emergency stop all bot operations."""
        if self.bot.active:
            self.bot.stop()
            self.toggle_btn.text = 'Start Bot'
            self.toggle_btn.props('color=green icon=play_arrow')
        
        # Log the emergency stop
        self.error_log_area.push(f"ALERT: Emergency stop triggered at {datetime.now().strftime('%H:%M:%S')}")
        
        # Show confirmation dialog
        ui.notify('Emergency stop activated! All trading halted.', type='negative')
    
    def update_risk_level(self):
        """Update risk level based on slider value."""
        Config.TRADE_THRESHOLD = self.risk_slider.value
        self.error_log_area.push(f"INFO: Risk level updated to {Config.TRADE_THRESHOLD:.2f}")
        ui.notify(f'Risk level updated to {Config.TRADE_THRESHOLD:.2f}')
    
    def update_strategy(self, event):
        """Update selected trading strategy."""
        strategy = event.value
        # Placeholder - should actually change the strategy
        self.error_log_area.push(f"INFO: Strategy changed to {strategy}")
        ui.notify(f'Strategy changed to {strategy}')
    
    def preview_trade(self):
        """Preview manual trade before execution."""
        if not hasattr(self, 'input_token') or not hasattr(self, 'output_token') or not hasattr(self, 'trade_amount'):
            ui.notify('Please select tokens and enter an amount', type='warning')
            return
            
        # Placeholder - should call the swap API to get a quote
        input_token = self.input_token 
        output_token = self.output_token
        amount = self.trade_amount
        
        # Show preview dialog
        with ui.dialog() as dialog, ui.card():
            ui.label('Trade Preview').classes('text-xl font-bold')
            ui.separator()
            ui.label(f'Swap {amount} {input_token} for {output_token}')
            ui.label(f'Estimated output: 0.123 {output_token}')  # Placeholder
            ui.label(f'Price impact: 0.05%')  # Placeholder
            ui.label(f'Fee: 0.000005 SOL')  # Placeholder
            ui.separator()
            with ui.row().classes('w-full justify-end'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Confirm Trade', on_click=lambda: self.execute_trade(dialog)).props('unelevated color=primary')
        
        dialog.open()
    
    def execute_trade(self, dialog=None):
        """Execute manual trade."""
        if dialog:
            dialog.close()
            
        if not hasattr(self, 'input_token') or not hasattr(self, 'output_token') or not hasattr(self, 'trade_amount'):
            ui.notify('Please select tokens and enter an amount', type='warning')
            return
            
        # Placeholder - should call the trading engine to execute the swap
        input_token = self.input_token 
        output_token = self.output_token
        amount = self.trade_amount
        
        # Log the trade
        self.error_log_area.push(f"INFO: Manual trade executed: {amount} {input_token} to {output_token}")
        
        # Show confirmation
        ui.notify(f'Trade executed: {amount} {input_token} to {output_token}', type='positive')
    
    def update_selected_token(self, event):
        """Update the selected token for charts."""
        self.selected_token = event.value
        self.update_price_chart('4h')
        self.update_technical_indicators()
    
    def toggle_theme(self, event):
        """Toggle between light and dark theme."""
        self.theme = 'dark' if event.value else 'light'
        if self.theme == 'dark':
            ui.dark_mode().enable()
        else:
            ui.dark_mode().disable()
    
    def reset_performance_data(self):
        """Reset performance metrics."""
        self.performance = PerformanceMonitor()
        self.error_log_area.push(f"INFO: Performance data reset at {datetime.now().strftime('%H:%M:%S')}")
        ui.notify('Performance data has been reset')
    
    def update_price_chart(self, timeframe='4h'):
        """Update price chart for selected token."""
        if not self.selected_token:
            return
            
        # Placeholder - should get actual historical price data
        # Generate sample data for now
        end_date = datetime.now()
        
        if timeframe == '1h':
            start_date = end_date - timedelta(hours=24)
            interval = timedelta(minutes=5)
        elif timeframe == '4h':
            start_date = end_date - timedelta(days=7)
            interval = timedelta(hours=1)
        elif timeframe == '1d':
            start_date = end_date - timedelta(days=30)
            interval = timedelta(hours=4)
        else:
            start_date = end_date - timedelta(days=7)
            interval = timedelta(hours=1)
        
        # Generate sample candlestick data
        dates = []
        open_prices = []
        high_prices = []
        low_prices = []
        close_prices = []
        
        current_date = start_date
        last_price = 100  # Starting price
        
        while current_date <= end_date:
            dates.append(current_date)
            
            # Generate random price movement
            change = (0.5 - (random.random())) * 2  # -1 to 1
            volatility = 0.02  # 2%
            
            open_price = last_price
            close_price = open_price * (1 + change * volatility)
            high_price = max(open_price, close_price) * (1 + abs(random.random() * volatility * 0.5))
            low_price = min(open_price, close_price) * (1 - abs(random.random() * volatility * 0.5))
            
            open_prices.append(open_price)
            high_prices.append(high_price)
            low_prices.append(low_price)
            close_prices.append(close_price)
            
            last_price = close_price
            current_date += interval
        
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=dates,
            open=open_prices,
            high=high_prices,
            low=low_prices,
            close=close_prices,
            increasing_line_color='green',
            decreasing_line_color='red'
        )])
        
        fig.update_layout(
            title=f'{self.selected_token} Price Chart ({timeframe})',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            margin=dict(l=0, r=0, t=30, b=0),
            height=300,
            xaxis_rangeslider_visible=False
        )
        
        self.price_chart.update_figure(fig)
    
    def update_technical_indicators(self):
        """Update technical indicator charts."""
        if not self.selected_token:
            return
            
        # Placeholder - should calculate actual indicators from price data
        # For now, generate sample data
        
        # RSI Chart
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        rsi_values = [50 + 20 * math.sin(i/5) for i in range(30)]  # Oscillating RSI
        
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=dates, y=rsi_values, mode='lines', name='RSI'))
        
        # Add overbought/oversold lines
        fig_rsi.add_shape(type="line", x0=dates[0], y0=70, x1=dates[-1], y1=70,
                    line=dict(color="red", width=2, dash="dash"))
        fig_rsi.add_shape(type="line", x0=dates[0], y0=30, x1=dates[-1], y1=30,
                    line=dict(color="green", width=2, dash="dash"))
        
        fig_rsi.update_layout(
            title=f'RSI Indicator - {self.selected_token}',
            xaxis_title='Date',
            yaxis_title='RSI',
            yaxis_range=[0, 100],
            margin=dict(l=0, r=0, t=30, b=0),
            height=200
        )
        
        self.rsi_chart.update_figure(fig_rsi)
        
        # MACD Chart
        macd_line = [2 * math.sin(i/5) for i in range(30)]
        signal_line = [2 * math.sin((i-2)/5) for i in range(30)]
        histogram = [macd_line[i] - signal_line[i] for i in range(30)]
        
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=dates, y=macd_line, mode='lines', name='MACD'))
        fig_macd.add_trace(go.Scatter(x=dates, y=signal_line, mode='lines', name='Signal'))
        
        # Add histogram
        colors = ['green' if h > 0 else 'red' for h in histogram]
        fig_macd.add_trace(go.Bar(x=dates, y=histogram, marker_color=colors, name='Histogram'))
        
        fig_macd.update_layout(
            title=f'MACD Indicator - {self.selected_token}',
            xaxis_title='Date',
            yaxis_title='MACD',
            margin=dict(l=0, r=0, t=30, b=0),
            height=200
        )
        
        self.macd_chart.update_figure(fig_macd)
        
        # Bollinger Bands Chart
        sma = [100 + 5 * math.sin(i/10) for i in range(30)]
        upper_band = [sma[i] + 10 for i in range(30)]
        lower_band = [sma[i] - 10 for i in range(30)]
        
        fig_bb = go.Figure()
        fig_bb.add_trace(go.Scatter(x=dates, y=upper_band, mode='lines', name='Upper Band', line=dict(width=1)))
        fig_bb.add_trace(go.Scatter(x=dates, y=sma, mode='lines', name='SMA', line=dict(width=2)))
        fig_bb.add_trace(go.Scatter(x=dates, y=lower_band, mode='lines', name='Lower Band', line=dict(width=1)))
        
        # Add fill between bands
        fig_bb.add_trace(go.Scatter(
            x=dates+dates[::-1],
            y=upper_band+lower_band[::-1],
            fill='toself',
            fillcolor='rgba(0,100,80,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False
        ))
        
        fig_bb.update_layout(
            title=f'Bollinger Bands - {self.selected_token}',
            xaxis_title='Date',
            yaxis_title='Price',
            margin=dict(l=0, r=0, t=30, b=0),
            height=200
        )
        
        self.bb_chart.update_figure(fig_bb)
    
    def update_performance_chart(self, timeframe='1d'):
        """Update portfolio performance chart."""
        # Placeholder - should get actual historical portfolio values
        # Generate sample data for now
        end_date = datetime.now()
        
        if timeframe == '1d':
            start_date = end_date - timedelta(days=1)
            interval = timedelta(minutes=15)
        elif timeframe == '1w':
            start_date = end_date - timedelta(weeks=1)
            interval = timedelta(hours=2)
        elif timeframe == '1m':
            start_date = end_date - timedelta(days=30)
            interval = timedelta(days=1)
        else:
            start_date = end_date - timedelta(days=1)
            interval = timedelta(minutes=15)
        
        # Generate sample portfolio value data
        dates = []
        values = []
        
        current_date = start_date
        current_value = self.bot.portfolio.current_balance * 0.9  # Starting at 90% of current value
        
        while current_date <= end_date:
            dates.append(current_date)
            
            # Generate random value movement
            change = (0.5 - (random.random())) * 2  # -1 to 1
            volatility = 0.005  # 0.5%
            
            current_value = current_value * (1 + change * volatility)
            values.append(current_value)
            
            current_date += interval
        
        # Create line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='rgb(0, 100, 80)', width=2)
        ))
        
        # Add fill below the line
        fig.add_trace(go.Scatter(
            x=dates,
            y=[min(values) * 0.95] * len(dates),
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(0, 100, 80, 0.2)',
            line=dict(width=0),
            hoverinfo='skip',
            showlegend=False
        ))
        
        # Calculate period performance
        start_value = values[0]
        end_value = values[-1]
        period_change = ((end_value / start_value) - 1) * 100
        
        fig.update_layout(
            title=f'Portfolio Performance ({timeframe}): {period_change:+.2f}%',
            xaxis_title='Time',
            yaxis_title='Value (USD)',
            margin=dict(l=0, r=0, t=30, b=0),
            height=300
        )
        
        self.portfolio_chart.update_figure(fig)
    
    def update_asset_allocation_chart(self, holdings):
        """Update asset allocation chart."""
        # Create pie chart for asset allocation
        fig = go.Figure()
        
        labels = [asset['symbol'] for asset in holdings]
        values = [asset['value'] for asset in holdings]
        
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo='label+percent',
            insidetextorientation='radial'
        ))
        
        fig.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=250
        )
        
        self.asset_allocation_chart.update_figure(fig)
    
    def update_success_rate_chart(self):
        """Update trade success rate chart."""
        # Placeholder - should get actual trade success rate data
        # Create simple gauge chart for success rate
        success_rate = 0.65  # 65% success rate
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = success_rate * 100,
            number = {'suffix': "%", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "green" if success_rate >= 0.5 else "red"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        
        fig.update_layout(
            height=150,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        self.success_rate_chart.update_figure(fig)
    
    def update_volume_chart(self):
        """Update daily trading volume chart."""
        # Placeholder - should get actual daily volume data
        # Generate sample volume data
        days = 7
        dates = [(datetime.now() - timedelta(days=i)).strftime('%a') for i in range(days-1, -1, -1)]
        volumes = [random.uniform(1000, 5000) for _ in range(days)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates,
            y=volumes,
            marker_color='rgb(55, 83, 109)'
        ))
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=150,
            yaxis_title="Volume (USD)"
        )
        
        self.volume_chart.update_figure(fig)
    
    def update_trade_distribution_charts(self):
        """Update trade distribution charts."""
        # Placeholder - should get actual trade distribution data
        
        # Trade distribution by token
        tokens = ['SOL', 'BTC', 'ETH', 'USDC', 'BONK', 'JUP']
        trade_counts = [random.randint(5, 30) for _ in range(len(tokens))]
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=tokens,
            y=trade_counts,
            marker_color=[
                'rgb(55, 83, 109)',
                'rgb(26, 118, 255)',
                'rgb(178, 71, 0)',
                'rgb(0, 128, 128)',
                'rgb(128, 0, 128)',
                'rgb(128, 128, 0)'
            ]
        ))
        
        fig1.update_layout(
            title="Trades by Token",
            margin=dict(l=0, r=0, t=30, b=0),
            height=300,
            yaxis_title="Number of Trades"
        )
        
        self.trade_distribution_chart.update_figure(fig1)
        
        # Trade distribution by time of day
        hours = list(range(24))
        hour_labels = [f"{h:02d}:00" for h in hours]
        hour_counts = [int(15 * math.sin(h/3) + 20) for h in hours]  # Simulated distribution
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=hour_labels,
            y=hour_counts,
            marker_color='rgba(55, 83, 109, 0.7)'
        ))
        
        fig2.update_layout(
            title="Trades by Hour of Day",
            margin=dict(l=0, r=0, t=30, b=0),
            height=300,
            xaxis_title="Hour",
            yaxis_title="Number of Trades"
        )
        
        self.trade_time_distribution.update_figure(fig2)
    
    def update_resource_charts(self):
        """Update resource usage charts."""
        # CPU usage chart
        cpu_times = [datetime.fromtimestamp(t) for t, _ in self.system_metrics['cpu']]
        cpu_values = [v for _, v in self.system_metrics['cpu']]
        
        fig_cpu = go.Figure()
        fig_cpu.add_trace(go.Scatter(
            x=cpu_times,
            y=cpu_values,
            mode='lines',
            name='CPU Usage',
            line=dict(color='rgb(0, 100, 80)', width=2)
        ))
        
        fig_cpu.update_layout(
            xaxis_title='Time',
            yaxis_title='CPU Usage (%)',
            yaxis_range=[0, 100],
            margin=dict(l=0, r=0, t=0, b=0),
            height=300
        )
        
        self.cpu_chart.update_figure(fig_cpu)
        
        # Memory usage chart
        mem_times = [datetime.fromtimestamp(t) for t, _ in self.system_metrics['memory']]
        mem_values = [v for _, v in self.system_metrics['memory']]
        
        fig_mem = go.Figure()
        fig_mem.add_trace(go.Scatter(
            x=mem_times,
            y=mem_values,
            mode='lines',
            name='Memory Usage',
            line=dict(color='rgb(100, 0, 80)', width=2)
        ))
        
        fig_mem.update_layout(
            xaxis_title='Time',
            yaxis_title='Memory Usage (%)',
            yaxis_range=[0, 100],
            margin=dict(l=0, r=0, t=0, b=0),
            height=300
        )
        
        self.memory_chart.update_figure(fig_mem)
        
        # API latency chart
        latency_times = [datetime.fromtimestamp(t) for t, _ in self.system_metrics['api_latency']]
        latency_values = [v for _, v in self.system_metrics['api_latency']]
        
        fig_latency = go.Figure()
        fig_latency.add_trace(go.Scatter(
            x=latency_times,
            y=latency_values,
            mode='lines',
            name='API Latency',
            line=dict(color='rgb(80, 0, 100)', width=2)
        ))
        
        fig_latency.update_layout(
            xaxis_title='Time',
            yaxis_title='Latency (ms)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=300
        )
        
        self.latency_chart.update_figure(fig_latency)
    
    async def get_holdings(self):
        """Get portfolio holdings."""
        # Placeholder - should get actual holdings data
        # Return sample holdings for now
        holdings = [
            {
                'symbol': 'SOL',
                'amount': 10.5,
                'price': 103.42,
                'value': 1085.91,
                'change': 2.3
            },
            {
                'symbol': 'USDC',
                'amount': 5000,
                'price': 1.0,
                'value': 5000,
                'change': 0.0
            },
            {
                'symbol': 'BTC',
                'amount': 0.15,
                'price': 43250.75,
                'value': 6487.61,
                'change': -1.2
            },
            {
                'symbol': 'ETH',
                'amount': 1.2,
                'price': 3105.33,
                'value': 3726.40,
                'change': 0.8
            }
        ]
        
        return holdings
    
    async def get_market_condition(self):
        """Get current market condition assessment."""
        # Placeholder - should analyze multiple indicators for market conditions
        # Return one of: 'bullish', 'bearish', 'neutral'
        
        # Simulate changing market conditions
        seconds = int(time.time())
        if seconds % 30 < 10:
            return 'bullish'
        elif seconds % 30 < 20:
            return 'neutral'
        else:
            return 'bearish'
    
    async def get_trading_opportunities(self):
        """Get potential trading opportunities."""
        # Placeholder - should analyze tokens for opportunities
        # Return sample opportunities for now
        opportunities = [
            {
                'symbol': 'SOL',
                'score': 0.82,
                'action': 'BUY'
            },
            {
                'symbol': 'JUP',
                'score': 0.75,
                'action': 'BUY'
            },
            {
                'symbol': 'BTC',
                'score': 0.45,
                'action': 'HOLD'
            },
            {
                'symbol': 'BONK',
                'score': 0.35,
                'action': 'HOLD'
            },
            {
                'symbol': 'ETH',
                'score': 0.22,
                'action': 'SELL'
            }
        ]
        
        return opportunities

# Add necessary imports for the placeholders used above
import random
import math

async def main():
    """Main entry point for the dashboard."""
    from app.dex_bot import DexBot
    
    # Initialize the bot
    bot = DexBot()
    
    # Create and run the dashboard
    dashboard = NumerusXDashboard(bot)

if __name__ == "__main__":
    asyncio.run(main())