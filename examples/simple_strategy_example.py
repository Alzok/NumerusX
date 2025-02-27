import asyncio
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Ajouter le répertoire parent au chemin pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.strategy_framework import Strategy, Signal, SignalType, BacktestEngine
from app.strategy_evaluator import StrategyEvaluator
from app.strategy_debug import StrategyDebugger

class SimpleRSIStrategy(Strategy):
    """Stratégie simple basée sur l'indicateur RSI."""
    
    def __init__(self, name: str, timeframes: List[str], params: Dict[str, Any] = None):
        """
        Initialise la stratégie RSI.
        
        Args:
            name: Nom de la stratégie
            timeframes: Liste des timeframes
            params: Paramètres optionnels
        """
        # Paramètres par défaut
        default_params = {
            "period": 14,       # Période du RSI
            "overbought": 70,   # Niveau de surachat
            "oversold": 30,     # Niveau de survente
            "exit_rsi": 50      # Niveau de sortie
        }
        
        # Fusionner avec les paramètres personnalisés
        actual_params = default_params.copy()
        if params:
            actual_params.update(params)
            
        super().__init__(name, timeframes, actual_params)
        
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        """
        Génère un signal basé sur le RSI.
        
        Args:
            token_address: Adresse du token
            price_data: Données de prix
            timeframe: Intervalle de temps
            
        Returns:
            Signal généré
        """
        # Vérifier que nous avons suffisamment de données
        if len(price_data) < self.params["period"] + 5:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.5,
                timestamp=datetime.now().timestamp(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={"reason": "Insufficient data"}
            )
        
        # Calculer le RSI
        rsi = self._calculate_rsi(price_data['close'], self.params["period"])
        
        # Obtenir le RSI actuel et précédent
        current_rsi = rsi[-1]
        previous_rsi = rsi[-2]
        
        # Obtenir le prix actuel
        current_price = price_data['close'].iloc[-1]
        
        # Logique de signal
        signal_type = SignalType.NEUTRAL
        confidence = 0.5
        metadata = {
            "rsi": current_rsi,
            "previous_rsi": previous_rsi,
            "current_price": current_price
        }
        
        # Signal d'achat: RSI passe au-dessus du niveau de survente
        if previous_rsi < self.params["oversold"] and current_rsi >= self.params["oversold"]:
            signal_type = SignalType.BUY
            confidence = 0.7 + min(0.2, (self.params["oversold"] - previous_rsi) / 100)
            
            # Calculer les niveaux de stop-loss et take-profit
            stop_loss = current_price * 0.97  # 3% en dessous du prix actuel
            take_profit = current_price * 1.06  # 6% au-dessus du prix actuel
            
            return Signal(
                type=signal_type,
                confidence=confidence,
                timestamp=datetime.now().timestamp(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata=metadata,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
        # Signal de vente: RSI passe en dessous du niveau de surachat
        elif previous_rsi > self.params["overbought"] and current_rsi <= self.params["overbought"]:
            signal_type = SignalType.SELL
            confidence = 0.7 + min(0.2, (previous_rsi - self.params["overbought"]) / 100)
            
            # Calculer les niveaux de stop-loss et take-profit
            stop_loss = current_price * 1.03  # 3% au-dessus du prix actuel
            take_profit = current_price * 0.94  # 6% en dessous du prix actuel
            
            return Signal(
                type=signal_type,
                confidence=confidence,
                timestamp=datetime.now().timestamp(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata=metadata,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        
        # Pas de nouveau signal
        return Signal(
            type=SignalType.NEUTRAL,
            confidence=confidence,
            timestamp=datetime.now().timestamp(),
            token_address=token_address,
            timeframe=timeframe,
            strategy_name=self.name,
            metadata=metadata
        )
        
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> np.ndarray:
        """
        Calcule l'indicateur RSI.
        
        Args:
            prices: Série de prix
            period: Période du RSI
            
        Returns:
            Valeurs du RSI
        """
        # Calculer les variations
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        
        # Calculer les gains et pertes
        up = seed[seed > 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:  # Éviter la division par zéro
            down = 0.00001
        
        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        # Calculer le RSI pour les valeurs restantes
        for i in range(period, len(prices)):
            delta = deltas[i-1]  # Différence avec le prix précédent
            
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
                
            # Moyenne mobile exponentielle des gains/pertes
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            if down == 0:  # Éviter la division par zéro
                down = 0.00001
                
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
            
        return rsi

def generate_sample_data(days: int = 100) -> pd.DataFrame:
    """
    Génère des données de prix synthétiques pour les tests.
    
    Args:
        days: Nombre de jours de données
        
    Returns:
        DataFrame contenant les données OHLCV
    """
    np.random.seed(42)  # Pour reproductibilité
    
    # Générer une marche aléatoire pour le prix
    base_price = 100
    returns = np.random.normal(0.0005, 0.02, days * 24)  # Données horaires
    price_movement = np.cumprod(1 + returns)
    prices = base_price * price_movement
    
    # Créer une liste de dates horaires
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, periods=len(prices))
    
    # Générer open, high, low, close à partir du prix moyen
    data = []
    for i, price in enumerate(prices):
        # Ajouter de la variation intra-période
        open_price = price * (1 + np.random.normal(0, 0.003))
        close_price = price * (1 + np.random.normal(0, 0.003))
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.004)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.004)))
        volume = abs(np.random.normal(1000000, 500000))
        
        data.append([dates[i], open_price, high_price, low_price, close_price, volume])
    
    # Créer le DataFrame
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df.set_index('timestamp', inplace=True)
    
    return df

