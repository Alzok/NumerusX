from nicegui import ui
from typing import Optional
import pandas as pd

class TradingDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.log_view: Optional[ui.log] = None
        
    def create(self):
        with ui.header().classes('bg-blue-800 text-white p-4'):
            ui.label('NumerusX Trading Platform').classes('text-2xl')
            
        with ui.row().classes('w-full p-4'):
            # Contrôles
            with ui.column().classes('w-1/4'):
                ui.switch('Auto Trading', value=False).bind_to(self.bot, 'auto_trade')
                ui.number('Risk %', min=0.1, max=5.0, step=0.1).bind_to(self.bot, 'risk_percent')
                ui.button('Start', on_click=self.bot.start).classes('bg-green-500')
                ui.button('Emergency Stop', on_click=self.bot.stop).classes('bg-red-500')
            
            # Logs
            with ui.column().classes('w-3/4'):
                self.log_view = ui.log().classes('h-96 w-full bg-gray-100 p-4 overflow-auto')
        
        # Statistiques
        with ui.footer().classes('bg-gray-100 p-2'):
            ui.label().bind_text_from(self.bot, 'status', 
                backward=lambda x: f"Status: {x} | Last Update: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")