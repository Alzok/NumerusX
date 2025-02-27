import logging
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Tuple, Optional, Union, Set
import os
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import traceback

from app.strategy_framework import Strategy, Signal, SignalType, BacktestEngine

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("strategy_debug")

@dataclass
class DebugEvent:
    """Événement de débogage capturé pendant l'exécution d'une stratégie."""
    timestamp: float
    event_type: str  # 'signal', 'price_update', 'trade', 'error'
    strategy_name: str
    token_address: str
    timeframe: str
    data: Dict[str, Any]
    trace: Optional[str] = None

@dataclass
class DebugResult:
    """Résultat du débogage d'une stratégie."""
    strategy_name: str
    execution_time: float
    events: List[DebugEvent]
    metrics: Dict[str, Any]
    warnings: List[str]
    errors: List[str]

class StrategyDebugger:
    """
    Classe pour déboguer et analyser les performances des stratégies de trading.
    Fournit des outils pour visualiser l'exécution des stratégies et identifier les problèmes.
    """
    
    def __init__(self, output_dir: str = "debug_results"):
        """
        Initialise le débogueur de stratégie.
        
        Args:
            output_dir: Répertoire de sortie pour les résultats de débogage
        """
        self.output_dir = output_dir
        self.debug_results: Dict[str, DebugResult] = {}
        self.current_events: List[DebugEvent] = []
        self.start_time: float = 0
        
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
    async def debug_strategy(self, strategy: Strategy, price_data: Dict[str, pd.DataFrame], 
                         token_address: str) -> DebugResult:
        """
        Exécute une stratégie en mode débogage et collecte des informations détaillées.
        
        Args:
            strategy: Stratégie à déboguer
            price_data: Données de prix par timeframe
            token_address: Adresse du token
            
        Returns:
            Résultat du débogage
        """
        # Initialiser les variables de débogage
        self.current_events = []
        self.start_time = time.time()
        warnings = []
        errors = []
        
        # Monkey patch les méthodes de la stratégie pour capturer les événements
        original_generate_signal = strategy.generate_signal
        original_add_signal = strategy.add_signal
        
        # Patching generate_signal
        async def patched_generate_signal(token_addr, price_df, tf):
            try:
                start = time.time()
                signal = await original_generate_signal(token_addr, price_df, tf)
                execution_time = time.time() - start
                
                # Enregistrer l'événement
                self._add_event('signal', strategy.name, token_addr, tf, {
                    'signal_type': signal.type.value,
                    'confidence': signal.confidence,
                    'execution_time': execution_time,
                    'metadata': signal.metadata
                })
                
                # Vérifier la durée d'exécution
                if execution_time > 0.5:
                    warnings.append(f"Signal generation is slow ({execution_time:.2f}s) for {tf}")
                    
                # Vérifier la cohérence du signal
                self._check_signal_consistency(signal, price_df, warnings)
                
                return signal
            except Exception as e:
                error_msg = f"Error in generate_signal: {str(e)}"
                tb = traceback.format_exc()
                errors.append(error_msg)
                self._add_event('error', strategy.name, token_addr, tf, {'error': error_msg}, tb)
                raise
                
        # Patching add_signal
        def patched_add_signal(signal):
            try:
                original_add_signal(signal)
                self._add_event('add_signal', strategy.name, signal.token_address, signal.timeframe, {
                    'signal_type': signal.type.value,
                    'signal_count': len(strategy.signals)
                })
            except Exception as e:
                error_msg = f"Error in add_signal: {str(e)}"
                errors.append(error_msg)
                self._add_event('error', strategy.name, signal.token_address, signal.timeframe, 
                             {'error': error_msg})
                raise
                
        # Appliquer les patches
        strategy.generate_signal = lambda t, p, tf: patched_generate_signal(t, p, tf)
        strategy.add_signal = patched_add_signal
        
        # Exécuter la stratégie
        try:
            # Simuler l'exécution sur plusieurs périodes
            for timeframe, df in price_data.items():
                if timeframe in strategy.timeframes:
                    for i in range(max(20, min(50, len(df) // 10)), len(df), 10):
                        # Sélectionner une fenêtre de données
                        window = df.iloc[:i]
                        
                        # Enregistrer l'événement de mise à jour de prix
                        current_price = window['close'].iloc[-1]
                        self._add_event('price_update', strategy.name, token_address, timeframe, {
                            'price': current_price,
                            'timestamp': window.index[-1].timestamp() if hasattr(window.index[-1], 'timestamp') else time.time()
                        })
                        
                        # Générer un signal
                        await strategy.generate_signal(token_address, window, timeframe)
            
            # Exécuter un backtest pour collecter les informations de trade
            backtest_engine = BacktestEngine()
            backtest_result = await backtest_engine.run_backtest(strategy, price_data, token_address)
            
            # Enregistrer les événements de trade
            for trade in backtest_result.get('trades', []):
                self._add_event('trade', strategy.name, token_address, "backtest", trade)
                
            # Collecter les métriques
            metrics = backtest_result.get('metrics', {})
            
            # Vérifier la qualité des métriques
            self._check_backtest_metrics(metrics, warnings)
                
        except Exception as e:
            error_msg = f"Error during strategy execution: {str(e)}"
            tb = traceback.format_exc()
            errors.append(error_msg)
            self._add_event('error', strategy.name, token_address, 'global', {'error': error_msg}, tb)
        finally:
            # Restaurer les méthodes d'origine
            strategy.generate_signal = original_generate_signal
            strategy.add_signal = original_add_signal
            
        # Calculer le temps total d'exécution
        execution_time = time.time() - self.start_time
        
        # Créer le résultat du débogage
        debug_result = DebugResult(
            strategy_name=strategy.name,
            execution_time=execution_time,
            events=self.current_events,
            metrics=metrics if 'metrics' in locals() else {},
            warnings=warnings,
            errors=errors
        )
        
        # Enregistrer le résultat
        key = f"{strategy.name}_{token_address}_{int(time.time())}"
        self.debug_results[key] = debug_result
        
        # Générer le rapport de débogage
        self._generate_debug_report(debug_result, token_address, key)
        
        return debug_result
        
    def _add_event(self, event_type: str, strategy_name: str, token_address: str, timeframe: str, 
                 data: Dict[str, Any], trace: Optional[str] = None) -> None:
        """
        Ajoute un événement de débogage à la liste courante.
        
        Args:
            event_type: Type d'événement
            strategy_name: Nom de la stratégie
            token_address: Adresse du token
            timeframe: Intervalle de temps
            data: Données associées à l'événement
            trace: Trace de la pile en cas d'erreur
        """
        event = DebugEvent(
            timestamp=time.time(),
            event_type=event_type,
            strategy_name=strategy_name,
            token_address=token_address,
            timeframe=timeframe,
            data=data,
            trace=trace
        )
        self.current_events.append(event)
        
    def _check_signal_consistency(self, signal: Signal, price_data: pd.DataFrame, warnings: List[str]) -> None:
        """
        Vérifie la cohérence d'un signal par rapport aux données de prix.
        
        Args:
            signal: Signal à vérifier
            price_data: Données de prix
            warnings: Liste des avertissements à compléter
        """
        if price_data.empty:
            return
            
        current_price = price_data['close'].iloc[-1]
        
        # Vérifier les niveaux de stop-loss et take-profit
        if signal.type in (SignalType.BUY, SignalType.STRONG_BUY):
            # Pour un signal d'achat, le stop-loss devrait être inférieur au prix actuel
            if signal.stop_loss is not None and signal.stop_loss >= current_price:
                warnings.append(f"Inconsistent stop-loss for BUY signal: {signal.stop_loss} >= current price {current_price}")
                
            # Le take-profit devrait être supérieur au prix actuel
            if signal.take_profit is not None and signal.take_profit <= current_price:
                warnings.append(f"Inconsistent take-profit for BUY signal: {signal.take_profit} <= current price {current_price}")
                
        elif signal.type in (SignalType.SELL, SignalType.STRONG_SELL):
            # Pour un signal de vente, le stop-loss devrait être supérieur au prix actuel
            if signal.stop_loss is not None and signal.stop_loss <= current_price:
                warnings.append(f"Inconsistent stop-loss for SELL signal: {signal.stop_loss} <= current price {current_price}")
                
            # Le take-profit devrait être inférieur au prix actuel
            if signal.take_profit is not None and signal.take_profit >= current_price:
                warnings.append(f"Inconsistent take-profit for SELL signal: {signal.take_profit} >= current price {current_price}")
                
        # Vérifier la cohérence métadonnées/prix actuel
        if "current_price" in signal.metadata and abs(signal.metadata["current_price"] - current_price) / current_price > 0.01:
            warnings.append(f"Discrepancy between metadata price {signal.metadata['current_price']} and actual price {current_price}")
            
    def _check_backtest_metrics(self, metrics: Dict[str, Any], warnings: List[str]) -> None:
        """
        Vérifie la qualité des métriques de backtest pour identifier les problèmes potentiels.
        
        Args:
            metrics: Métriques de backtest
            warnings: Liste des avertissements à compléter
        """
        # Vérifier le nombre de trades
        trade_count = metrics.get('trade_count', 0)
        if trade_count < 5:
            warnings.append(f"Low number of trades: {trade_count}. Results may not be statistically significant.")
            
        # Vérifier le taux de réussite
        win_rate = metrics.get('win_rate', 0)
        if win_rate > 0.85:
            warnings.append(f"Suspiciously high win rate: {win_rate*100:.1f}%. Possible overfitting.")
        elif win_rate < 0.3:
            warnings.append(f"Very low win rate: {win_rate*100:.1f}%. Strategy might not be effective.")
            
        # Vérifier le drawdown maximum
        max_drawdown = metrics.get('max_drawdown', 0)
        if max_drawdown > 30:
            warnings.append(f"High maximum drawdown: {max_drawdown:.1f}%. Strategy might be too risky.")
            
        # Vérifier le ratio de Sharpe
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe < 0.5:
            warnings.append(f"Low Sharpe ratio: {sharpe:.2f}. Poor risk-adjusted return.")
            
        # Vérifier le ROI
        roi = metrics.get('total_roi', 0)
        if roi < 0:
            warnings.append(f"Negative ROI: {roi:.2f}%. Strategy is losing money.")
            
    def _generate_debug_report(self, result: DebugResult, token_address: str, key: str) -> None:
        """
        Génère un rapport de débogage au format HTML et JSON.
        
        Args:
            result: Résultat du débogage
            token_address: Adresse du token
            key: Clé unique pour le résultat
        """
        # Créer un répertoire spécifique pour ce rapport
        debug_dir = os.path.join(self.output_dir, key)
        os.makedirs(debug_dir, exist_ok=True)
        
        # Sauvegarder les données brutes au format JSON
        json_path = os.path.join(debug_dir, "debug_data.json")
        with open(json_path, 'w') as f:
            json.dump({
                "strategy_name": result.strategy_name,
                "execution_time": result.execution_time,
                "metrics": result.metrics,
                "warnings": result.warnings,
                "errors": result.errors,
                "events": [asdict(event) for event in result.events],
            }, f, indent=2)
            
        # Générer des visualisations
        self._generate_debug_visualizations(result, debug_dir)
        
        # Créer le rapport HTML
        html_path = os.path.join(debug_dir, "debug_report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self._create_html_report(result, token_address))
            
        logger.info(f"Rapport de débogage généré dans {debug_dir}")
        
    def _create_html_report(self, result: DebugResult, token_address: str) -> str:
        """
        Crée un rapport de débogage au format HTML.
        
        Args:
            result: Résultat du débogage
            token_address: Adresse du token
            
        Returns:
            Rapport HTML
        """
        # En-tête du rapport
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Debug Report - {result.strategy_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeeba; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .event {{ border-bottom: 1px solid #ddd; padding: 10px 0; }}
                .event-signal {{ background-color: #e6f7ff; }}
                .event-trade {{ background-color: #f0f7f0; }}
                .event-error {{ background-color: #fff1f0; }}
                pre {{ background-color: #f5f5f5; padding: 10px; overflow: auto; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                img {{ max-width: 100%; height: auto; margin: 20px 0; }}
                .metrics {{ display: flex; flex-wrap: wrap; }}
                .metric-card {{ background-color: #f8f9fa; border: 1px solid #eee; border-radius: 5px; margin: 10px; padding: 15px; width: calc(25% - 22px); }}
                .container {{ display: flex; flex-wrap: wrap; }}
                .chart {{ width: 50%; padding: 10px; box-sizing: border-box; }}
                @media (max-width: 768px) {{
                    .chart {{ width: 100%; }}
                    .metric-card {{ width: calc(50% - 22px); }}
                }}
            </style>
        </head>
        <body>
            <h1>Rapport de débogage pour {result.strategy_name}</h1>
            <p><strong>Token:</strong> {token_address}</p>
            <p><strong>Date:</strong> {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Temps d'exécution:</strong> {result.execution_time:.2f} secondes</p>
        """
        
        # Section métriques
        html += """
            <h2>Métriques</h2>
            <div class="metrics">
        """
        
        # Afficher les métriques dans des cartes
        for key, value in result.metrics.items():
            if isinstance(value, (int, float)):
                formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                html += f"""
                <div class="metric-card">
                    <h3>{key}</h3>
                    <p>{formatted_value}</p>
                </div>
                """
        html += "</div>"
        
        # Section avertissements
        if result.warnings:
            html += "<h2>Avertissements</h2>"
            for warning in result.warnings:
                html += f'<div class="warning">{warning}</div>'
        
        # Section erreurs
        if result.errors:
            html += "<h2>Erreurs</h2>"
            for error in result.errors:
                html += f'<div class="error">{error}</div>'
        
        # Section visualisations
        html += """
            <h2>Visualisations</h2>
            <div class="container">
                <div class="chart">
                    <img src="signal_timeline.png" alt="Timeline des signaux">
                </div>
                <div class="chart">
                    <img src="execution_time.png" alt="Temps d'exécution">
                </div>
            </div>
            <div class="container">
                <div class="chart">
                    <img src="event_distribution.png" alt="Distribution des événements">
                </div>
                <div class="chart">
                    <img src="error_analysis.png" alt="Analyse des erreurs">
                </div>
            </div>
        """
        
        # Section événements
        html += "<h2>Journal des événements</h2>"
        
        # Afficher seulement les 100 premiers événements avec pagination
        event_count = len(result.events)
        events_per_page = 100
        
        html += f"<p>Total des événements: {event_count}</p>"
        
        if event_count > events_per_page:
            html += """
            <div class="pagination">
                <button id="prev-btn" disabled>Précédent</button>
                <span id="page-info">Page 1</span>
                <button id="next-btn">Suivant</button>
            </div>
            """
        
        html += '<div id="events-container">'
        
        # Ajouter tous les événements
        for i, event in enumerate(result.events):
            display = "" if i < events_per_page else "display: none;"
            event_class = f"event event-{event.event_type}"
            timestamp = datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            html += f"""
            <div class="{event_class}" data-page="{i // events_per_page + 1}" style="{display}">
                <p><strong>{timestamp} - {event.event_type.upper()} - {event.timeframe}</strong></p>
            """
            
            # Ajouter les détails spécifiques selon le type d'événement
            if event.event_type == 'signal':
                html += f"""
                <p>Signal: {event.data.get('signal_type', 'N/A')}</p>
                <p>Confiance: {event.data.get('confidence', 'N/A')}</p>
                <p>Temps d'exécution: {event.data.get('execution_time', 0):.3f}s</p>
                <details>
                    <summary>Métadonnées</summary>
                    <pre>{json.dumps(event.data.get('metadata', {}), indent=2)}</pre>
                </details>
                """
            elif event.event_type == 'trade':
                profit_pct = event.data.get('profit_pct', 0)
                color = "green" if profit_pct > 0 else "red"
                html += f"""
                <p>Entrée: {datetime.fromtimestamp(event.data.get('entry_timestamp', 0)).strftime('%Y-%m-%d %H:%M')}</p>
                <p>Sortie: {datetime.fromtimestamp(event.data.get('exit_timestamp', 0)).strftime('%Y-%m-%d %H:%M')}</p>
                <p>Prix d'entrée: {event.data.get('entry_price', 'N/A')}</p>
                <p>Prix de sortie: {event.data.get('exit_price', 'N/A')}</p>
                <p>P&L: <span style="color: {color}">{event.data.get('profit_loss', 0):.2f} ({profit_pct:.2f}%)</span></p>
                <p>Raison: {event.data.get('exit_reason', 'N/A')}</p>
                """
            elif event.event_type == 'error':
                html += f"""
                <p>Erreur: {event.data.get('error', 'Erreur inconnue')}</p>
                """
                if event.trace:
                    html += f"""
                    <details>
                        <summary>Stack Trace</summary>
                        <pre>{event.trace}</pre>
                    </details>
                    """
            else:
                # Pour les autres types d'événements, afficher les données brutes
                html += f"""
                <details>
                    <summary>Données</summary>
                    <pre>{json.dumps(event.data, indent=2)}</pre>
                </details>
                """
                
            html += "</div>"
            
        html += "</div>"
        
        # Ajouter le JavaScript pour la pagination
        if event_count > events_per_page:
            html += """
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const prevBtn = document.getElementById('prev-btn');
                    const nextBtn = document.getElementById('next-btn');
                    const pageInfo = document.getElementById('page-info');
                    const events = document.querySelectorAll('#events-container .event');
                    
                    let currentPage = 1;
                    const totalPages = Math.ceil(events.length / 100);
                    
                    function showPage(page) {
                        events.forEach(event => {
                            const eventPage = parseInt(event.getAttribute('data-page'));
                            event.style.display = eventPage === page ? '' : 'none';
                        });
                        
                        currentPage = page;
                        pageInfo.textContent = `Page ${currentPage} / ${totalPages}`;
                        prevBtn.disabled = currentPage === 1;
                        nextBtn.disabled = currentPage === totalPages;
                    }
                    
                    prevBtn.addEventListener('click', () => {
                        if (currentPage > 1) {
                            showPage(currentPage - 1);
                        }
                    });
                    
                    nextBtn.addEventListener('click', () => {
                        if (currentPage < totalPages) {
                            showPage(currentPage + 1);
                        }
                    });
                });
            </script>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
        
    def _generate_debug_visualizations(self, result: DebugResult, output_dir: str) -> None:
        """
        Génère des visualisations pour le rapport de débogage.
        
        Args:
            result: Résultat du débogage
            output_dir: Répertoire de sortie
        """
        try:
            # Configurer le style
            plt.style.use('ggplot')
            
            # 1. Timeline des signaux
            self._plot_signal_timeline(result, os.path.join(output_dir, "signal_timeline.png"))
            
            # 2. Temps d'exécution
            self._plot_execution_time(result, os.path.join(output_dir, "execution_time.png"))
            
            # 3. Distribution des événements
            self._plot_event_distribution(result, os.path.join(output_dir, "event_distribution.png"))
            
            # 4. Analyse des erreurs
            self._plot_error_analysis(result, os.path.join(output_dir, "error_analysis.png"))
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations de débogage: {e}")
            
    def _plot_signal_timeline(self, result: DebugResult, output_path: str) -> None:
        """
        Trace une timeline des signaux générés.
        
        Args:
            result: Résultat du débogage
            output_path: Chemin de sortie pour l'image
        """
        plt.figure(figsize=(12, 6))
        
        # Collecter les signaux
        signal_events = [e for e in result.events if e.event_type == 'signal']
        
        if not signal_events:
            plt.text(0.5, 0.5, "Aucun signal généré", ha='center', va='center', fontsize=14)
            plt.tight_layout()
            plt.savefig(output_path, dpi=100)
            plt.close()
            return
            
        # Préparer les données
        timestamps = [e.timestamp for e in signal_events]
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]
        
        # Convertir les types de signaux en valeurs numériques pour le graphique
        signal_values = []
        colors = []
        
        for event in signal_events:
            signal_type = event.data.get('signal_type', 'neutral')
            confidence = event.data.get('confidence', 0.5)
            
            if signal_type in ('buy', 'strong_buy'):
                value = confidence
                color = 'green'
            elif signal_type in ('sell', 'strong_sell'):
                value = -confidence
                color = 'red'
            else:
                value = 0
                color = 'gray'
                
            signal_values.append(value)
            colors.append(color)
            
        # Tracer la timeline
        plt.scatter(dates, signal_values, c=colors, s=50, alpha=0.7)
        plt.plot(dates, signal_values, 'k--', alpha=0.3)
        
        # Ajouter des repères pour les trades
        trade_events = [e for e in result.events if e.event_type == 'trade']
        
        if trade_events:
            trade_timestamps = [e.timestamp for e in trade_events]
            trade_dates = [datetime.fromtimestamp(ts) for ts in trade_timestamps]
            trade_pnls = [e.data.get('profit_pct', 0) for e in trade_events]
            
            # Normaliser les profits pour qu'ils s'affichent bien sur le graphique
            max_signal = max(abs(min(signal_values)), abs(max(signal_values))) if signal_values else 1
            normalized_pnls = [pnl * max_signal * 0.5 / max(abs(min(trade_pnls)), abs(max(trade_pnls))) if trade_pnls else 0 
                              for pnl in trade_pnls]
            
            trade_colors = ['green' if pnl > 0 else 'red' for pnl in trade_pnls]
            
            plt.scatter(trade_dates, normalized_pnls, marker='D', c=trade_colors, s=80, alpha=0.9, label='Trades')
        
        # Formater le graphique
        plt.title('Timeline des signaux générés', fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Force du signal (-1 à 1)', fontsize=12)
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.grid(True, alpha=0.3)
        
        # Ajouter une légende
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label='Signal d\'achat'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Signal de vente'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='Signal neutre')
        ]
        
        if trade_events:
            legend_elements.append(plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='green', markersize=10, label='Trade profitable'))
            legend_elements.append(plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='red', markersize=10, label='Trade perdant'))
            
        plt.legend(handles=legend_elements, loc='best')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()
        
    def _plot_execution_time(self, result: DebugResult, output_path: str) -> None:
        """
        Trace l'évolution du temps d'exécution.
        
        Args:
            result: Résultat du débogage
            output_path: Chemin de sortie pour l'image
        """
        plt.figure(figsize=(12, 6))
        
        # Collecter les événements avec des temps d'exécution
        exec_events = [e for e in result.events if e.event_type == 'signal' and 'execution_time' in e.data]
        
        if not exec_events:
            plt.text(0.5, 0.5, "Aucune donnée de temps d'exécution", ha='center', va='center', fontsize=14)
            plt.tight_layout()
            plt.savefig(output_path, dpi=100)
            plt.close()
            return
            
        # Préparer les données
        timestamps = [e.timestamp for e in exec_events]
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]
        exec_times = [e.data.get('execution_time', 0) for e in exec_events]
        
        # Calculer les statistiques
        avg_time = sum(exec_times) / len(exec_times)
        max_time = max(exec_times)
        min_time = min(exec_times)
        
        # Tracé principal
        plt.plot(dates, exec_times, 'b-', alpha=0.7, label='Temps d\'exécution')
        
        # Ajouter une ligne pour la moyenne
        plt.axhline(y=avg_time, color='r', linestyle='-', alpha=0.7, label=f'Moyenne: {avg_time:.3f}s')
        
        # Ajouter des annotations pour les valeurs maximales
        highest_idx = exec_times.index(max_time)
        plt.annotate(f'Max: {max_time:.3f}s', 
                    xy=(dates[highest_idx], max_time),
                    xytext=(dates[highest_idx], max_time*1.15),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5),
                    ha='center', fontweight='bold')
        
        # Formater le graphique
        plt.title('Temps d\'exécution de la génération des signaux', fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Temps (secondes)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Ajouter les statistiques
        stats_text = f"Min: {min_time:.3f}s\nMoy: {avg_time:.3f}s\nMax: {max_time:.3f}s"
        plt.text(0.02, 0.95, stats_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()
        
    def _plot_event_distribution(self, result: DebugResult, output_path: str) -> None:
        """
        Trace la distribution des différents types d'événements.
        
        Args:
            result: Résultat du débogage
            output_path: Chemin de sortie pour l'image
        """
        plt.figure(figsize=(10, 8))
        
        # Compter les différents types d'événements
        event_counts = {}
        for event in result.events:
            if event.event_type not in event_counts:
                event_counts[event.event_type] = 0
            event_counts[event.event_type] += 1
            
        # Compter les différents types de signaux
        signal_types = {}
        for event in result.events:
            if event.event_type == 'signal' and 'signal_type' in event.data:
                signal_type = event.data['signal_type']
                if signal_type not in signal_types:
                    signal_types[signal_type] = 0
                signal_types[signal_type] += 1
        
        # Tracer deux graphiques
        plt.subplot(2, 1, 1)
        
        # Graphique des types d'événements
        types = list(event_counts.keys())
        counts = list(event_counts.values())
        
        # Couleurs selon le type d'événement
        colors = []
        for event_type in types:
            if event_type == 'signal':
                colors.append('blue')
            elif event_type == 'trade':
                colors.append('green')
            elif event_type == 'error':
                colors.append('red')
            elif event_type == 'price_update':
                colors.append('orange')
            else:
                colors.append('gray')
                
        plt.bar(types, counts, color=colors)
        plt.title('Distribution des types d\'événements', fontsize=14)
        plt.xlabel('Type d\'événement')
        plt.ylabel('Nombre')
        
        # Ajouter les valeurs au-dessus des barres
        for i, count in enumerate(counts):
            plt.text(i, count + 0.1, str(count), ha='center')
            
        # Graphique des types de signaux
        plt.subplot(2, 1, 2)
        
        if signal_types:
            sig_types = list(signal_types.keys())
            sig_counts = list(signal_types.values())
            
            # Couleurs selon le type de signal
            sig_colors = []
            for sig_type in sig_types:
                if sig_type in ('buy', 'strong_buy'):
                    sig_colors.append('green')
                elif sig_type in ('sell', 'strong_sell'):
                    sig_colors.append('red')
                else:
                    sig_colors.append('gray')
                    
            plt.bar(sig_types, sig_counts, color=sig_colors)
            plt.title('Distribution des types de signaux', fontsize=14)
            plt.xlabel('Type de signal')
            plt.ylabel('Nombre')
            
            # Ajouter les valeurs au-dessus des barres
            for i, count in enumerate(sig_counts):
                plt.text(i, count + 0.1, str(count), ha='center')
        else:
            plt.text(0.5, 0.5, "Aucun signal généré", ha='center', va='center', fontsize=14, transform=plt.gca().transAxes)
            
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()
        
    def _plot_error_analysis(self, result: DebugResult, output_path: str) -> None:
        """
        Analyse et trace un graphique des erreurs.
        
        Args:
            result: Résultat du débogage
            output_path: Chemin de sortie pour l'image
        """
        plt.figure(figsize=(12, 6))
        
        # Collecter les événements d'erreur
        error_events = [e for e in result.events if e.event_type == 'error']
        
        if not error_events and not result.warnings:
            plt.text(0.5, 0.5, "Aucune erreur détectée", ha='center', va='center', fontsize=14, color='green')
            plt.tight_layout()
            plt.savefig(output_path, dpi=100)
            plt.close()
            return
            
        # Créer deux sous-graphiques : un pour les erreurs, un pour les avertissements
        plt.subplot(2, 1, 1)
        
        if error_events:
            # Grouper les erreurs par type
            error_types = {}
            for event in error_events:
                error_text = event.data.get('error', 'Unknown error')
                error_type = error_text.split(':')[0] if ':' in error_text else error_text
                
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1
                
            # Tracer le graphique des erreurs
            types = list(error_types.keys())
            counts = list(error_types.values())
            
            plt.barh(types, counts, color='red', alpha=0.7)
            plt.title('Distribution des types d\'erreurs', fontsize=14)
            plt.xlabel('Nombre d\'occurrences')
            plt.ylabel('Type d\'erreur')
            
            # Ajouter les valeurs à côté des barres
            for i, count in enumerate(counts):
                plt.text(count + 0.1, i, str(count), va='center')
        else:
            plt.text(0.5, 0.5, "Aucune erreur détectée", ha='center', va='center', fontsize=14, color='green')
            
        # Tracer le graphique des avertissements
        plt.subplot(2, 1, 2)
        
        if result.warnings:
            # Grouper les avertissements par type
            warning_types = {}
            for warning in result.warnings:
                warning_type = warning.split(':')[0] if ':' in warning else warning[:30]
                
                if warning_type not in warning_types:
                    warning_types[warning_type] = 0
                warning_types[warning_type] += 1
                
            # Tracer le graphique des avertissements
            types = list(warning_types.keys())
            counts = list(warning_types.values())
            
            plt.barh(types, counts, color='orange', alpha=0.7)
            plt.title('Distribution des types d\'avertissements', fontsize=14)
            plt.xlabel('Nombre d\'occurrences')
            plt.ylabel('Type d\'avertissement')
            
            # Ajouter les valeurs à côté des barres
            for i, count in enumerate(counts):
                plt.text(count + 0.1, i, str(count), va='center')
        else:
            plt.text(0.5, 0.5, "Aucun avertissement généré", ha='center', va='center', fontsize=14, color='green')
            
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()
        
    def analyze_strategy_problems(self, result: DebugResult) -> Dict[str, Any]:
        """
        Analyse les problèmes potentiels d'une stratégie à partir des résultats de débogage.
        
        Args:
            result: Résultat du débogage
            
        Returns:
            Dictionnaire contenant l'analyse des problèmes
        """
        analysis = {
            "performance_issues": [],
            "stability_issues": [],
            "logic_issues": [],
            "recommendations": []
        }
        
        # 1. Analyser les problèmes de performance
        perf_issues = self._analyze_performance_issues(result)
        if perf_issues:
            analysis["performance_issues"] = perf_issues
            
        # 2. Analyser les problèmes de stabilité
        stability_issues = self._analyze_stability_issues(result)
        if stability_issues:
            analysis["stability_issues"] = stability_issues
            
        # 3. Analyser les problèmes logiques
        logic_issues = self._analyze_logic_issues(result)
        if logic_issues:
            analysis["logic_issues"] = logic_issues
            
        # 4. Générer des recommandations
        recommendations = self._generate_recommendations(analysis, result)
        analysis["recommendations"] = recommendations
        
        return analysis
        
    def _analyze_performance_issues(self, result: DebugResult) -> List[Dict[str, Any]]:
        """
        Analyse les problèmes de performance.
        
        Args:
            result: Résultat du débogage
            
        Returns:
            Liste des problèmes de performance
        """
        issues = []
        
        # Vérifier les temps d'exécution
        exec_events = [e for e in result.events if e.event_type == 'signal' and 'execution_time' in e.data]
        if exec_events:
            exec_times = [e.data['execution_time'] for e in exec_events]
            avg_time = sum(exec_times) / len(exec_times)
            max_time = max(exec_times) if exec_times else 0
            
            # Problème de temps d'exécution moyen élevé
            if avg_time > 0.5:
                issues.append({
                    "issue": "temps_execution_moyen_eleve",
                    "severity": "medium" if avg_time < 1.0 else "high",
                    "average_time": avg_time,
                    "details": f"Le temps d'exécution moyen pour la génération de signaux est trop long ({avg_time:.2f}s)."
                })
                
            # Problème de temps d'exécution maximal élevé
            if max_time > 1.0:
                issues.append({
                    "issue": "temps_execution_max_eleve",
                    "severity": "medium" if max_time < 2.0 else "high",
                    "max_time": max_time,
                    "details": f"Le temps d'exécution maximal pour la génération de signaux est trop long ({max_time:.2f}s)."
                })
            
            # Vérifier la variabilité des temps d'exécution
            if len(exec_times) > 3:
                std_dev = np.std(exec_times)
                if std_dev > 0.2:
                    issues.append({
                        "issue": "variabilite_temps_execution",
                        "severity": "low",
                        "std_dev": std_dev,
                        "details": f"Grande variabilité dans les temps d'exécution (écart-type: {std_dev:.2f}s)."
                    })
        
        # Vérifier l'efficacité du backtest
        if 'metrics' in result.__dict__ and result.metrics:
            trade_count = result.metrics.get('trade_count', 0)
            signal_events = [e for e in result.events if e.event_type == 'signal']
            
            # Ratio signaux par trade
            if trade_count > 0 and signal_events:
                signal_trade_ratio = len(signal_events) / trade_count
                if signal_trade_ratio > 10:
                    issues.append({
                        "issue": "ratio_signaux_trades_eleve",
                        "severity": "medium",
                        "ratio": signal_trade_ratio,
                        "details": f"La stratégie génère beaucoup de signaux ({len(signal_events)}) pour peu de trades ({trade_count})."
                    })
        
        return issues
        
    def _analyze_stability_issues(self, result: DebugResult) -> List[Dict[str, Any]]:
        """
        Analyse les problèmes de stabilité.
        
        Args:
            result: Résultat du débogage
            
        Returns:
            Liste des problèmes de stabilité
        """
        issues = []
        
        # Vérifier les erreurs
        error_events = [e for e in result.events if e.event_type == 'error']
        if error_events:
            error_types = {}
            for event in error_events:
                error_text = event.data.get('error', 'Unknown error')
                error_type = error_text.split(':')[0] if ':' in error_text else error_text
                
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1
                
            for error_type, count in error_types.items():
                severity = "high" if count > 5 else "medium" if count > 2 else "low"
                issues.append({
                    "issue": "erreurs_frequentes",
                    "severity": severity,
                    "error_type": error_type,
                    "count": count,
                    "details": f"La stratégie a rencontré {count} erreurs de type '{error_type}'."
                })
        
        # Vérifier les crashs dans la génération de signaux
        signal_timeframes = set()
        for event in result.events:
            if event.event_type == 'signal':
                signal_timeframes.add(event.timeframe)
        
        price_timeframes = set()
        for event in result.events:
            if event.event_type == 'price_update':
                price_timeframes.add(event.timeframe)
        
        # Vérifier s'il y a des timeframes avec des mises à jour de prix mais sans signaux
        missing_signals = price_timeframes - signal_timeframes
        if missing_signals:
            issues.append({
                "issue": "timeframes_sans_signaux",
                "severity": "medium",
                "timeframes": list(missing_signals),
                "details": f"Certains timeframes ({', '.join(missing_signals)}) ont reçu des données de prix mais n'ont pas généré de signaux."
            })
                
        return issues
        
    def _analyze_logic_issues(self, result: DebugResult) -> List[Dict[str, Any]]:
        """
        Analyse les problèmes logiques dans la stratégie.
        
        Args:
            result: Résultat du débogage
            
        Returns:
            Liste des problèmes logiques
        """
        issues = []
        
        # Analyser les avertissements
        if result.warnings:
            warning_types = {}
            for warning in result.warnings:
                warning_type = warning.split(':')[0] if ':' in warning else warning[:30]
                
                if warning_type not in warning_types:
                    warning_types[warning_type] = []
                warning_types[warning_type].append(warning)
                
            for warning_type, warnings_list in warning_types.items():
                count = len(warnings_list)
                severity = "high" if count > 5 else "medium" if count > 2 else "low"
                issues.append({
                    "issue": "avertissements_frequents",
                    "severity": severity,
                    "warning_type": warning_type,
                    "count": count,
                    "examples": warnings_list[:3],  # Limiter à 3 exemples
                    "details": f"La stratégie a généré {count} avertissements de type '{warning_type}'."
                })
        
        # Analyser la cohérence des signaux
        buy_signals = 0
        sell_signals = 0
        neutral_signals = 0
        
        for event in result.events:
            if event.event_type == 'signal' and 'signal_type' in event.data:
                signal_type = event.data['signal_type']
                if signal_type in ('buy', 'strong_buy'):
                    buy_signals += 1
                elif signal_type in ('sell', 'strong_sell'):
                    sell_signals += 1
                else:
                    neutral_signals += 1
        
        total_signals = buy_signals + sell_signals + neutral_signals
        
        if total_signals > 10:  # Seulement si nous avons suffisamment de signaux
            # Vérifier le ratio achat/vente
            if buy_signals > 0 and sell_signals > 0:
                buy_sell_ratio = max(buy_signals, sell_signals) / min(buy_signals, sell_signals)
                if buy_sell_ratio > 5:  # Si un type est 5x plus fréquent que l'autre
                    dominant_type = "d'achat" if buy_signals > sell_signals else "de vente"
                    issues.append({
                        "issue": "desequilibre_signaux",
                        "severity": "medium",
                        "buy_signals": buy_signals,
                        "sell_signals": sell_signals,
                        "ratio": buy_sell_ratio,
                        "details": f"Déséquilibre important entre les signaux d'achat et de vente. Les signaux {dominant_type} sont {buy_sell_ratio:.1f}x plus fréquents."
                    })
            
            # Vérifier les signaux neutres excessifs
            if neutral_signals > 0:
                neutral_ratio = neutral_signals / total_signals
                if neutral_ratio > 0.7:  # Plus de 70% de signaux neutres
                    issues.append({
                        "issue": "exces_signaux_neutres",
                        "severity": "medium",
                        "neutral_ratio": neutral_ratio,
                        "details": f"La stratégie génère un pourcentage élevé ({neutral_ratio*100:.1f}%) de signaux neutres."
                    })
        
        # Analyser les trades
        trade_events = [e for e in result.events if e.event_type == 'trade']
        if trade_events:
            # Calculer la durée des trades
            trade_durations = []
            for trade in trade_events:
                if 'entry_timestamp' in trade.data and 'exit_timestamp' in trade.data:
                    duration = trade.data['exit_timestamp'] - trade.data['entry_timestamp']
                    trade_durations.append(duration)
            
            # Vérifier les trades très courts
            if trade_durations:
                short_trades = [d for d in trade_durations if d < 60*5]  # Moins de 5 minutes
                if short_trades and len(short_trades) / len(trade_durations) > 0.2:  # Plus de 20% sont courts
                    issues.append({
                        "issue": "trades_tres_courts",
                        "severity": "medium",
                        "count": len(short_trades),
                        "percentage": len(short_trades) / len(trade_durations) * 100,
                        "details": f"{len(short_trades)} trades ({len(short_trades)/len(trade_durations)*100:.1f}%) ont duré moins de 5 minutes."
                    })
                
                # Vérifier les trades très longs
                long_trades = [d for d in trade_durations if d > 60*60*24*3]  # Plus de 3 jours
                if long_trades and len(long_trades) / len(trade_durations) > 0.2:  # Plus de 20% sont longs
                    issues.append({
                        "issue": "trades_tres_longs",
                        "severity": "low",
                        "count": len(long_trades),
                        "percentage": len(long_trades) / len(trade_durations) * 100,
                        "details": f"{len(long_trades)} trades ({len(long_trades)/len(trade_durations)*100:.1f}%) ont duré plus de 3 jours."
                    })
        
        return issues
        
    def _generate_recommendations(self, analysis: Dict[str, Any], result: DebugResult) -> List[str]:
        """
        Génère des recommandations basées sur l'analyse des problèmes.
        
        Args:
            analysis: Analyse des problèmes
            result: Résultat du débogage
            
        Returns:
            Liste des recommandations
        """
        recommendations = []
        
        # Recommandations pour les problèmes de performance
        if analysis["performance_issues"]:
            for issue in analysis["performance_issues"]:
                if issue["issue"] == "temps_execution_moyen_eleve":
                    recommendations.append(
                        f"Optimiser le code de génération des signaux pour réduire le temps d'exécution moyen (actuellement {issue['average_time']:.2f}s)."
                    )
                elif issue["issue"] == "temps_execution_max_eleve":
                    recommendations.append(
                        f"Identifier et optimiser les cas particuliers qui causent des temps d'exécution élevés (max: {issue['max_time']:.2f}s)."
                    )
                elif issue["issue"] == "ratio_signaux_trades_eleve":
                    recommendations.append(
                        f"Réviser les critères d'entrée/sortie pour réduire le nombre de signaux qui ne mènent pas à des trades."
                    )
            
        # Recommandations pour les problèmes de stabilité
        if analysis["stability_issues"]:
            for issue in analysis["stability_issues"]:
                if issue["issue"] == "erreurs_frequentes":
                    recommendations.append(
                        f"Corriger les erreurs de type '{issue['error_type']}' qui se produisent fréquemment."
                    )
                elif issue["issue"] == "timeframes_sans_signaux":
                    recommendations.append(
                        f"Vérifier pourquoi les timeframes {', '.join(issue['timeframes'])} ne génèrent pas de signaux."
                    )
        
        # Recommandations pour les problèmes logiques
        if analysis["logic_issues"]:
            for issue in analysis["logic_issues"]:
                if issue["issue"] == "avertissements_frequents":
                    recommendations.append(
                        f"Résoudre les avertissements de type '{issue['warning_type']}' qui apparaissent {issue['count']} fois."
                    )
                elif issue["issue"] == "desequilibre_signaux":
                    recommendations.append(
                        f"Rééquilibrer la génération des signaux d'achat et de vente qui présentent un ratio de {issue['ratio']:.1f}."
                    )
                elif issue["issue"] == "exces_signaux_neutres":
                    recommendations.append(
                        f"Affiner les conditions de génération des signaux pour réduire le pourcentage de signaux neutres ({issue['neutral_ratio']*100:.1f}%)."
                    )
                elif issue["issue"] == "trades_tres_courts":
                    recommendations.append(
                        f"Ajuster les paramètres de sortie pour éviter les trades très courts ({issue['percentage']:.1f}% durent moins de 5 minutes)."
                    )
        
        # Recommandations générales
        if not recommendations:
            recommendations.append("Aucun problème majeur détecté. La stratégie semble bien fonctionner.")
        else:
            # Ajouter une recommandation de tests supplémentaires
            recommendations.append(
                "Effectuer des tests de backtest supplémentaires sur différentes périodes et conditions de marché pour valider les améliorations."
            )
        
        return recommendations
