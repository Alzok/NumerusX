from nicegui import ui
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict

class TradingDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.init_ui()
        ui.timer(2.0, self.update_dashboard)

    def init_ui(self):
        """Interface utilisateur optimisée"""
        with ui.header().classes('bg-gray-800 text-white p-4 flex items-center'):
            ui.icon('rocket', size='lg').classes('mr-2')
            ui.label('NumerusX Trading Bot').classes('text-xl font-bold')
            ui.space()
            self.status_indicator = ui.icon('circle', size='sm', color='red').tooltip('Statut du bot')
            ui.button(icon='refresh', on_click=self.update_dashboard).props('flat')

        with ui.row().classes('w-full h-[calc(100vh-80px)] p-4 gap-4'):
            # Colonne de contrôle
            with ui.column().classes('w-1/4 space-y-4'):
                self._build_control_panel()
                self._build_risk_panel()
            
            # Colonne principale
            with ui.column().classes('w-3/4 space-y-4'):
                self._build_performance_section()
                self._build_active_trades()

    def _build_control_panel(self):
        """Panneau de contrôle principal"""
        with ui.card().classes('w-full p-4 bg-gray-50'):
            ui.label('Contrôle du Bot').classes('text-lg font-semibold mb-4')
            
            self.toggle_btn = ui.button(
                'Démarrer le Bot', 
                on_click=self.toggle_bot,
                icon='play_arrow'
            ).props('unelevated color=green').classes('w-full')
            
            ui.button(
                'Arrêt d\'Urgence', 
                on_click=self.bot.stop,
                icon='stop'
            ).props('color=red').classes('w-full')

            ui.separator().classes('my-4')
            
            with ui.row().classes('w-full items-center'):
                ui.icon('speed', size='sm', color='blue')
                ui.slider(
                    min=1, 
                    max=5, 
                    value=3
                ).bind_value(self.bot, 'speed').classes('grow')

    def _build_risk_panel(self):
        """Panneau de gestion des risques"""
        with ui.card().classes('w-full p-4 bg-gray-50'):
            ui.label('Paramètres de Risque').classes('text-lg font-semibold mb-2')
            
            with ui.row().classes('items-center justify-between'):
                ui.label('Exposition Max:')
                ui.number(
                    value=20, 
                    min=5, 
                    max=100, 
                    format='%d%%'
                ).bind_value(self.bot.risk_engine, 'max_exposure').classes('w-20')
            
            with ui.row().classes('items-center justify-between'):
                ui.label('Stop-Loss Auto:')
                ui.switch().bind_value(self.bot.risk_engine, 'auto_stop_loss')
            
            ui.separator().classes('my-3')
            
            with ui.row().classes('text-xs justify-between'):
                ui.label('Risque Actuel:')
                ui.label().bind_text_from(
                    self.bot.risk_engine,
                    'current_risk',
                    backward=lambda v: f'{v}/100'
                )

    def _build_performance_section(self):
        """Section des performances"""
        with ui.card().classes('w-full p-4'):
            # Métriques clés
            with ui.grid(columns=3).classes('w-full gap-4 mb-4'):
                self._create_metric('Portefeuille', 'total_balance', '€')
                self._create_metric('Profit Journalier', 'daily_pnl', '%')
                self._create_metric('Trades Actifs', 'active_trades', '')
            
            # Graphique de performance
            self.performance_chart = ui.plotly().classes('w-full h-64')

    def _build_active_trades(self):
        """Liste des trades actifs"""
        with ui.card().classes('w-full p-4'):
            ui.label('Trades en Cours').classes('text-lg font-semibold mb-2')
            
            columns = [
                {'name': 'pair', 'label': 'Paire', 'field': 'pair', 'align': 'left'},
                {'name': 'side', 'label': 'Type', 'field': 'side'},
                {'name': 'size', 'label': 'Montant', 'field': 'size'},
                {'name': 'entry', 'label': 'Prix Entrée', 'field': 'entry'},
                {'name': 'current', 'label': 'Prix Actuel', 'field': 'current'},
                {'name': 'pnl', 'label': 'P&L', 'field': 'pnl'}
            ]
            
            self.trades_table = ui.table(
                columns=columns,
                rows=[],
                pagination=5,
                row_key='id'
            ).classes('w-full').props('dense flat')

    def _create_metric(self, title: str, metric: str, suffix: str):
        """Crée une carte métrique standardisée"""
        with ui.card().classes('p-2 text-center').props('flat'):
            ui.label(title).classes('text-xs text-gray-500 mb-1')
            ui.label().bind_text_from(
                self.bot.performance,
                metric,
                backward=lambda v: f'{v}{suffix}' if isinstance(v, (int, float)) else v
            ).classes('text-2xl font-bold')
            ui.label().bind_text_from(
                self.bot.performance,
                f'{metric}_delta',
                backward=lambda v: f'({v:+}{suffix})' if v else ''
            ).classes('text-xs').style('color: $positive' if '+ ' in suffix else '')

    def toggle_bot(self):
        """Bascule l'état du bot"""
        if self.bot.active:
            self.bot.stop()
            self.toggle_btn.text('Démarrer le Bot')
            self.toggle_btn.props('color=green icon=play_arrow')
        else:
            self.bot.run()
            self.toggle_btn.text('Arrêter le Bot')
            self.toggle_btn.props('color=red icon=stop')

    def update_dashboard(self):
        """Met à jour toutes les données du dashboard"""
        try:
            # Mettre à jour le statut
            self.status_indicator.props(f'color={"green" if self.bot.active else "red"}')
            
            # Mettre à jour le tableau des trades
            self.trades_table.rows = self._format_trades(self.bot.active_trades)
            
            # Mettre à jour le graphique
            self._update_performance_chart()
            
        except Exception as e:
            ui.notify(f"Erreur de mise à jour: {str(e)}", type='negative')

    def _format_trades(self, trades: List[Dict]) -> List[Dict]:
        """Formate les trades pour le tableau"""
        return [{
            'id': t['id'],
            'pair': t['pair'],
            'side': 'Achat' if t['amount'] > 0 else 'Vente',
            'size': f"€{abs(t['amount']):.2f}",
            'entry': f"€{t['entry_price']:.2f}",
            'current': f"€{self._get_current_price(t['pair']):.2f}",
            'pnl': self._calculate_pnl(t)
        } for t in trades]

    def _calculate_pnl(self, trade: Dict) -> str:
        """Calcule le P&L formaté"""
        current_price = self._get_current_price(trade['pair'])
        pct = ((current_price - trade['entry_price']) / trade['entry_price']) * 100
        color = 'green' if pct >= 0 else 'red'
        return f'<span style="color: {color}">{pct:+.2f}%</span>'

    def _get_current_price(self, pair: str) -> float:
        """Récupère le prix actuel depuis l'API"""
        return self.bot.dex_api.get_price(pair)

    def _update_performance_chart(self):
        """Met à jour le graphique de performance"""
        history = self.bot.performance.history
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=[h['timestamp'] for h in history],
            y=[h['value'] for h in history],
            mode='lines',
            name='Valeur Portefeuille',
            line=dict(color='#4CAF50', width=2)
        ))
        
        fig.update_layout(
            margin={'t': 20, 'b': 30, 'l': 40, 'r': 20},
            height=250,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#eeeeee')
        )
        
        self.performance_chart.update_figure(fig)