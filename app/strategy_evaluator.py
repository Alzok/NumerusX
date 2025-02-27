import logging
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime
import json
import asyncio
from dataclasses import dataclass
from app.strategy_framework import Strategy, Signal, StrategyMetrics, BacktestEngine

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("strategy_evaluator")

@dataclass
class EvaluationResult:
    """Résultat d'une évaluation de stratégie."""
    strategy_name: str
    metrics: StrategyMetrics
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]
    token_address: str
    timeframe: str
    timestamp: float
    signals: List[Signal]

class StrategyEvaluator:
    """
    Classe principale pour l'évaluation des performances des stratégies de trading.
    Fournit des fonctionnalités avancées d'analyse et de visualisation.
    """
    
    def __init__(self, output_dir: str = "evaluation_results"):
        """
        Initialise l'évaluateur de stratégie.
        
        Args:
            output_dir: Répertoire de sortie pour les résultats
        """
        self.output_dir = output_dir
        self.results: Dict[str, EvaluationResult] = {}
        self.backtest_engine = BacktestEngine()
        
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
    async def evaluate_strategy(self, strategy: Strategy, price_data: Dict[str, pd.DataFrame], 
                            token_address: str) -> EvaluationResult:
        """
        Évalue une stratégie sur des données historiques.
        
        Args:
            strategy: Stratégie à évaluer
            price_data: Données de prix historiques par timeframe
            token_address: Adresse du token
            
        Returns:
            Résultat de l'évaluation
        """
        # Exécuter le backtest
        backtest_result = await self.backtest_engine.run_backtest(strategy, price_data, token_address)
        
        # Regrouper les données des différents timeframes
        combined_timeframe = "+".join(sorted(price_data.keys()))
        
        # Collecter les signaux générés
        signals = []
        for timeframe, df in price_data.items():
            if timeframe in strategy.timeframes:
                for i in range(min(10, len(df))):  # Prendre les 10 plus récentes périodes
                    idx = len(df) - 1 - i
                    if idx >= 0:
                        signal = await strategy.generate_signal(
                            token_address, df.iloc[:idx+1], timeframe)
                        signals.append(signal)
                        
        # Calculer les métriques de performance
        metrics = await self._calculate_strategy_metrics(backtest_result)
        
        # Créer le résultat
        result = EvaluationResult(
            strategy_name=strategy.name,
            metrics=metrics,
            trades=backtest_result["trades"],
            equity_curve=backtest_result["equity_curve"],
            token_address=token_address,
            timeframe=combined_timeframe,
            timestamp=time.time(),
            signals=signals
        )
        
        # Enregistrer le résultat pour référence future
        self.results[f"{strategy.name}_{token_address}"] = result
        
        return result
        
    async def compare_strategies(self, strategies: List[Strategy], price_data: Dict[str, pd.DataFrame], 
                             token_address: str) -> Dict[str, Any]:
        """
        Compare plusieurs stratégies sur les mêmes données.
        
        Args:
            strategies: Liste des stratégies à comparer
            price_data: Données de prix historiques
            token_address: Adresse du token
            
        Returns:
            Résultats de la comparaison
        """
        results = {}
        
        # Évaluer chaque stratégie
        for strategy in strategies:
            result = await self.evaluate_strategy(strategy, price_data, token_address)
            results[strategy.name] = result
            
        # Générer une analyse comparative
        comparison = self._compare_results(results)
        
        return {
            "individual_results": results,
            "comparison": comparison
        }
        
    def _compare_results(self, results: Dict[str, EvaluationResult]) -> Dict[str, Any]:
        """
        Compare les résultats de plusieurs stratégies.
        
        Args:
            results: Dictionnaire des résultats par stratégie
            
        Returns:
            Analyse comparative
        """
        comparison = {
            "roi": {},
            "sharpe": {},
            "max_drawdown": {},
            "win_rate": {},
            "profit_factor": {},
            "trade_count": {}
        }
        
        # Collecter les métriques par stratégie
        for name, result in results.items():
            comparison["roi"][name] = result.metrics.roi
            comparison["sharpe"][name] = result.metrics.sharpe_ratio
            comparison["max_drawdown"][name] = result.metrics.max_drawdown
            comparison["win_rate"][name] = result.metrics.win_rate
            comparison["profit_factor"][name] = result.metrics.profit_factor
            comparison["trade_count"][name] = result.metrics.total_trades
            
        # Déterminer la meilleure stratégie selon différentes métriques
        best_strategy = {
            "roi": max(comparison["roi"].items(), key=lambda x: x[1])[0],
            "sharpe": max(comparison["sharpe"].items(), key=lambda x: x[1])[0],
            "max_drawdown": min(comparison["max_drawdown"].items(), key=lambda x: x[1])[0],
            "win_rate": max(comparison["win_rate"].items(), key=lambda x: x[1])[0],
            "profit_factor": max(comparison["profit_factor"].items(), key=lambda x: x[1])[0],
        }
        
        # Calculer un score composite pour chaque stratégie
        composite_scores = {}
        for name in results.keys():
            # Formule de score composite pondérée
            score = (
                comparison["roi"][name] * 0.3 +
                comparison["sharpe"][name] * 0.2 +
                (1 - comparison["max_drawdown"][name]) * 0.2 +
                comparison["win_rate"][name] * 0.15 +
                min(comparison["profit_factor"][name], 5) / 5 * 0.15  # Limiter l'impact des valeurs aberrantes
            )
            composite_scores[name] = score
            
        best_overall = max(composite_scores.items(), key=lambda x: x[1])[0]
        
        return {
            "metrics_by_strategy": comparison,
            "best_by_metric": best_strategy,
            "composite_scores": composite_scores,
            "best_overall": best_overall
        }
        
    async def _calculate_strategy_metrics(self, backtest_result: Dict[str, Any]) -> StrategyMetrics:
        """
        Calcule les métriques de performance à partir d'un résultat de backtest.
        
        Args:
            backtest_result: Résultat du backtest
            
        Returns:
            Métriques de la stratégie
        """
        # Extraire les métriques du résultat de backtest
        metrics = backtest_result.get("metrics", {})
        trades = backtest_result.get("trades", [])
        
        # Calculer le win rate
        if trades:
            win_count = sum(1 for trade in trades if trade.get("profit_pct", 0) > 0)
            win_rate = win_count / len(trades)
        else:
            win_rate = 0.0
            
        # Calculer le profit factor
        profits = sum(max(0, trade.get("profit_loss", 0)) for trade in trades)
        losses = sum(abs(min(0, trade.get("profit_loss", 0))) for trade in trades)
        profit_factor = profits / losses if losses > 0 else float('inf')
        
        # Calcul de la durée moyenne des trades
        if trades:
            durations = []
            for trade in trades:
                if "entry_timestamp" in trade and "exit_timestamp" in trade:
                    duration = trade["exit_timestamp"] - trade["entry_timestamp"]
                    durations.append(duration)
            avg_duration = sum(durations) / len(durations) if durations else 0
        else:
            avg_duration = 0
        
        # Créer l'objet StrategyMetrics
        return StrategyMetrics(
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=metrics.get("sharpe_ratio", 0),
            max_drawdown=metrics.get("max_drawdown", 0),
            avg_trade_duration=avg_duration,
            total_trades=len(trades),
            profitable_trades=sum(1 for trade in trades if trade.get("profit_pct", 0) > 0),
            roi=metrics.get("total_roi", 0)
        )
        
    def generate_report(self, result: EvaluationResult, save_html: bool = True) -> str:
        """
        Génère un rapport détaillé pour une stratégie évaluée.
        
        Args:
            result: Résultat de l'évaluation
            save_html: Si True, sauvegarde le rapport au format HTML
            
        Returns:
            Rapport au format markdown
        """
        # Créer le rapport en markdown
        report = f"# Rapport d'évaluation: {result.strategy_name}\n\n"
        report += f"## Synthèse\n\n"
        report += f"- **Token**: {result.token_address}\n"
        report += f"- **Timeframe**: {result.timeframe}\n"
        report += f"- **Date d'évaluation**: {datetime.fromtimestamp(result.timestamp).strftime('%Y-%m-%d %H:%M')}\n\n"
        
        report += f"## Métriques de performance\n\n"
        report += f"- ROI: **{result.metrics.roi:.2f}%**\n"
        report += f"- Ratio de Sharpe: **{result.metrics.sharpe_ratio:.2f}**\n"
        report += f"- Drawdown maximum: **{result.metrics.max_drawdown:.2f}%**\n"
        report += f"- Taux de réussite: **{result.metrics.win_rate*100:.2f}%**\n"
        report += f"- Facteur de profit: **{result.metrics.profit_factor:.2f}**\n"
        report += f"- Nombre de trades: **{result.metrics.total_trades}**\n"
        report += f"- Trades profitables: **{result.metrics.profitable_trades}**\n"
        report += f"- Durée moyenne des trades: **{result.metrics.avg_trade_duration/3600:.2f} heures**\n\n"
        
        # Générer les visualisations
        self._generate_visualizations(result)
        
        report += f"## Visualisations\n\n"
        report += f"### Courbe d'équité\n\n"
        report += f"![Courbe d'équité]({self._get_file_path(result, 'equity_curve.png', url=True)})\n\n"
        
        report += f"### Distribution des profits/pertes\n\n"
        report += f"![Distribution P&L]({self._get_file_path(result, 'pnl_distribution.png', url=True)})\n\n"
        
        report += f"### Performance mensuelle\n\n"
        report += f"![Performance mensuelle]({self._get_file_path(result, 'monthly_performance.png', url=True)})\n\n"
        
        # Ajouter des détails sur les trades
        report += f"## Détails des trades\n\n"
        
        # Tableau des 10 meilleurs trades
        if result.trades:
            best_trades = sorted(result.trades, key=lambda t: t.get("profit_pct", 0), reverse=True)[:10]
            report += "### Top 10 des meilleurs trades\n\n"
            report += "| Date d'entrée | Date de sortie | P&L | P&L % | Raison de sortie |\n"
            report += "|--------------|--------------|-----|-------|------------------|\n"
            
            for trade in best_trades:
                entry_date = datetime.fromtimestamp(trade.get("entry_timestamp", 0)).strftime('%Y-%m-%d %H:%M')
                exit_date = datetime.fromtimestamp(trade.get("exit_timestamp", 0)).strftime('%Y-%m-%d %H:%M')
                profit_loss = trade.get("profit_loss", 0)
                profit_pct = trade.get("profit_pct", 0)
                exit_reason = trade.get("exit_reason", "signal")
                
                report += f"| {entry_date} | {exit_date} | ${profit_loss:.2f} | {profit_pct:.2f}% | {exit_reason} |\n"
                
            report += "\n"
            
            # Tableau des 10 pires trades
            worst_trades = sorted(result.trades, key=lambda t: t.get("profit_pct", 0))[:10]
            report += "### Top 10 des pires trades\n\n"
            report += "| Date d'entrée | Date de sortie | P&L | P&L % | Raison de sortie |\n"
            report += "|--------------|--------------|-----|-------|------------------|\n"
            
            for trade in worst_trades:
                entry_date = datetime.fromtimestamp(trade.get("entry_timestamp", 0)).strftime('%Y-%m-%d %H:%M')
                exit_date = datetime.fromtimestamp(trade.get("exit_timestamp", 0)).strftime('%Y-%m-%d %H:%M')
                profit_loss = trade.get("profit_loss", 0)
                profit_pct = trade.get("profit_pct", 0)
                exit_reason = trade.get("exit_reason", "signal")
                
                report += f"| {entry_date} | {exit_date} | ${profit_loss:.2f} | {profit_pct:.2f}% | {exit_reason} |\n"
                
            report += "\n"
            
        # Informations sur les signaux
        report += f"## Analyse des signaux\n\n"
        signal_counts = self._analyze_signals(result.signals)
        
        report += "### Répartition des signaux\n\n"
        report += "| Type de signal | Nombre | Confiance moyenne |\n"
        report += "|---------------|--------|------------------|\n"
        
        for signal_type, data in signal_counts.items():
            report += f"| {signal_type} | {data['count']} | {data['avg_confidence']:.2f} |\n"
            
        # Sauvegarder le rapport
        report_path = self._get_file_path(result, "report.md")
        with open(report_path, 'w') as f:
            f.write(report)
            
        # Convertir en HTML si demandé
        if save_html:
            try:
                import markdown
                html = markdown.markdown(report, extensions=['tables', 'fenced_code'])
                
                # Ajouter un peu de style CSS
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Rapport: {result.strategy_name}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                        h1, h2, h3 {{ color: #333; }}
                        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                        th {{ background-color: #f2f2f2; }}
                        img {{ max-width: 100%; height: auto; }}
                        .metric {{ font-weight: bold; }}
                    </style>
                </head>
                <body>
                {html}
                </body>
                </html>
                """
                
                html_path = self._get_file_path(result, "report.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                    
                logger.info(f"Rapport HTML généré: {html_path}")
                
            except ImportError:
                logger.warning("Package 'markdown' non disponible, rapport HTML non généré")
                
        logger.info(f"Rapport Markdown généré: {report_path}")
        return report
    
    def _analyze_signals(self, signals: List[Signal]) -> Dict[str, Dict[str, Any]]:
        """
        Analyse les signaux générés par la stratégie.
        
        Args:
            signals: Liste des signaux
            
        Returns:
            Statistiques sur les signaux
        """
        signal_counts = {}
        
        for signal in signals:
            signal_type = signal.type.value
            if signal_type not in signal_counts:
                signal_counts[signal_type] = {"count": 0, "total_confidence": 0, "signals": []}
                
            signal_counts[signal_type]["count"] += 1
            signal_counts[signal_type]["total_confidence"] += signal.confidence
            signal_counts[signal_type]["signals"].append(signal)
            
        # Calculer la confiance moyenne pour chaque type de signal
        for signal_type, data in signal_counts.items():
            data["avg_confidence"] = data["total_confidence"] / data["count"] if data["count"] > 0 else 0
            
        return signal_counts
    
    def _generate_visualizations(self, result: EvaluationResult) -> None:
        """
        Génère des visualisations pour le rapport.
        
        Args:
            result: Résultat de l'évaluation
        """
        try:
            # Utiliser seaborn pour un meilleur style
            sns.set(style="whitegrid")
            
            # 1. Courbe d'équité
            self._plot_equity_curve(result)
            
            # 2. Distribution des profits/pertes
            self._plot_pnl_distribution(result)
            
            # 3. Performance mensuelle
            self._plot_monthly_performance(result)
            
            # 4. Efficacité des signaux (facultatif si on a suffisamment de signaux)
            if len(result.signals) > 10:
                self._plot_signal_efficiency(result)
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations: {e}")
            
    def _plot_equity_curve(self, result: EvaluationResult) -> None:
        """
        Trace la courbe d'équité.
        
        Args:
            result: Résultat de l'évaluation
        """
        plt.figure(figsize=(12, 6))
        
        # Extraire les données de la courbe d'équité
        timestamps = [entry.get('timestamp', 0) for entry in result.equity_curve]
        values = [entry.get('value', 0) for entry in result.equity_curve]
        
        # Convertir les timestamps en dates
        dates = [datetime.fromtimestamp(ts) for ts in timestamps]
        
        # Tracer la courbe d'équité
        plt.plot(dates, values, label=f"{result.strategy_name}", color='blue', linewidth=2)
        
        # Ajouter des marques pour les trades
        for trade in result.trades:
            entry_time = datetime.fromtimestamp(trade.get('entry_timestamp', 0))
            exit_time = datetime.fromtimestamp(trade.get('exit_timestamp', 0))
            
            # Marquer les entrées
            plt.scatter([entry_time], [trade.get('entry_price', 0) * trade.get('size', 1)], 
                     marker='^', color='green', s=50, alpha=0.7)
            
            # Marquer les sorties avec couleur selon profit/perte
            color = 'green' if trade.get('profit_pct', 0) > 0 else 'red'
            plt.scatter([exit_time], [trade.get('exit_price', 0) * trade.get('size', 1)], 
                     marker='v', color=color, s=50, alpha=0.7)
        
        # Ajouter les détails du graphique
        plt.title(f"Courbe d'équité - {result.strategy_name}", fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Valeur du portefeuille', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Ajouter des annotations pour les métriques clés
        text = f"ROI: {result.metrics.roi:.2f}%\n"
        text += f"DD Max: {result.metrics.max_drawdown:.2f}%\n"
        text += f"Sharpe: {result.metrics.sharpe_ratio:.2f}\n"
        text += f"Win Rate: {result.metrics.win_rate*100:.1f}%"
        
        plt.annotate(text, xy=(0.02, 0.95), xycoords='axes fraction', 
                 fontsize=10, bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8))
        
        # Sauvegarder l'image
        plt.tight_layout()
        file_path = self._get_file_path(result, "equity_curve.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        logger.info(f"Courbe d'équité enregistrée: {file_path}")
        
    def _plot_pnl_distribution(self, result: EvaluationResult) -> None:
        """
        Trace la distribution des profits et pertes.
        
        Args:
            result: Résultat de l'évaluation
        """
        if not result.trades:
            logger.warning("Pas de trades pour générer la distribution P&L")
            return
            
        plt.figure(figsize=(12, 6))
        
        # Extraire les données de P&L en pourcentage
        pnl_pct = [trade.get('profit_pct', 0) for trade in result.trades]
        
        # Créer l'histogramme avec une division entre profits et pertes
        sns.histplot(pnl_pct, kde=True, bins=20, color='skyblue')
        
        # Ajouter une ligne verticale à zéro
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        
        # Calculer quelques statistiques
        avg_win = np.mean([p for p in pnl_pct if p > 0]) if any(p > 0 for p in pnl_pct) else 0
        avg_loss = np.mean([p for p in pnl_pct if p < 0]) if any(p < 0 for p in pnl_pct) else 0
        
        # Ajouter des lignes pour les moyennes
        plt.axvline(x=avg_win, color='green', linestyle='--', alpha=0.7, label=f"Gain moyen: {avg_win:.2f}%")
        plt.axvline(x=avg_loss, color='darkred', linestyle='--', alpha=0.7, label=f"Perte moyenne: {avg_loss:.2f}%")
        
        # Ajouter les détails du graphique
        plt.title(f"Distribution des profits et pertes - {result.strategy_name}", fontsize=14)
        plt.xlabel('Profit/Perte (%)', fontsize=12)
        plt.ylabel('Nombre de trades', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Sauvegarder l'image
        plt.tight_layout()
        file_path = self._get_file_path(result, "pnl_distribution.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        logger.info(f"Distribution P&L enregistrée: {file_path}")
        
    def _plot_monthly_performance(self, result: EvaluationResult) -> None:
        """
        Trace la performance mensuelle.
        
        Args:
            result: Résultat de l'évaluation
        """
        if not result.trades:
            logger.warning("Pas de trades pour générer la performance mensuelle")
            return
            
        # Calculer les performances par mois
        monthly_returns = {}
        
        for trade in result.trades:
            exit_time = trade.get('exit_timestamp', 0)
            exit_date = datetime.fromtimestamp(exit_time)
            month_key = f"{exit_date.year}-{exit_date.month:02d}"
            
            if month_key not in monthly_returns:
                monthly_returns[month_key] = []
                
            monthly_returns[month_key].append(trade.get('profit_pct', 0))
            
        # Calculer la performance cumulée par mois
        months = sorted(monthly_returns.keys())
        cumulative_returns = []
        monthly_avg_returns = []
        
        for month in months:
            avg_return = np.mean(monthly_returns[month])
            monthly_avg_returns.append(avg_return)
            
        # Créer le graphique
        plt.figure(figsize=(14, 10))
        
        # Sous-graphique 1: Performance moyenne par mois
        plt.subplot(2, 1, 1)
        
        colors = ['green' if ret > 0 else 'red' for ret in monthly_avg_returns]
        plt.bar(months, monthly_avg_returns, color=colors, alpha=0.7)
        
        plt.title(f"Performance mensuelle moyenne - {result.strategy_name}", fontsize=14)
        plt.xlabel('Mois', fontsize=12)
        plt.ylabel('Rendement moyen (%)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Sous-graphique 2: Distribution des rendements par mois
        plt.subplot(2, 1, 2)
        
        # Préparer les données pour le box plot
        box_data = [monthly_returns[month] for month in months]
        
        # Créer le box plot
        plt.boxplot(box_data, labels=months)
        plt.title("Distribution des rendements par mois", fontsize=14)
        plt.xlabel('Mois', fontsize=12)
        plt.ylabel('Rendement (%)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Ajouter une ligne à zéro
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Sauvegarder l'image
        plt.tight_layout()
        file_path = self._get_file_path(result, "monthly_performance.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        logger.info(f"Performance mensuelle enregistrée: {file_path}")
        
    def _plot_signal_efficiency(self, result: EvaluationResult) -> None:
        """
        Trace l'efficacité des signaux.
        
        Args:
            result: Résultat de l'évaluation
        """
        # Analyser l'efficacité des signaux
        signal_analysis = self._analyze_signals(result.signals)
        
        # Préparer les données pour le graphique
        signal_types = list(signal_analysis.keys())
        counts = [data["count"] for data in signal_analysis.values()]
        confidences = [data["avg_confidence"] for data in signal_analysis.values()]
        
        # Créer le graphique
        plt.figure(figsize=(10, 6))
        
        # Barres pour le nombre de signaux
        bar_positions = np.arange(len(signal_types))
        bars = plt.bar(bar_positions, counts, alpha=0.6, color='skyblue', label='Nombre de signaux')
        
        # Ligne pour la confiance moyenne
        plt.plot(bar_positions, confidences, marker='o', color='darkred', label='Confiance moyenne')
        
        # Ajouter les détails du graphique
        plt.title(f"Analyse des signaux - {result.strategy_name}", fontsize=14)
        plt.xlabel('Type de signal', fontsize=12)
        plt.ylabel('Nombre de signaux', fontsize=12)
        plt.xticks(bar_positions, signal_types)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Ajouter un axe Y secondaire pour la confiance
        ax2 = plt.gca().twinx()
        ax2.set_ylabel('Confiance moyenne', fontsize=12, color='darkred')
        ax2.set_ylim([0, 1.0])
        
        # Sauvegarder l'image
        plt.tight_layout()
        file_path = self._get_file_path(result, "signal_efficiency.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
    def _get_file_path(self, result: EvaluationResult, filename: str, url: bool = False) -> str:
        """
        Génère un chemin de fichier pour les résultats d'évaluation.
        
        Args:
            result: Résultat de l'évaluation
            filename: Nom du fichier
            url: Si True, renvoie un chemin URL relatif
            
        Returns:
            Chemin vers le fichier
        """
        # Créer un sous-répertoire pour la stratégie
        strategy_dir = os.path.join(
            self.output_dir, 
            f"{result.strategy_name}_{result.token_address[-6:]}"
        )
        os.makedirs(strategy_dir, exist_ok=True)
        
        if url:
            return f"{os.path.basename(strategy_dir)}/{filename}"
        else:
            return os.path.join(strategy_dir, filename)
            
    def generate_comparative_report(self, comparison_result: Dict[str, Any], save_html: bool = True) -> str:
        """
        Génère un rapport comparatif de plusieurs stratégies.
        
        Args:
            comparison_result: Résultat de la comparaison de stratégies
            save_html: Si True, sauvegarde le rapport au format HTML
            
        Returns:
            Rapport au format markdown
        """
        # Extraire les données
        individual_results = comparison_result.get("individual_results", {})
        comparison = comparison_result.get("comparison", {})
        
        if not individual_results or not comparison:
            return "Pas assez de données pour générer un rapport comparatif."
            
        # Créer le rapport en markdown
        report = "# Rapport de comparaison des stratégies\n\n"
        report += f"## Synthèse\n\n"
        
        # Détails sur la meilleure stratégie
        best_overall = comparison.get("best_overall", "")
        if best_overall:
            report += f"### Meilleure stratégie globale: **{best_overall}**\n\n"
            
        report += "### Performances par métrique\n\n"
        report += "| Métrique | Meilleure stratégie | Valeur |\n"
        report += "|----------|-------------------|-------|\n"
        
        for metric, strategy in comparison.get("best_by_metric", {}).items():
            value = comparison.get("metrics_by_strategy", {}).get(metric, {}).get(strategy, 0)
            if metric == "max_drawdown":
                report += f"| {metric.capitalize()} | {strategy} | {value:.2f}% |\n"
            elif metric == "win_rate":
                report += f"| {metric.capitalize()} | {strategy} | {value*100:.2f}% |\n"
            else:
                report += f"| {metric.upper()} | {strategy} | {value:.2f} |\n"
                
        report += "\n"
        
        # Générer le tableau comparatif
        report += "## Tableau comparatif\n\n"
        report += "| Stratégie | ROI | Sharpe | Win Rate | Max DD | Profit Factor | Trades |\n"
        report += "|-----------|-----|--------|----------|--------|--------------|--------|\n"
        
        # Trier les stratégies par leur score composite
        sorted_strategies = sorted(
            comparison.get("composite_scores", {}).items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        metrics_by_strategy = comparison.get("metrics_by_strategy", {})
        for strategy_name, score in sorted_strategies:
            roi = metrics_by_strategy.get("roi", {}).get(strategy_name, 0)
            sharpe = metrics_by_strategy.get("sharpe", {}).get(strategy_name, 0)
            win_rate = metrics_by_strategy.get("win_rate", {}).get(strategy_name, 0)
            max_dd = metrics_by_strategy.get("max_drawdown", {}).get(strategy_name, 0)
            profit_factor = metrics_by_strategy.get("profit_factor", {}).get(strategy_name, 0)
            trade_count = metrics_by_strategy.get("trade_count", {}).get(strategy_name, 0)
            
            report += f"| {strategy_name} | {roi:.2f}% | {sharpe:.2f} | {win_rate*100:.1f}% | {max_dd:.2f}% | {profit_factor:.2f} | {trade_count} |\n"
            
        report += "\n"
        
        # Générer les visualisations comparatives
        self._generate_comparative_visualizations(individual_results)
        
        # Ajouter les visualisations au rapport
        report += "## Visualisations comparatives\n\n"
        report += "### Courbes d'équité\n\n"
        report += "![Courbes d'équité](comparative_equity_curves.png)\n\n"
        
        report += "### Performance mensuelle\n\n"
        report += "![Performance mensuelle](comparative_monthly_returns.png)\n\n"
        
        report += "### Distribution des rendements\n\n"
        report += "![Distribution des rendements](comparative_return_distributions.png)\n\n"
        
        # Sauvegarder le rapport
        report_path = os.path.join(self.output_dir, "comparative_report.md")
        with open(report_path, 'w') as f:
            f.write(report)
            
        # Convertir en HTML si demandé
        if save_html:
            try:
                import markdown
                html = markdown.markdown(report, extensions=['tables', 'fenced_code'])
                
                # Ajouter un style CSS
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Rapport comparatif des stratégies</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                        h1, h2, h3 {{ color: #333; }}
                        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                        th {{ background-color: #f2f2f2; }}
                        img {{ max-width: 100%; height: auto; }}
                        .best {{ color: #007bff; font-weight: bold; }}
                    </style>
                </head>
                <body>
                {html}
                </body>
                </html>
                """
                
                html_path = os.path.join(self.output_dir, "comparative_report.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                    
                logger.info(f"Rapport HTML comparatif généré: {html_path}")
                
            except ImportError:
                logger.warning("Package 'markdown' non disponible, rapport HTML non généré")
                
        logger.info(f"Rapport Markdown comparatif généré: {report_path}")
        return report
        
    def _generate_comparative_visualizations(self, results: Dict[str, EvaluationResult]) -> None:
        """
        Génère des visualisations comparatives pour plusieurs stratégies.
        
        Args:
            results: Dictionnaire de résultats d'évaluation par stratégie
        """
        try:
            # Style pour les visualisations
            sns.set(style="whitegrid")
            
            # 1. Courbes d'équité comparatives
            self._plot_comparative_equity_curves(results)
            
            # 2. Performance mensuelle comparative
            self._plot_comparative_monthly_returns(results)
            
            # 3. Distribution des rendements comparative
            self._plot_comparative_return_distributions(results)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations comparatives: {e}")
            
    def _plot_comparative_equity_curves(self, results: Dict[str, EvaluationResult]) -> None:
        """
        Trace les courbes d'équité de plusieurs stratégies sur le même graphique.
        
        Args:
            results: Dictionnaire de résultats d'évaluation par stratégie
        """
        plt.figure(figsize=(12, 8))
        
        # Palette de couleurs pour les différentes stratégies
        colors = sns.color_palette("tab10", len(results))
        
        # Tracer les courbes d'équité pour chaque stratégie
        for i, (strategy_name, result) in enumerate(results.items()):
            # Extraire les données de la courbe d'équité
            timestamps = [entry.get('timestamp', 0) for entry in result.equity_curve]
            values = [entry.get('value', 0) for entry in result.equity_curve]
            
            # Normaliser les valeurs (chaque stratégie commence à 100)
            if values:
                start_value = values[0]
                normalized_values = [100 * v / start_value for v in values]
                
                # Convertir les timestamps en dates
                dates = [datetime.fromtimestamp(ts) for ts in timestamps]
                
                # Tracer la courbe
                plt.plot(dates, normalized_values, label=strategy_name, color=colors[i], linewidth=2)
        
        # Ajouter les détails du graphique
        plt.title(f"Comparaison des courbes d'équité (normalisées)", fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Valeur du portefeuille (normalisée à 100)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper left')
        
        # Sauvegarder l'image
        plt.tight_layout()
        file_path = os.path.join(self.output_dir, "comparative_equity_curves.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        logger.info(f"Courbes d'équité comparatives enregistrées: {file_path}")
        
    def _plot_comparative_monthly_returns(self, results: Dict[str, EvaluationResult]) -> None:
        """
        Trace les rendements mensuels de plusieurs stratégies.
        
        Args:
            results: Dictionnaire de résultats d'évaluation par stratégie
        """
        if not results:
            return
            
        # Collecter les rendements mensuels pour chaque stratégie
        monthly_returns = {}
        
        for strategy_name, result in results.items():
            strategy_monthly = {}
            
            for trade in result.trades:
                exit_time = trade.get('exit_timestamp', 0)
                exit_date = datetime.fromtimestamp(exit_time)
                month_key = f"{exit_date.year}-{exit_date.month:02d}"
                
                if month_key not in strategy_monthly:
                    strategy_monthly[month_key] = []
                    
                strategy_monthly[month_key].append(trade.get('profit_pct', 0))
                
            # Calculer les moyennes mensuelles
            monthly_returns[strategy_name] = {
                month: sum(returns) / len(returns) if returns else 0
                for month, returns in strategy_monthly.items()
            }
            
        # Obtenir tous les mois uniques
        all_months = sorted(set().union(*(d.keys() for d in monthly_returns.values())))
        
        if not all_months:
            return
            
        # Préparer les données pour le graphique
        strategy_names = list(results.keys())
        data = []
        
        for month in all_months:
            row = [month]
            for strategy in strategy_names:
                row.append(monthly_returns.get(strategy, {}).get(month, 0))
            data.append(row)
            
        # Créer un DataFrame pandas
        df = pd.DataFrame(data, columns=['Month'] + strategy_names)
        
        # Transformer pour faciliter le traçage
        df_melted = pd.melt(df, id_vars=['Month'], value_vars=strategy_names, 
                         var_name='Strategy', value_name='Return')
        
        # Créer le graphique
        plt.figure(figsize=(14, 8))
        sns.barplot(x='Month', y='Return', hue='Strategy', data=df_melted)
        
        plt.title("Rendements mensuels par stratégie", fontsize=14)
        plt.xlabel('Mois', fontsize=12)
        plt.ylabel('Rendement (%)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        plt.legend(title='Stratégie')
        
        # Sauvegarder l'image
        plt.tight_layout()
        file_path = os.path.join(self.output_dir, "comparative_monthly_returns.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        logger.info(f"Rendements mensuels comparatifs enregistrés: {file_path}")
        
    def _plot_comparative_return_distributions(self, results: Dict[str, EvaluationResult]) -> None:
        """
        Trace les distributions de rendements de plusieurs stratégies.
        
        Args:
            results: Dictionnaire de résultats d'évaluation par stratégie
        """
        plt.figure(figsize=(12, 8))
        
        # Collecter les distributions de rendements
        all_returns = {}
        
        for strategy_name, result in results.items():
            returns = [trade.get('profit_pct', 0) for trade in result.trades]
            all_returns[strategy_name] = returns
            
        # Tracer les distributions de densité
        for strategy_name, returns in all_returns.items():
            if returns:  # S'assurer qu'il y a des données
                sns.kdeplot(returns, label=strategy_name)
                
        # Ajouter une ligne verticale à zéro
        plt.axvline(x=0, color='black', linestyle='--', alpha=0.7)
        
        # Ajouter les détails du graphique
        plt.title("Distribution des rendements par stratégie", fontsize=14)
        plt.xlabel('Rendement (%)', fontsize=12)
        plt.ylabel('Densité', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(title='Stratégie')
        
        # Sauvegarder l'image
        plt.tight_layout()
        file_path = os.path.join(self.output_dir, "comparative_return_distributions.png")
        plt.savefig(file_path, dpi=150)
        plt.close()
        
        logger.info(f"Distributions de rendements comparatives enregistrées: {file_path}")