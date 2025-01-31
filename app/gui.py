from nicegui import ui
from typing import Optional
from config import Config
import time

class TradingGUI:
    def __init__(self, bot):
        self.bot = bot
        self.log: Optional[ui.log] = None
        self.stats = {
            'status': '🟢 En ligne',
            'last_check': time.strftime('%H:%M:%S'),
            'active_pairs': 0
        }
        
    def create_interface(self):
        """Interface utilisateur avec métriques en temps réel"""
        with ui.header().classes('bg-blue-800 text-white p-4 shadow-lg'):
            ui.label('NumerusX Pro').classes('text-2xl font-bold')
            
        with ui.row().classes('w-full p-4 gap-4'):
            # Panneau de contrôle
            with ui.column().classes('w-1/4 space-y-4'):
                ui.switch('Mode Auto', value=True).bind_to(self.bot, 'active')
                ui.number('Risque (%)', min=0.1, max=5.0, step=0.1).bind_to(self.bot.risk_engine, 'risk_percent')
                with ui.row().classes('space-x-2'):
                    ui.button('Démarrer', on_click=self.bot.run).classes('bg-green-600 hover:bg-green-700')
                    ui.button('Arrêt Urgence', on_click=self.bot.stop).classes('bg-red-600 hover:bg-red-700')
                ui.linear_progress().bind_value_from(self.bot.portfolio, 'current_balance', 
                    backward=lambda v: v / Config.INITIAL_BALANCE)
            
            # Section des logs
            with ui.column().classes('w-3/4'):
                self.log = ui.log().classes('h-96 bg-gray-100 rounded p-4 font-mono text-sm')
                
        # Pied de page avec statistiques
        with ui.footer().classes('bg-gray-100 p-3 flex justify-between items-center'):
            ui.label().bind_text_from(self.stats, 'status')
            ui.label().bind_text_from(self.stats, 'last_check', 
                backward=lambda x: f"Dernière mise à jour: {x}")
            ui.label().bind_text_from(self.stats, 'active_pairs',
                backward=lambda x: f"Paires actives: {x}")