async def run_strategy_example():
    """
    Exécute un exemple complet de la stratégie RSI.
    """
    print("🚀 Démarrage de l'exemple de stratégie RSI...")
    
    # Générer des données synthétiques
    hourly_data = generate_sample_data(days=30)
    print(f"📊 Données générées: {len(hourly_data)} points OHLCV horaires")
    
    # Créer la stratégie RSI avec des paramètres personnalisés
    strategy = SimpleRSIStrategy(
        name="RSI_30_70",
        timeframes=["1h"],
        params={
            "period": 14,
            "overbought": 70,
            "oversold": 30,
        }
    )
    
    # Format du prix pour l'affichage
    price_data = {"1h": hourly_data}
    token_address = "SAMPLE_TOKEN_123"
    
    # 1. Générer quelques signaux
    print("\n📡 Génération de signaux sur différentes périodes...")
    signals = []
    
    # Prendre quelques fenêtres de temps pour l'analyse
    windows = [
        int(len(hourly_data) * 0.5),
        int(len(hourly_data) * 0.7),
        int(len(hourly_data) * 0.8),
        int(len(hourly_data) * 0.9),
        len(hourly_data)
    ]
    
    for i in windows:
        window = hourly_data.iloc[:i]
        signal = await strategy.generate_signal(token_address, window, "1h")
        signals.append(signal)
        
        print(f"  ↳ Point {i:3d}: Signal {signal.type.value.upper():8s} (confidence: {signal.confidence:.2f}), RSI: {signal.metadata['rsi']:.1f}")
    
    # 2. Exécuter un backtest complet
    print("\n⚙️ Exécution du backtest...")
    backtest_engine = BacktestEngine()
    result = await backtest_engine.run_backtest(strategy, price_data, token_address)
    
    trades = result.get("trades", [])
    
    print(f"  ↳ {len(trades)} trades exécutés")
    print(f"  ↳ ROI total: {result['metrics'].get('total_roi', 0):.2f}%")
    print(f"  ↳ Win rate: {result['metrics'].get('win_rate', 0) * 100:.1f}%")
    print(f"  ↳ Profit factor: {result['metrics'].get('profit_factor', 0):.2f}")
    
    # 3. Évaluer avec le module d'évaluation
    print("\n📊 Génération du rapport d'évaluation...")
    evaluator = StrategyEvaluator(output_dir="example_results")
    evaluation = await evaluator.evaluate_strategy(strategy, price_data, token_address)
    
    report_path = evaluator.generate_report(evaluation)
    print(f"  ↳ Rapport généré: {report_path}")
    
    # 4. Déboguer la stratégie
    print("\n🔍 Débogage de la stratégie...")
    debugger = StrategyDebugger(output_dir="example_debug")
    debug_result = await debugger.debug_strategy(strategy, price_data, token_address)
    
    analysis = debugger.analyze_strategy_problems(debug_result)
    
    # Afficher les recommandations
    print("\n📝 Recommandations d'amélioration:")
    for i, recommendation in enumerate(analysis["recommendations"], 1):
        print(f"  {i}. {recommendation}")
    
    print("\n✅ Exemple terminé ! Explorez les résultats dans les dossiers 'example_results' et 'example_debug'.")

# Exécuter l'exemple si le script est exécuté directement
if __name__ == "__main__":
    asyncio.run(run_strategy_example())