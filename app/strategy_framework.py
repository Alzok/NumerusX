import logging
import time
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("strategy_framework")

class SignalType(Enum):
    """Types de signaux de trading possibles."""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"

class StrategyType(Enum):
    """Types de stratégies de trading."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    PATTERN_RECOGNITION = "pattern_recognition"
    SENTIMENT = "sentiment"
    VOLATILITY = "volatility"
    MULTI_FACTOR = "multi_factor"

@dataclass
class Signal:
    """Représentation d'un signal de trading."""
    type: SignalType
    confidence: float  # 0.0-1.0
    timestamp: float
    token_address: str
    timeframe: str
    strategy_name: str
    metadata: Dict[str, Any]
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class StrategyMetrics:
    """Métriques d'évaluation d'une stratégie."""
    win_rate: float
    profit_factor: float  # Profits bruts / pertes brutes
    sharpe_ratio: float
    max_drawdown: float
    avg_trade_duration: float  # En secondes
    total_trades: int
    profitable_trades: int
    roi: float  # Return on Investment
    
class Strategy(ABC):
    """Classe de base pour toutes les stratégies de trading."""
    
    def __init__(self, name: str, timeframes: List[str], params: Dict[str, Any] = None):
        """
        Initialise une stratégie.
        
        Args:
            name: Nom de la stratégie
            timeframes: Liste des timeframes utilisés
            params: Paramètres optionnels pour la stratégie
        """
        self.name = name
        self.timeframes = timeframes
        self.params = params or {}
        self.signals: List[Signal] = []
        self.metrics: Optional[StrategyMetrics] = None
        
    @abstractmethod
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        """
        Génère un signal de trading pour un token donné.
        
        Args:
            token_address: Adresse du token
            price_data: DataFrame de données de prix
            timeframe: Timeframe utilisé
            
        Returns:
            Signal de trading généré
        """
        pass
        
    def add_signal(self, signal: Signal) -> None:
        """
        Ajoute un signal à l'historique des signaux.
        
        Args:
            signal: Signal à ajouter
        """
        self.signals.append(signal)
        # Garder un maximum de 1000 signaux en mémoire
        if len(self.signals) > 1000:
            self.signals = self.signals[-1000:]
            
    async def calculate_metrics(self, performance_data: Optional[List[Dict[str, Any]]] = None) -> StrategyMetrics:
        """
        Calcule les métriques de performance de la stratégie.
        
        Args:
            performance_data: Données de performance optionnelles
            
        Returns:
            Métriques de la stratégie
        """
        # Si des données de performance sont fournies, les utiliser
        # Sinon, analyser l'historique des signaux
        
        if performance_data:
            return await self._calculate_metrics_from_performance(performance_data)
        else:
            return await self._calculate_metrics_from_signals()
            
    async def _calculate_metrics_from_performance(self, performance_data: List[Dict[str, Any]]) -> StrategyMetrics:
        """Calcule les métriques à partir des données de performance."""
        if not performance_data:
            return StrategyMetrics(
                win_rate=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                avg_trade_duration=0.0,
                total_trades=0,
                profitable_trades=0,
                roi=0.0
            )
            
        total_trades = len(performance_data)
        profitable_trades = sum(1 for trade in performance_data if trade.get('profit', 0) > 0)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0.0
        
        total_profit = sum(trade.get('profit', 0) for trade in performance_data if trade.get('profit', 0) > 0)
        total_loss = sum(abs(trade.get('profit', 0)) for trade in performance_data if trade.get('profit', 0) < 0)
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Calcul du ROI
        initial_capital = performance_data[0].get('capital_before', 1000) if performance_data else 1000
        final_capital = performance_data[-1].get('capital_after', initial_capital) if performance_data else initial_capital
        roi = (final_capital / initial_capital - 1) if initial_capital > 0 else 0.0
        
        # Drawdown et Sharpe Ratio nécessitent des calculs plus complexes
        # Pour cet exemple, nous utilisons des valeurs simplifiées
        
        # Durée moyenne des trades
        durations = []
        for trade in performance_data:
            if 'entry_time' in trade and 'exit_time' in trade:
                duration = trade['exit_time'] - trade['entry_time']
                durations.append(duration)
                
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return StrategyMetrics(
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=1.0,  # Placeholder
            max_drawdown=0.1,  # Placeholder
            avg_trade_duration=avg_duration,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            roi=roi
        )
        
    async def _calculate_metrics_from_signals(self) -> StrategyMetrics:
        """Calcule les métriques à partir des signaux historiques."""
        # Ce calcul nécessiterait de simuler des trades basés sur les signaux
        # Pour cet exemple, nous renvoyons des valeurs par défaut
        return StrategyMetrics(
            win_rate=0.5,
            profit_factor=1.2,
            sharpe_ratio=0.8,
            max_drawdown=0.15,
            avg_trade_duration=86400,  # 1 jour
            total_trades=len(self.signals),
            profitable_trades=len(self.signals) // 2,  # Hypothèse simplifiée
            roi=0.05
        )
        
    async def optimize_parameters(self, price_data: Dict[str, pd.DataFrame], 
                              parameter_ranges: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Optimise les paramètres de la stratégie sur des données historiques.
        
        Args:
            price_data: Données de prix par timeframe
            parameter_ranges: Plages de valeurs pour chaque paramètre
            
        Returns:
            Paramètres optimaux trouvés
        """
        best_params = {}
        best_performance = float('-inf')
        
        # Générer toutes les combinaisons de paramètres possibles
        param_combinations = self._generate_parameter_combinations(parameter_ranges)
        
        for params in param_combinations:
            # Tester cette combinaison de paramètres
            temp_strategy = self.__class__(self.name, self.timeframes, params)
            performance = await self._backtest_parameters(temp_strategy, price_data)
            
            if performance > best_performance:
                best_performance = performance
                best_params = params.copy()
                
        logger.info(f"Paramètres optimaux trouvés pour {self.name}: {best_params} (performance: {best_performance:.4f})")
        return best_params
        
    def _generate_parameter_combinations(self, parameter_ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Génère toutes les combinaisons possibles de paramètres."""
        import itertools
        
        keys = list(parameter_ranges.keys())
        values = list(parameter_ranges.values())
        combinations = list(itertools.product(*values))
        
        return [dict(zip(keys, combo)) for combo in combinations]
        
    async def _backtest_parameters(self, strategy, price_data: Dict[str, pd.DataFrame]) -> float:
        """
        Effectue un backtest d'une stratégie avec un ensemble de paramètres.
        
        Returns:
            Score de performance (plus élevé = meilleur)
        """
        # Dans une implémentation réelle, exécuter un backtest complet
        # Pour cet exemple, nous simulons un score
        return 0.5  # Score par défaut

class MovingAverageCrossStrategy(Strategy):
    """Stratégie basée sur le croisement de moyennes mobiles."""
    
    def __init__(self, name: str, timeframes: List[str], params: Dict[str, Any] = None):
        """
        Initialise une stratégie de croisement de moyennes mobiles.
        
        Args:
            name: Nom de la stratégie
            timeframes: Liste des timeframes
            params: Paramètres de la stratégie
        """
        default_params = {
            "fast_period": 10,
            "slow_period": 30
        }
        
        # Fusionner avec les paramètres par défaut
        actual_params = default_params.copy()
        if params:
            actual_params.update(params)
            
        super().__init__(name, timeframes, actual_params)
        
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        """
        Génère un signal basé sur le croisement de moyennes mobiles.
        
        Args:
            token_address: Adresse du token
            price_data: DataFrame des données de prix
            timeframe: Timeframe actuel
            
        Returns:
            Signal généré
        """
        if price_data.empty or len(price_data) < self.params["slow_period"]:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.0,
                timestamp=time.time(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={}
            )
            
        # Calculer les moyennes mobiles
        fast_ma = price_data['close'].rolling(window=self.params["fast_period"]).mean()
        slow_ma = price_data['close'].rolling(window=self.params["slow_period"]).mean()
        
        # Obtenir les valeurs les plus récentes
        latest_fast = fast_ma.iloc[-1]
        latest_slow = slow_ma.iloc[-1]
        
        # Obtenir les valeurs précédentes
        prev_fast = fast_ma.iloc[-2]
        prev_slow = slow_ma.iloc[-2]
        
        # Déterminer le signal
        if prev_fast < prev_slow and latest_fast > latest_slow:
            signal_type = SignalType.BUY
            confidence = min(1.0, (latest_fast / latest_slow - 1) * 10)
        elif prev_fast > prev_slow and latest_fast < latest_slow:
            signal_type = SignalType.SELL
            confidence = min(1.0, (latest_slow / latest_fast - 1) * 10)
        else:
            signal_type = SignalType.NEUTRAL
            confidence = 0.1
            
        # Calculer les niveaux de stop-loss et take-profit
        current_price = price_data['close'].iloc[-1]
        atr = self._calculate_atr(price_data)
        
        if signal_type == SignalType.BUY:
            stop_loss = current_price - 2 * atr
            take_profit = current_price + 3 * atr
        elif signal_type == SignalType.SELL:
            stop_loss = current_price + 2 * atr
            take_profit = current_price - 3 * atr
        else:
            stop_loss = None
            take_profit = None
            
        # Créer le signal
        signal = Signal(
            type=signal_type,
            confidence=confidence,
            timestamp=time.time(),
            token_address=token_address,
            timeframe=timeframe,
            strategy_name=self.name,
            metadata={
                "fast_ma": latest_fast,
                "slow_ma": latest_slow,
                "current_price": current_price,
                "atr": atr
            },
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Ajouter à l'historique des signaux
        self.add_signal(signal)
        
        return signal
        
    def _calculate_atr(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calcule l'Average True Range."""
        high = price_data['high']
        low = price_data['low']
        close = price_data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr

class RSIStrategy(Strategy):
    """Stratégie basée sur l'indicateur RSI (Relative Strength Index)."""
    
    def __init__(self, name: str, timeframes: List[str], params: Dict[str, Any] = None):
        """
        Initialise une stratégie RSI.
        
        Args:
            name: Nom de la stratégie
            timeframes: Liste des timeframes
            params: Paramètres de la stratégie
        """
        default_params = {
            "period": 14,
            "overbought": 70,
            "oversold": 30
        }
        
        # Fusionner avec les paramètres par défaut
        actual_params = default_params.copy()
        if params:
            actual_params.update(params)
            
        super().__init__(name, timeframes, actual_params)
        
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        """
        Génère un signal basé sur le RSI.
        
        Args:
            token_address: Adresse du token
            price_data: DataFrame des données de prix
            timeframe: Timeframe actuel
            
        Returns:
            Signal généré
        """
        if price_data.empty or len(price_data) < self.params["period"] + 1:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.0,
                timestamp=time.time(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={}
            )
            
        # Calculer le RSI
        delta = price_data['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.params["period"]).mean()
        avg_loss = loss.rolling(window=self.params["period"]).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Obtenir le RSI le plus récent
        latest_rsi = rsi.iloc[-1]
        
        # Déterminer le signal
        if latest_rsi <= self.params["oversold"]:
            signal_type = SignalType.BUY
            confidence = min(1.0, (self.params["oversold"] - latest_rsi) / self.params["oversold"])
        elif latest_rsi >= self.params["overbought"]:
            signal_type = SignalType.SELL
            confidence = min(1.0, (latest_rsi - self.params["overbought"]) / (100 - self.params["overbought"]))
        else:
            signal_type = SignalType.NEUTRAL
            confidence = 0.1
            
        # Calculer les niveaux de stop-loss et take-profit
        current_price = price_data['close'].iloc[-1]
        atr = self._calculate_atr(price_data)
        
        if signal_type == SignalType.BUY:
            stop_loss = current_price * 0.95  # 5% sous le prix actuel
            take_profit = current_price * 1.15  # 15% au-dessus du prix actuel
        elif signal_type == SignalType.SELL:
            stop_loss = current_price * 1.05  # 5% au-dessus du prix actuel
            take_profit = current_price * 0.85  # 15% sous le prix actuel
        else:
            stop_loss = None
            take_profit = None
            
        # Créer le signal
        signal = Signal(
            type=signal_type,
            confidence=confidence,
            timestamp=time.time(),
            token_address=token_address,
            timeframe=timeframe,
            strategy_name=self.name,
            metadata={
                "rsi": latest_rsi,
                "current_price": current_price,
                "atr": atr
            },
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Ajouter à l'historique des signaux
        self.add_signal(signal)
        
        return signal
        
    def _calculate_atr(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calcule l'Average True Range."""
        high = price_data['high']
        low = price_data['low']
        close = price_data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr

class SentimentBasedStrategy(Strategy):
    """Stratégie basée sur l'analyse de sentiment."""
    
    def __init__(self, name: str, timeframes: List[str], sentiment_analyzer=None, params: Dict[str, Any] = None):
        """
        Initialise une stratégie basée sur le sentiment.
        
        Args:
            name: Nom de la stratégie
            timeframes: Liste des timeframes
            sentiment_analyzer: Analyseur de sentiment à utiliser
            params: Paramètres de la stratégie
        """
        default_params = {
            "positive_threshold": 0.6,
            "negative_threshold": -0.3,
            "volume_min": 100  # Volume minimum pour considérer le sentiment
        }
        
        # Fusionner avec les paramètres par défaut
        actual_params = default_params.copy()
        if params:
            actual_params.update(params)
            
        super().__init__(name, timeframes, actual_params)
        self.sentiment_analyzer = sentiment_analyzer
        
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        """
        Génère un signal basé sur l'analyse de sentiment.
        
        Args:
            token_address: Adresse du token
            price_data: DataFrame des données de prix
            timeframe: Timeframe actuel
            
        Returns:
            Signal généré
        """
        if not self.sentiment_analyzer:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.0,
                timestamp=time.time(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={}
            )
            
        # Obtenir le sentiment
        sentiment_data = await self.sentiment_analyzer.get_sentiment(token_address)
        
        # Vérifier si le volume est suffisant
        if sentiment_data.get("volume", 0) < self.params["volume_min"]:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.2,
                timestamp=time.time(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={"sentiment_score": sentiment_data.get("overall_score", 0),
                         "volume": sentiment_data.get("volume", 0)}
            )
            
        # Analyser le score de sentiment
        sentiment_score = sentiment_data.get("overall_score", 0)
        
        # Déterminer le signal
        if sentiment_score >= self.params["positive_threshold"]:
            signal_type = SignalType.BUY
            confidence = min(1.0, sentiment_score)
        elif sentiment_score <= self.params["negative_threshold"]:
            signal_type = SignalType.SELL
            confidence = min(1.0, -sentiment_score)
        else:
            signal_type = SignalType.NEUTRAL
            confidence = 0.3
            
        # Calculer les niveaux de stop-loss et take-profit
        if price_data.empty:
            stop_loss = None
            take_profit = None
            current_price = None
        else:
            current_price = price_data['close'].iloc[-1]
            volatility = price_data['close'].pct_change().std() * np.sqrt(252)  # Annualisé
            
            if signal_type == SignalType.BUY:
                stop_loss = current_price * (1 - volatility)
                take_profit = current_price * (1 + 2 * volatility)
            elif signal_type == SignalType.SELL:
                stop_loss = current_price * (1 + volatility)
                take_profit = current_price * (1 - 2 * volatility)
            else:
                stop_loss = None
                take_profit = None
                
        # Créer le signal
        signal = Signal(
            type=signal_type,
            confidence=confidence,
            timestamp=time.time(),
            token_address=token_address,
            timeframe=timeframe,
            strategy_name=self.name,
            metadata={
                "sentiment_score": sentiment_score,
                "volume": sentiment_data.get("volume", 0),
                "current_price": current_price,
                "sources": sentiment_data.get("sources", {})
            },
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Ajouter à l'historique des signaux
        self.add_signal(signal)
        
        return signal

class MultiStrategyFramework:
    """Framework pour combiner et pondérer plusieurs stratégies."""
    
    def __init__(self, strategies: List[Strategy], weights: Optional[Dict[str, float]] = None):
        """
        Initialise le framework multi-stratégies.
        
        Args:
            strategies: Liste des stratégies à utiliser
            weights: Poids à appliquer à chaque stratégie (par nom)
        """
        self.strategies = strategies
        
        # Si aucun poids n'est fourni, utiliser des poids égaux
        if weights is None:
            total = len(strategies)
            self.weights = {strategy.name: 1.0 / total for strategy in strategies}
        else:
            # Normaliser les poids
            total = sum(weights.values())
            self.weights = {name: weight / total for name, weight in weights.items()}
            
    async def generate_combined_signal(self, token_address: str, 
                                    price_data: Dict[str, pd.DataFrame]) -> Signal:
        """
        Génère un signal combiné à partir de toutes les stratégies.
        
        Args:
            token_address: Adresse du token
            price_data: Données de prix par timeframe
            
        Returns:
            Signal combiné
        """
        signals = []
        
        # Générer un signal pour chaque stratégie
        for strategy in self.strategies:
            for timeframe in strategy.timeframes:
                if timeframe in price_data:
                    signal = await strategy.generate_signal(
                        token_address, 
                        price_data[timeframe],
                        timeframe
                    )
                    signals.append((signal, self.weights.get(strategy.name, 0.0)))
                    
        # Si aucun signal n'a été généré, renvoyer un signal neutre
        if not signals:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.0,
                timestamp=time.time(),
                token_address=token_address,
                timeframe="all",
                strategy_name="multi_strategy",
                metadata={}
            )
            
        # Combiner les signaux
        return self._combine_signals(signals, token_address)
        
    def _combine_signals(self, weighted_signals: List[Tuple[Signal, float]], token_address: str) -> Signal:
        """
        Combine plusieurs signaux pondérés en un seul.
        
        Args:
            weighted_signals: Liste de tuples (signal, poids)
            token_address: Adresse du token
            
        Returns:
            Signal combiné
        """
        # Compteurs pour chaque type de signal
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        # Métadonnées combinées
        combined_metadata = {}
        
        # Références aux signaux d'origine
        signal_refs = []
        
        # Agréger les scores
        for signal, weight in weighted_signals:
            signal_refs.append(f"{signal.strategy_name}:{signal.type.value}")
            
            if signal.type in (SignalType.BUY, SignalType.STRONG_BUY):
                buy_score += signal.confidence * weight
            elif signal.type in (SignalType.SELL, SignalType.STRONG_SELL):
                sell_score += signal.confidence * weight
                
            # Ajouter les métadonnées (préfixées par le nom de la stratégie)
            for key, value in signal.metadata.items():
                combined_key = f"{signal.strategy_name}_{key}"
                combined_metadata[combined_key] = value
                
            total_weight += weight
            
        # Si le poids total est nul, renvoyer un signal neutre
        if total_weight == 0:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.0,
                timestamp=time.time(),
                token_address=token_address,
                timeframe="all",
                strategy_name="multi_strategy",
                metadata={"signals": signal_refs}
            )
            
        # Normaliser les scores
        buy_score /= total_weight
        sell_score /= total_weight
        
        # Déterminer le type de signal
        if buy_score > 0.7 and buy_score > sell_score:
            signal_type = SignalType.STRONG_BUY
            confidence = buy_score
        elif buy_score > 0.3 and buy_score > sell_score:
            signal_type = SignalType.BUY
            confidence = buy_score
        elif sell_score > 0.7 and sell_score > buy_score:
            signal_type = SignalType.STRONG_SELL
            confidence = sell_score
        elif sell_score > 0.3 and sell_score > buy_score:
            signal_type = SignalType.SELL
            confidence = sell_score
        else:
            signal_type = SignalType.NEUTRAL
            confidence = max(0.1, 1.0 - max(buy_score, sell_score))
            
        # Ajouter les scores aux métadonnées
        combined_metadata["buy_score"] = buy_score
        combined_metadata["sell_score"] = sell_score
        combined_metadata["signals"] = signal_refs
        
        # Stop loss et take profit moyens (uniquement pour les signaux du même type)
        matching_signals = [s for s, _ in weighted_signals if s.type == signal_type]
        
        stop_loss = None
        take_profit = None
        
        if matching_signals:
            valid_stops = [s.stop_loss for s in matching_signals if s.stop_loss is not None]
            valid_targets = [s.take_profit for s in matching_signals if s.take_profit is not None]
            
            if valid_stops:
                stop_loss = sum(valid_stops) / len(valid_stops)
                
            if valid_targets:
                take_profit = sum(valid_targets) / len(valid_targets)
                
        return Signal(
            type=signal_type,
            confidence=confidence,
            timestamp=time.time(),
            token_address=token_address,
            timeframe="all",
            strategy_name="multi_strategy",
            metadata=combined_metadata,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
    async def optimize_weights(self, token_address: str, 
                           price_data: Dict[str, pd.DataFrame], 
                           historical_period: int = 30) -> Dict[str, float]:
        """
        Optimise les poids des stratégies en fonction des performances historiques.
        
        Args:
            token_address: Adresse du token
            price_data: Données de prix par timeframe
            historical_period: Période historique pour l'optimisation (en jours)
            
        Returns:
            Poids optimisés pour chaque stratégie
        """
        if not self.strategies:
            return {}
            
        # Générer des signaux historiques pour chaque stratégie
        strategy_signals = {}
        for strategy in self.strategies:
            signals = []
            for timeframe in strategy.timeframes:
                if timeframe in price_data:
                    # Simuler des signaux sur la période historique
                    df = price_data[timeframe]
                    for i in range(len(df) - 30, len(df), 5):  # Échantillonnage pour réduire les calculs
                        if i >= 0:
                            window = df.iloc[:i]
                            if not window.empty:
                                signal = await strategy.generate_signal(token_address, window, timeframe)
                                signals.append(signal)
            strategy_signals[strategy.name] = signals
            
        # Calculer les performances par stratégie
        strategy_performances = {}
        for name, signals in strategy_signals.items():
            if signals:
                # Simuler des trades basés sur les signaux
                trades = self._simulate_trades(signals, price_data)
                # Calculer la performance (par exemple, ROI)
                roi = self._calculate_roi(trades)
                strategy_performances[name] = max(0.0001, roi)  # Éviter les valeurs négatives ou nulles
            else:
                strategy_performances[name] = 0.0001
                
        # Calculer les poids en fonction des performances relatives
        total_performance = sum(strategy_performances.values())
        if total_performance == 0:
            # Si toutes les performances sont nulles, utiliser des poids égaux
            equal_weight = 1.0 / len(self.strategies)
            return {s.name: equal_weight for s in self.strategies}
            
        # Normaliser les performances pour obtenir les poids
        weights = {name: perf / total_performance for name, perf in strategy_performances.items()}
        
        # Appliquer un lissage pour éviter des poids extrêmes
        alpha = 0.7  # Facteur de lissage
        smoothed_weights = {}
        for name in weights:
            # Mélanger le nouveau poids avec l'ancien
            old_weight = self.weights.get(name, 1.0 / len(self.strategies))
            smoothed_weights[name] = alpha * weights[name] + (1 - alpha) * old_weight
            
        # Re-normaliser les poids lissés
        total_smoothed = sum(smoothed_weights.values())
        normalized_weights = {name: w / total_smoothed for name, w in smoothed_weights.items()}
        
        logger.info(f"Poids optimisés pour {token_address}: {normalized_weights}")
        return normalized_weights
        
    def _simulate_trades(self, signals: List[Signal], price_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Simule des trades basés sur les signaux générés.
        
        Args:
            signals: Liste des signaux à simuler
            price_data: Données de prix par timeframe
            
        Returns:
            Liste des trades simulés
        """
        trades = []
        current_position = None
        
        # Trier les signaux par timestamp
        sorted_signals = sorted(signals, key=lambda s: s.timestamp)
        
        for signal in sorted_signals:
            # Obtenir le dataframe correspondant au timeframe du signal
            if signal.timeframe not in price_data or price_data[signal.timeframe].empty:
                continue
                
            df = price_data[signal.timeframe]
            current_price = df['close'].iloc[-1]
            
            # Si pas de position ouverte et signal d'achat
            if current_position is None and signal.type in (SignalType.BUY, SignalType.STRONG_BUY):
                # Ouvrir une position
                current_position = {
                    'entry_price': current_price,
                    'entry_time': signal.timestamp,
                    'token_address': signal.token_address,
                    'signal': signal,
                    'size': 1.0,  # Taille normalisée pour simplifier
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit
                }
            
            # Si position ouverte et signal de vente
            elif current_position and signal.type in (SignalType.SELL, SignalType.STRONG_SELL):
                # Fermer la position
                profit = (current_price - current_position['entry_price']) / current_position['entry_price']
                trade = {
                    'entry_price': current_position['entry_price'],
                    'entry_time': current_position['entry_time'],
                    'exit_price': current_price,
                    'exit_time': signal.timestamp,
                    'profit': profit,
                    'profit_pct': profit * 100,
                    'token_address': signal.token_address,
                    'entry_signal': current_position['signal'],
                    'exit_signal': signal
                }
                trades.append(trade)
                current_position = None
                
        return trades
        
    def _calculate_roi(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calcule le ROI à partir d'une liste de trades.
        
        Args:
            trades: Liste des trades
            
        Returns:
            ROI calculé
        """
        if not trades:
            return 0.0
            
        # Simuler un portefeuille initial de 1.0
        portfolio = 1.0
        
        for trade in trades:
            profit_factor = 1.0 + trade.get('profit', 0)
            portfolio *= profit_factor
            
        # Calculer le ROI total
        roi = portfolio - 1.0
        return roi

class BacktestEngine:
    """Moteur de backtest pour évaluer les stratégies sur des données historiques."""
    
    def __init__(self, initial_capital: float = 10000.0, 
                maker_fee: float = 0.001, taker_fee: float = 0.002,
                slippage: float = 0.002):
        """
        Initialise le moteur de backtest.
        
        Args:
            initial_capital: Capital initial pour le backtest
            maker_fee: Frais maker en pourcentage (0.001 = 0.1%)
            taker_fee: Frais taker en pourcentage (0.002 = 0.2%)
            slippage: Glissement de prix moyen par trade (0.002 = 0.2%)
        """
        self.initial_capital = initial_capital
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage = slippage
        self.trades = []
        self.equity_curve = []
        self.metrics = None
        
    async def run_backtest(self, strategy: Strategy, price_data: Dict[str, pd.DataFrame], 
                        token_address: str) -> Dict[str, Any]:
        """
        Exécute un backtest complet pour une stratégie.
        
        Args:
            strategy: Stratégie à tester
            price_data: Données de prix historiques par timeframe
            token_address: Adresse du token à trader
            
        Returns:
            Résultats du backtest
        """
        # Réinitialiser l'état
        self.trades = []
        self.equity_curve = []
        current_capital = self.initial_capital
        position_size = 0.0
        current_position = None
        
        # Liste pour suivre la valeur du portefeuille au fil du temps
        portfolio_values = []
        
        # Parcourir chaque timeframe
        for timeframe, df in price_data.items():
            if timeframe not in strategy.timeframes:
                continue
                
            # Effectuer le backtest sur chaque point historique
            for i in range(strategy.params.get("slow_period", 30), len(df) - 1):
                # Données disponibles jusqu'au point actuel
                historical_data = df.iloc[:i+1]
                
                # Date actuelle pour le suivi
                current_timestamp = historical_data.index[-1].timestamp()
                current_price = historical_data['close'].iloc[-1]
                
                # Générer un signal avec les données disponibles à ce moment
                signal = await strategy.generate_signal(token_address, historical_data, timeframe)
                
                # Mettre à jour la valeur du portefeuille
                portfolio_value = current_capital
                if current_position:
                    # Ajouter la valeur de la position ouverte
                    position_value = position_size * current_price
                    portfolio_value += position_value
                    
                portfolio_values.append({
                    'timestamp': current_timestamp,
                    'value': portfolio_value
                })
                
                # Traiter le signal
                if signal.type in (SignalType.BUY, SignalType.STRONG_BUY) and not current_position:
                    # Acheter avec le capital disponible
                    position_size = current_capital / current_price * (1 - self.taker_fee)
                    entry_price = current_price * (1 + self.slippage)  # Tenir compte du slippage
                    current_capital = 0.0  # Tout le capital est utilisé
                    
                    # Créer la position
                    current_position = {
                        'entry_price': entry_price,
                        'entry_timestamp': current_timestamp,
                        'size': position_size,
                        'stop_loss': signal.stop_loss,
                        'take_profit': signal.take_profit
                    }
                    
                    logger.debug(f"BACKTEST: BUY à {entry_price:.6f}, taille: {position_size:.6f}")
                    
                elif signal.type in (SignalType.SELL, SignalType.STRONG_SELL) and current_position:
                    # Vendre la position
                    exit_price = current_price * (1 - self.slippage)  # Tenir compte du slippage
                    sale_value = position_size * exit_price * (1 - self.taker_fee)
                    
                    # Calculer le P&L
                    profit_loss = sale_value - (position_size * current_position['entry_price'])
                    profit_pct = (exit_price / current_position['entry_price'] - 1) * 100
                    
                    # Enregistrer le trade
                    self.trades.append({
                        'entry_price': current_position['entry_price'],
                        'exit_price': exit_price,
                        'entry_timestamp': current_position['entry_timestamp'],
                        'exit_timestamp': current_timestamp,
                        'profit_loss': profit_loss,
                        'profit_pct': profit_pct,
                        'size': position_size
                    })
                    
                    logger.debug(f"BACKTEST: SELL à {exit_price:.6f}, P&L: {profit_loss:.2f} ({profit_pct:.2f}%)")
                    
                    # Mettre à jour le capital et réinitialiser la position
                    current_capital = sale_value
                    current_position = None
                    position_size = 0.0
                    
                # Vérifier les stop-loss et take-profit si une position est ouverte
                elif current_position:
                    # Vérifier le stop-loss
                    if current_position['stop_loss'] and current_price <= current_position['stop_loss']:
                        # Déclencher le stop-loss
                        exit_price = current_position['stop_loss'] * (1 - self.slippage)
                        sale_value = position_size * exit_price * (1 - self.taker_fee)
                        
                        # Calculer le P&L
                        profit_loss = sale_value - (position_size * current_position['entry_price'])
                        profit_pct = (exit_price / current_position['entry_price'] - 1) * 100
                        
                        # Enregistrer le trade
                        self.trades.append({
                            'entry_price': current_position['entry_price'],
                            'exit_price': exit_price,
                            'entry_timestamp': current_position['entry_timestamp'],
                            'exit_timestamp': current_timestamp,
                            'profit_loss': profit_loss,
                            'profit_pct': profit_pct,
                            'size': position_size,
                            'exit_reason': 'stop_loss'
                        })
                        
                        logger.debug(f"BACKTEST: STOP-LOSS à {exit_price:.6f}, P&L: {profit_loss:.2f} ({profit_pct:.2f}%)")
                        
                        # Mettre à jour le capital et réinitialiser la position
                        current_capital = sale_value
                        current_position = None
                        position_size = 0.0
                        
                    # Vérifier le take-profit
                    elif current_position['take_profit'] and current_price >= current_position['take_profit']:
                        # Déclencher le take-profit
                        exit_price = current_position['take_profit'] * (1 - self.slippage)
                        sale_value = position_size * exit_price * (1 - self.taker_fee)
                        
                        # Calculer le P&L
                        profit_loss = sale_value - (position_size * current_position['entry_price'])
                        profit_pct = (exit_price / current_position['entry_price'] - 1) * 100
                        
                        # Enregistrer le trade
                        self.trades.append({
                            'entry_price': current_position['entry_price'],
                            'exit_price': exit_price,
                            'entry_timestamp': current_position['entry_timestamp'],
                            'exit_timestamp': current_timestamp,
                            'profit_loss': profit_loss,
                            'profit_pct': profit_pct,
                            'size': position_size,
                            'exit_reason': 'take_profit'
                        })
                        
                        logger.debug(f"BACKTEST: TAKE-PROFIT à {exit_price:.6f}, P&L: {profit_loss:.2f} ({profit_pct:.2f}%)")
                        
                        # Mettre à jour le capital et réinitialiser la position
                        current_capital = sale_value
                        current_position = None
                        position_size = 0.0
        
        # Fermer toute position restante à la fin du backtest
        if current_position:
            final_price = price_data[list(price_data.keys())[0]]['close'].iloc[-1]
            exit_price = final_price * (1 - self.slippage)
            sale_value = position_size * exit_price * (1 - self.taker_fee)
            
            # Calculer le P&L
            profit_loss = sale_value - (position_size * current_position['entry_price'])
            profit_pct = (exit_price / current_position['entry_price'] - 1) * 100
            
            # Enregistrer le trade
            self.trades.append({
                'entry_price': current_position['entry_price'],
                'exit_price': exit_price,
                'entry_timestamp': current_position['entry_timestamp'],
                'exit_timestamp': price_data[list(price_data.keys())[0]].index[-1].timestamp(),
                'profit_loss': profit_loss,
                'profit_pct': profit_pct,
                'size': position_size,
                'exit_reason': 'end_of_backtest'
            })
            
            # Mettre à jour le capital
            current_capital = sale_value
            
        # Calculer les métriques de performance
        self.metrics = self._calculate_performance_metrics(portfolio_values)
        self.metrics['final_capital'] = current_capital
        self.metrics['roi'] = (current_capital / self.initial_capital - 1) * 100
        self.metrics['trade_count'] = len(self.trades)
        
        if self.trades:
            self.metrics['win_rate'] = sum(1 for t in self.trades if t['profit_pct'] > 0) / len(self.trades)
            self.metrics['avg_win'] = sum(t['profit_pct'] for t in self.trades if t['profit_pct'] > 0) / max(1, sum(1 for t in self.trades if t['profit_pct'] > 0))
            self.metrics['avg_loss'] = sum(t['profit_pct'] for t in self.trades if t['profit_pct'] <= 0) / max(1, sum(1 for t in self.trades if t['profit_pct'] <= 0))
            
        return {
            'trades': self.trades,
            'metrics': self.metrics,
            'equity_curve': portfolio_values
        }
        
    def _calculate_performance_metrics(self, portfolio_values: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcule les métriques de performance à partir de la courbe d'équité.
        
        Args:
            portfolio_values: Liste des valeurs du portefeuille dans le temps
            
        Returns:
            Dictionnaire des métriques de performance
        """
        if not portfolio_values:
            return {}
            
        # Extraire les valeurs
        values = [entry['value'] for entry in portfolio_values]
        
        # Calculer les rendements
        returns = np.diff(values) / values[:-1]
        
        # Calculer les métriques standard
        metrics = {}
        
        # Drawdown
        max_drawdown = 0
        peak = values[0]
        for value in values:
            if value > peak:
                peak = value
            elif peak > 0:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
                
        metrics['max_drawdown'] = max_drawdown * 100  # En pourcentage
        
        # Volatilité (annualisée)
        if len(returns) > 1:
            volatility = np.std(returns) * np.sqrt(252)  # Supposer 252 jours de trading
            metrics['annual_volatility'] = volatility * 100  # En pourcentage
            
            # Sharpe Ratio (avec un taux sans risque de 0% pour simplifier)
            avg_return = np.mean(returns)
            sharpe = np.sqrt(252) * avg_return / volatility if volatility > 0 else 0
            metrics['sharpe_ratio'] = sharpe
            
        # ROI total
        if values:
            total_roi = (values[-1] / values[0] - 1) * 100
            metrics['total_roi'] = total_roi
            
        return metrics

    def plot_equity_curve(self, save_path: Optional[str] = None) -> None:
        """
        Trace la courbe d'équité du backtest.
        
        Args:
            save_path: Chemin pour sauvegarder le graphique (optionnel)
        """
        try:
            import matplotlib.pyplot as plt
            import datetime
            
            if not self.equity_curve:
                logger.warning("Aucune donnée de courbe d'équité à tracer")
                return
                
            # Convertir les timestamps en dates
            dates = [datetime.datetime.fromtimestamp(entry['timestamp']) for entry in self.equity_curve]
            values = [entry['value'] for entry in self.equity_curve]
            
            # Créer la figure
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(dates, values, label='Valeur du portefeuille')
            
            # Ajouter les trades sur le graphique
            for trade in self.trades:
                entry_date = datetime.datetime.fromtimestamp(trade['entry_timestamp'])
                exit_date = datetime.datetime.fromtimestamp(trade['exit_timestamp'])
                
                # Marquer les entrées et sorties
                if trade['profit_pct'] > 0:
                    ax.plot([exit_date], [trade['exit_price'] * trade['size']], 'g^', markersize=8)  # Marqueur vert pour un gain
                else:
                    ax.plot([exit_date], [trade['exit_price'] * trade['size']], 'rv', markersize=8)  # Marqueur rouge pour une perte
                    
                ax.plot([entry_date], [trade['entry_price'] * trade['size']], 'bo', markersize=6)  # Marqueur bleu pour l'entrée
                
            # Ajouter les labels et la légende
            ax.set_title('Courbe d\'équité du backtest')
            ax.set_xlabel('Date')
            ax.set_ylabel('Valeur du portefeuille')
            ax.grid(True)
            
            # Ajouter les métriques clés
            if self.metrics:
                metrics_text = f"ROI: {self.metrics.get('total_roi', 0):.2f}%\n"
                metrics_text += f"Max drawdown: {self.metrics.get('max_drawdown', 0):.2f}%\n"
                metrics_text += f"Sharpe: {self.metrics.get('sharpe_ratio', 0):.2f}\n"
                metrics_text += f"Win rate: {self.metrics.get('win_rate', 0)*100:.1f}%"
                
                # Ajouter le texte dans un coin du graphique
                ax.text(0.02, 0.97, metrics_text, transform=ax.transAxes, fontsize=9,
                        verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.5))
                        
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Graphique sauvegardé dans {save_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("matplotlib est requis pour tracer la courbe d'équité")
        except Exception as e:
            logger.error(f"Erreur lors du tracé de la courbe d'équité: {e}")

class StrategyValidator:
    """Utilitaire pour valider et comparer différentes stratégies."""
    
    def __init__(self, token_addresses: List[str], market_data_provider=None):
        """
        Initialise le validateur de stratégies.
        
        Args:
            token_addresses: Liste d'adresses de tokens pour la validation
            market_data_provider: Fournisseur de données de marché
        """
        self.token_addresses = token_addresses
        self.market_data_provider = market_data_provider
        self.results = {}
        self.backtest_engine = BacktestEngine()
        
    async def validate_strategy(self, strategy: Strategy, 
                             timeframes: List[str] = ["1h", "4h", "1d"],
                             lookback_days: int = 30) -> Dict[str, Any]:
        """
        Valide une stratégie sur plusieurs tokens et timeframes.
        
        Args:
            strategy: Stratégie à valider
            timeframes: Liste des timeframes à tester
            lookback_days: Nombre de jours d'historique à utiliser
            
        Returns:
            Résultats de validation
        """
        results = {}
        
        for token_address in self.token_addresses:
            token_results = {}
            
            # Récupérer les données historiques pour chaque timeframe
            price_data = {}
            for timeframe in timeframes:
                if timeframe in strategy.timeframes:
                    try:
                        # Obtenir les données historiques via le fournisseur
                        if self.market_data_provider:
                            data = await self.market_data_provider.get_historical_prices(
                                token_address, timeframe, lookback_days * 24)  # Approximation du nombre de périodes
                                
                            # Convertir au format pandas si nécessaire
                            if isinstance(data, list) and data:
                                df = pd.DataFrame(data)
                                df['timestamp'] = pd.to_datetime(df['timestamp'] * 1e9)  # Convertir en timestamp pandas
                                df.set_index('timestamp', inplace=True)
                                price_data[timeframe] = df
                    except Exception as e:
                        logger.error(f"Erreur lors de la récupération des données pour {token_address} ({timeframe}): {e}")
            
            if price_data:
                # Exécuter un backtest pour ce token
                backtest_result = await self.backtest_engine.run_backtest(
                    strategy, price_data, token_address)
                token_results['backtest'] = backtest_result
                
                # Générer un signal actuel pour ce token
                latest_data = {tf: df.iloc[-30:] for tf, df in price_data.items()}  # Utiliser les 30 dernières périodes
                signals = {}
                for tf, df in latest_data.items():
                    signal = await strategy.generate_signal(token_address, df, tf)
                    signals[tf] = signal
                    
                token_results['current_signals'] = signals
                
            results[token_address] = token_results
            
        # Agréger les résultats
        aggregated = self._aggregate_results(results)
        
        # Stocker les résultats
        self.results[strategy.name] = {
            'token_results': results,
            'aggregated': aggregated
        }
        
        return {
            'token_results': results,
            'aggregated': aggregated
        }
        
    def _aggregate_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agrège les résultats de plusieurs tokens.
        
        Args:
            results: Résultats par token
            
        Returns:
            Résultats agrégés
        """
        # Calculer des métriques agrégées
        total_roi = 0.0
        total_trades = 0
        winning_trades = 0
        total_tokens = 0
        max_drawdowns = []
        sharpe_ratios = []
        
        for token, token_results in results.items():
            if 'backtest' in token_results and 'metrics' in token_results['backtest']:
                metrics = token_results['backtest']['metrics']
                total_roi += metrics.get('total_roi', 0)
                total_trades += metrics.get('trade_count', 0)
                winning_trades += metrics.get('win_rate', 0) * metrics.get('trade_count', 0)
                max_drawdowns.append(metrics.get('max_drawdown', 0))
                sharpe_ratios.append(metrics.get('sharpe_ratio', 0))
                total_tokens += 1
                
        # Calculer les moyennes
        if total_tokens > 0:
            return {
                'avg_roi': total_roi / total_tokens,
                'total_trades': total_trades,
                'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
                'avg_max_drawdown': sum(max_drawdowns) / len(max_drawdowns) if max_drawdowns else 0,
                'avg_sharpe': sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0,
                'tokens_tested': total_tokens
            }
        else:
            return {}
            
    async def compare_strategies(self, strategies: List[Strategy]) -> Dict[str, Any]:
        """
        Compare plusieurs stratégies sur les mêmes tokens et timeframes.
        
        Args:
            strategies: Liste des stratégies à comparer
            
        Returns:
            Comparaison des différentes stratégies
        """
        comparison = {}
        
        # Valider chaque stratégie
        for strategy in strategies:
            results = await self.validate_strategy(strategy)
            comparison[strategy.name] = results['aggregated']
            
        return comparison
        
    def generate_report(self, save_path: Optional[str] = None) -> str:
        """
        Génère un rapport complet des résultats de validation.
        
        Args:
            save_path: Chemin pour sauvegarder le rapport
            
        Returns:
            Contenu du rapport
        """
        if not self.results:
            return "Aucun résultat à rapporter. Exécutez d'abord validate_strategy()."
            
        report = "# Rapport de validation des stratégies\n\n"
        
        # Ajouter une section par stratégie
        for strategy_name, result in self.results.items():
            report += f"## {strategy_name}\n\n"
            
            # Résultats agrégés
            aggregated = result.get('aggregated', {})
            report += "### Résultats agrégés\n\n"
            report += f"- ROI moyen: {aggregated.get('avg_roi', 0):.2f}%\n"
            report += f"- Trades totaux: {aggregated.get('total_trades', 0)}\n"
            report += f"- Taux de réussite: {aggregated.get('win_rate', 0)*100:.2f}%\n"
            report += f"- Drawdown max moyen: {aggregated.get('avg_max_drawdown', 0):.2f}%\n"
            report += f"- Ratio de Sharpe moyen: {aggregated.get('avg_sharpe', 0):.2f}\n"
            report += f"- Tokens testés: {aggregated.get('tokens_tested', 0)}\n\n"
            
            # Détails par token
            report += "### Détails par token\n\n"
            
            token_results = result.get('token_results', {})
            for token_address, token_data in token_results.items():
                if 'backtest' in token_data and 'metrics' in token_data['backtest']:
                    metrics = token_data['backtest']['metrics']
                    report += f"#### Token {token_address}\n\n"
                    report += f"- ROI: {metrics.get('total_roi', 0):.2f}%\n"
                    report += f"- Nombre de trades: {metrics.get('trade_count', 0)}\n"
                    report += f"- Taux de réussite: {metrics.get('win_rate', 0)*100:.2f}%\n"
                    report += f"- Gain moyen: {metrics.get('avg_win', 0):.2f}%\n"
                    report += f"- Perte moyenne: {metrics.get('avg_loss', 0):.2f}%\n"
                    report += f"- Drawdown maximum: {metrics.get('max_drawdown', 0):.2f}%\n\n"
            
            report += "---\n\n"
            
        # Si un chemin est spécifié, enregistrer le rapport
        if save_path:
            try:
                with open(save_path, 'w') as f:
                    f.write(report)
                logger.info(f"Rapport enregistré dans {save_path}")
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement du rapport: {e}")
                
        return report

class VolatilityBreakoutStrategy(Strategy):
    """Stratégie de breakout basée sur la volatilité."""
    
    def __init__(self, name: str, timeframes: List[str], params: Dict[str, Any] = None):
        """
        Initialise une stratégie de breakout basée sur la volatilité.
        
        Args:
            name: Nom de la stratégie
            timeframes: Liste des timeframes
            params: Paramètres de la stratégie
        """
        default_params = {
            "atr_period": 14,
            "breakout_multiplier": 2.0,  # Multiple de l'ATR pour considérer un breakout
            "min_consolidation_periods": 5,  # Nombre minimal de périodes de consolidation
            "max_volatility_percentile": 70  # Percentile maximal de volatilité pour la consolidation
        }
        
        # Fusionner avec les paramètres par défaut
        actual_params = default_params.copy()
        if params:
            actual_params.update(params)
            
        super().__init__(name, timeframes, actual_params)
        
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        """
        Génère un signal basé sur un breakout de volatilité.
        
        Args:
            token_address: Adresse du token
            price_data: DataFrame des données de prix
            timeframe: Timeframe actuel
            
        Returns:
            Signal généré
        """
        if price_data.empty or len(price_data) < self.params["atr_period"] + 10:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.0,
                timestamp=time.time(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={}
            )
            
        # Calculer l'ATR
        atr = self._calculate_atr(price_data, period=self.params["atr_period"])
        
        # Obtenir les prix récents
        current_price = price_data['close'].iloc[-1]
        previous_price = price_data['close'].iloc[-2]
        
        # Calculer les bornes supérieures et inférieures
        high_price = price_data['high'].iloc[-self.params["min_consolidation_periods"]-1:-1].max()
        low_price = price_data['low'].iloc[-self.params["min_consolidation_periods"]-1:-1].min()
        
        # Vérifier si le marché était en consolidation (plage de prix réduite)
        price_range = high_price - low_price
        avg_price = (high_price + low_price) / 2
        normalized_range = price_range / avg_price
        
        # Calculer l'ATR normalisé
        normalized_atr = atr / current_price
        
        # Vérifier si le marché était en consolidation
        is_consolidation = self._detect_consolidation(price_data)
        
        # Calculer le seuil de breakout
        breakout_threshold = atr * self.params["breakout_multiplier"]
        
        # Détecter un breakout
        signal_type = SignalType.NEUTRAL
        confidence = 0.1
        metadata = {
            "atr": atr,
            "normalized_atr": normalized_atr,
            "price_range": price_range,
            "normalized_range": normalized_range,
            "is_consolidation": is_consolidation,
            "current_price": current_price,
            "high_price": high_price,
            "low_price": low_price
        }
        
        if is_consolidation:
            # Breakout à la hausse
            if current_price > high_price + breakout_threshold:
                signal_type = SignalType.BUY
                confidence = min(1.0, (current_price - high_price) / breakout_threshold)
                metadata["breakout_direction"] = "up"
            # Breakout à la baisse
            elif current_price < low_price - breakout_threshold:
                signal_type = SignalType.SELL
                confidence = min(1.0, (low_price - current_price) / breakout_threshold)
                metadata["breakout_direction"] = "down"
                
        # Calculer les niveaux de stop-loss et take-profit
        stop_loss = None
        take_profit = None
        
        if signal_type == SignalType.BUY:
            stop_loss = low_price  # Utiliser le plus bas récent comme stop-loss
            take_profit = current_price + 2 * (current_price - stop_loss)  # Risk/Reward 1:2
        elif signal_type == SignalType.SELL:
            stop_loss = high_price  # Utiliser le plus haut récent comme stop-loss
            take_profit = current_price - 2 * (stop_loss - current_price)  # Risk/Reward 1:2
            
        # Créer le signal
        signal = Signal(
            type=signal_type,
            confidence=confidence,
            timestamp=time.time(),
            token_address=token_address,
            timeframe=timeframe,
            strategy_name=self.name,
            metadata=metadata,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Ajouter à l'historique des signaux
        self.add_signal(signal)
        
        return signal
        
    def _detect_consolidation(self, price_data: pd.DataFrame) -> bool:
        """
        Détecte si le marché est en phase de consolidation.
        
        Args:
            price_data: DataFrame des données de prix
            
        Returns:
            True si le marché est en consolidation
        """
        # Calculer la volatilité récente
        returns = price_data['close'].pct_change().iloc[-self.params["min_consolidation_periods"]:]
        recent_volatility = returns.std()
        
        # Calculer l'historique de volatilité pour comparer
        historical_window = min(100, len(price_data) - self.params["min_consolidation_periods"])
        historical_returns = price_data['close'].pct_change().iloc[:-self.params["min_consolidation_periods"]]
        historical_volatility = [historical_returns.iloc[i:i+self.params["min_consolidation_periods"]].std() 
                              for i in range(0, historical_window, self.params["min_consolidation_periods"])]
        
        # Calculer le percentile de la volatilité récente
        if historical_volatility:
            volatility_percentile = sum(v > recent_volatility for v in historical_volatility) / len(historical_volatility) * 100
        else:
            volatility_percentile = 50  # Valeur par défaut
            
        # Vérifier si la volatilité récente est faible (indiquant une consolidation)
        return volatility_percentile < self.params["max_volatility_percentile"]
        
    def _calculate_atr(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calcule l'Average True Range."""
        high = price_data['high']
        low = price_data['low']
        close = price_data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr

class PatternRecognitionStrategy(Strategy):
    """Stratégie basée sur la reconnaissance de patterns de prix."""
    
    def __init__(self, name: str, timeframes: List[str], params: Dict[str, Any] = None):
        """
        Initialise une stratégie de reconnaissance de patterns.
        
        Args:
            name: Nom de la stratégie
            timeframes: Liste des timeframes
            params: Paramètres de la stratégie
        """
        default_params = {
            "pattern_window": 5,  # Taille de la fenêtre pour la reconnaissance de patterns
            "similarity_threshold": 0.8,  # Seuil de similarité pour reconnaître un pattern
            "min_pattern_occurrences": 3  # Nombre minimum d'occurrences précédentes du pattern
        }
        
        # Fusionner avec les paramètres par défaut
        actual_params = default_params.copy()
        if params:
            actual_params.update(params)
            
        super().__init__(name, timeframes, actual_params)
        
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        """
        Génère un signal basé sur la reconnaissance de patterns de prix.
        
        Args:
            token_address: Adresse du token
            price_data: DataFrame des données de prix
            timeframe: Timeframe actuel
            
        Returns:
            Signal généré
        """
        if price_data.empty or len(price_data) < self.params["pattern_window"] * 5:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.0,
                timestamp=time.time(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={}
            )
            
        # Extraire le pattern récent
        recent_pattern = self._extract_pattern(price_data.iloc[-self.params["pattern_window"]:])
        
        # Rechercher des occurrences similaires du pattern dans l'historique
        similar_patterns, outcomes = self._find_similar_patterns(price_data, recent_pattern)
        
        # Si pas assez de patterns similaires trouvés, retourner un signal neutre
        if len(similar_patterns) < self.params["min_pattern_occurrences"]:
            return Signal(
                type=SignalType.NEUTRAL,
                confidence=0.1,
                timestamp=time.time(),
                token_address=token_address,
                timeframe=timeframe,
                strategy_name=self.name,
                metadata={"patterns_found": len(similar_patterns)}
            )
            
        # Analyser les résultats historiques pour prédire l'évolution future
        up_count = sum(1 for outcome in outcomes if outcome > 0)
        down_count = sum(1 for outcome in outcomes if outcome < 0)
        
        # Calculer le score d'orientation et la confiance
        if up_count > down_count and up_count / len(outcomes) > 0.6:
            signal_type = SignalType.BUY
            confidence = min(0.95, up_count / len(outcomes))
        elif down_count > up_count and down_count / len(outcomes) > 0.6:
            signal_type = SignalType.SELL
            confidence = min(0.95, down_count / len(outcomes))
        else:
            signal_type = SignalType.NEUTRAL
            confidence = 0.2
            
        # Calculer le mouvement de prix attendu
        avg_outcome = sum(outcomes) / len(outcomes) if outcomes else 0
        current_price = price_data['close'].iloc[-1]
        
        # Calculer les niveaux de stop-loss et take-profit
        stop_loss = None
        take_profit = None
        
        if signal_type == SignalType.BUY and avg_outcome > 0:
            stop_loss = current_price * (1 - 0.5 * abs(avg_outcome))
            take_profit = current_price * (1 + abs(avg_outcome))
        elif signal_type == SignalType.SELL and avg_outcome < 0:
            stop_loss = current_price * (1 + 0.5 * abs(avg_outcome))
            take_profit = current_price * (1 - abs(avg_outcome))
            
        # Créer le signal
        metadata = {
            "patterns_found": len(similar_patterns),
            "up_probability": up_count / len(outcomes) if outcomes else 0,
            "down_probability": down_count / len(outcomes) if outcomes else 0,
            "avg_outcome": avg_outcome,
            "current_price": current_price
        }
        
        signal = Signal(
            type=signal_type,
            confidence=confidence,
            timestamp=time.time(),
            token_address=token_address,
            timeframe=timeframe,
            strategy_name=self.name,
            metadata=metadata,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Ajouter à l'historique des signaux
        self.add_signal(signal)
        
        return signal
        
    def _extract_pattern(self, window_data: pd.DataFrame) -> np.ndarray:
        """
        Extrait un pattern normalisé des données de prix.
        
        Args:
            window_data: DataFrame contenant une fenêtre de données de prix
            
        Returns:
            Array numpy contenant le pattern normalisé
        """
        # Utiliser les prix de clôture normalisés comme pattern
        closes = window_data['close'].values
        
        # Normaliser le pattern entre 0 et 1
        min_price = closes.min()
        max_price = closes.max()
        range_price = max_price - min_price
        
        if range_price == 0:
            # Éviter la division par zéro
            return np.zeros_like(closes)
            
        normalized_pattern = (closes - min_price) / range_price
        
        return normalized_pattern
        
    def _find_similar_patterns(self, price_data: pd.DataFrame, recent_pattern: np.ndarray) -> Tuple[List[np.ndarray], List[float]]:
        """
        Recherche des patterns similaires dans l'historique et leurs résultats.
        
        Args:
            price_data: DataFrame contenant l'historique des prix
            recent_pattern: Pattern récent à rechercher
            
        Returns:
            Tuple (patterns similaires trouvés, résultats après ces patterns)
        """
        window_size = len(recent_pattern)
        similar_patterns = []
        outcomes = []
        
        # Parcourir l'historique des données
        for i in range(len(price_data) - window_size * 2):
            # Extraire le pattern historique
            historical_window = price_data.iloc[i:i+window_size]
            historical_pattern = self._extract_pattern(historical_window)
            
            # Calculer la similarité (corrélation)
            correlation = np.corrcoef(recent_pattern, historical_pattern)[0, 1]
            
            # Si suffisamment similaire, ajouter à la liste
            if correlation > self.params["similarity_threshold"]:
                similar_patterns.append(historical_pattern)
                
                # Calculer l'évolution du prix après ce pattern (sur la même durée que le pattern)
                start_price = price_data['close'].iloc[i+window_size-1]
                end_price = price_data['close'].iloc[i+window_size*2-1]
                outcome = (end_price / start_price) - 1  # Rendement en %
                
                outcomes.append(outcome)
                
        return similar_patterns, outcomes

class StrategyOptimizer:
    """
    Utilitaire pour optimiser les paramètres de stratégies de trading
    en utilisant des techniques avancées d'optimisation.
    """
    
    def __init__(self, strategy_class: Type[Strategy], price_data: Dict[str, pd.DataFrame], 
               token_address: str, timeframes: List[str]):
        """
        Initialise l'optimiseur de stratégie.
        
        Args:
            strategy_class: Classe de la stratégie à optimiser
            price_data: Données de prix par timeframe
            token_address: Adresse du token
            timeframes: Liste des timeframes à utiliser
        """
        self.strategy_class = strategy_class
        self.price_data = price_data
        self.token_address = token_address
        self.timeframes = timeframes
        self.backtest_engine = BacktestEngine()
        
    async def optimize_grid_search(self, param_grid: Dict[str, List[Any]], 
                               metric: str = "roi") -> Tuple[Dict[str, Any], float]:
        """
        Optimise les paramètres par recherche exhaustive (grid search).
        
        Args:
            param_grid: Grille de paramètres à tester
            metric: Métrique à optimiser ('roi', 'sharpe', 'win_rate', etc.)
            
        Returns:
            Tuple (meilleurs paramètres, meilleur score)
        """
        best_params = None
        best_score = float('-inf')
        
        # Générer toutes les combinaisons de paramètres
        param_combinations = self._generate_parameter_combinations(param_grid)
        logger.info(f"Optimisation avec grid search: {len(param_combinations)} combinaisons à tester")
        
        # Tester chaque combinaison
        for i, params in enumerate(param_combinations):
            # Créer une nouvelle instance de stratégie avec ces paramètres
            strategy = self.strategy_class(f"test_strategy_{i}", self.timeframes, params)
            
            # Effectuer un backtest
            result = await self._run_backtest(strategy)
            
            # Extraire la métrique spécifiée du résultat
            score = self._extract_metric(result, metric)
            
            # Mettre à jour si c'est le meilleur résultat jusqu'à présent
            if score > best_score:
                best_score = score
                best_params = params.copy()
                logger.info(f"Nouvelle meilleure combinaison trouvée: score={best_score:.4f}, params={best_params}")
                
        return best_params, best_score
        
    async def optimize_genetic_algorithm(self, param_ranges: Dict[str, Tuple[float, float]], 
                                     population_size: int = 20, generations: int = 10, 
                                     mutation_rate: float = 0.1, metric: str = "roi") -> Tuple[Dict[str, Any], float]:
        """
        Optimise les paramètres en utilisant un algorithme génétique.
        
        Args:
            param_ranges: Plages de paramètres (min, max)
            population_size: Taille de la population
            generations: Nombre de générations
            mutation_rate: Taux de mutation
            metric: Métrique à optimiser
            
        Returns:
            Tuple (meilleurs paramètres, meilleur score)
        """
        # Initialiser la population avec des paramètres aléatoires
        population = []
        for _ in range(population_size):
            params = {param: np.random.uniform(range_min, range_max) 
                    for param, (range_min, range_max) in param_ranges.items()}
            population.append(params)
            
        best_params = None
        best_score = float('-inf')
        
        # Évoluer sur plusieurs générations
        for generation in range(generations):
            logger.info(f"Génération {generation+1}/{generations}")
            
            # Évaluer la population actuelle
            scores = []
            for i, params in enumerate(population):
                strategy = self.strategy_class(f"ga_strategy_{generation}_{i}", self.timeframes, params)
                result = await self._run_backtest(strategy)
                score = self._extract_metric(result, metric)
                scores.append(score)
                
                # Mettre à jour le meilleur résultat global
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    logger.info(f"Nouvelle meilleure solution: score={best_score:.4f}, params={best_params}")
            
            # Créer la nouvelle génération
            new_population = []
            
            # Élitisme: conserver les meilleurs individus
            elite_size = max(1, population_size // 10)
            elite_indices = np.argsort(scores)[-elite_size:]
            for idx in elite_indices:
                new_population.append(population[idx])
                
            # Compléter la population avec de nouveaux individus
            while len(new_population) < population_size:
                # Sélection par tournoi
                parent1 = self._tournament_selection(population, scores)
                parent2 = self._tournament_selection(population, scores)
                
                # Croisement
                child = self._crossover(parent1, parent2)
                
                # Mutation
                child = self._mutate(child, param_ranges, mutation_rate)
                
                new_population.append(child)
                
            population = new_population
            
        return best_params, best_score
        
    def _generate_parameter_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Génère toutes les combinaisons de paramètres."""
        import itertools
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        return [dict(zip(keys, combo)) for combo in combinations]
        
    async def _run_backtest(self, strategy: Strategy) -> Dict[str, Any]:
        """Exécute un backtest pour une stratégie donnée."""
        result = {}
        
        for timeframe in strategy.timeframes:
            if timeframe in self.price_data:
                # Filtrer les données de prix pour le timeframe actuel
                timeframe_data = {timeframe: self.price_data[timeframe]}
                
                # Exécuter le backtest
                backtest_result = await self.backtest_engine.run_backtest(
                    strategy, timeframe_data, self.token_address
                )
                
                # Fusionner les résultats
                if not result:
                    result = backtest_result
                else:
                    # Fusionner les trades
                    result["trades"].extend(backtest_result["trades"])
                    
                    # Mettre à jour les métriques (moyennes pondérées)
                    for key, value in backtest_result["metrics"].items():
                        if key in result["metrics"]:
                            result["metrics"][key] = (result["metrics"][key] + value) / 2
                        else:
                            result["metrics"][key] = value
                    
        return result
        
    def _extract_metric(self, result: Dict[str, Any], metric: str) -> float:
        """
        Extrait une métrique spécifique du résultat de backtest.
        
        Args:
            result: Résultat du backtest
            metric: Nom de la métrique à extraire
            
        Returns:
            Valeur de la métrique
        """
        # Métriques basiques
        if metric == "roi":
            return result.get("metrics", {}).get("total_roi", 0)
        elif metric == "sharpe":
            return result.get("metrics", {}).get("sharpe_ratio", 0)
        elif metric == "win_rate":
            return result.get("metrics", {}).get("win_rate", 0)
        elif metric == "profit_factor":
            avg_win = result.get("metrics", {}).get("avg_win", 0)
            avg_loss = abs(result.get("metrics", {}).get("avg_loss", 1))
            win_rate = result.get("metrics", {}).get("win_rate", 0)
            return (win_rate * avg_win) / ((1 - win_rate) * avg_loss) if avg_loss > 0 else 0
            
        # Métriques composites
        elif metric == "composite":
            # Combinaison de plusieurs métriques
            roi = result.get("metrics", {}).get("total_roi", 0)
            sharpe = result.get("metrics", {}).get("sharpe_ratio", 0)
            win_rate = result.get("metrics", {}).get("win_rate", 0)
            drawdown = result.get("metrics", {}).get("max_drawdown", 100)
            
            # Formule composite personnalisée
            return roi * 0.4 + sharpe * 0.3 + win_rate * 0.2 - (drawdown / 100) * 0.1
            
        else:
            # Par défaut, renvoyer 0
            return 0
            
    def _tournament_selection(self, population: List[Dict[str, Any]], scores: List[float], tournament_size: int = 3) -> Dict[str, Any]:
        """
        Sélectionne un individu par tournoi.
        
        Args:
            population: Liste des individus
            scores: Liste des scores correspondants
            tournament_size: Taille du tournoi
            
        Returns:
            Individu sélectionné
        """
        # Sélectionner des individus aléatoires pour le tournoi
        indices = np.random.choice(len(population), tournament_size, replace=False)
        tournament_scores = [scores[i] for i in indices]
        
        # Sélectionner le meilleur
        winner_idx = indices[np.argmax(tournament_scores)]
        return population[winner_idx]
        
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue un croisement entre deux parents.
        
        Args:
            parent1: Premier parent
            parent2: Deuxième parent
            
        Returns:
            Enfant issu du croisement
        """
        child = {}
        for param in parent1.keys():
            # Croisement aléatoire pour chaque paramètre
            if np.random.random() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child
        
    def _mutate(self, individual: Dict[str, Any], param_ranges: Dict[str, Tuple[float, float]], mutation_rate: float) -> Dict[str, Any]:
        """
        Applique une mutation à un individu.
        
        Args:
            individual: Individu à muter
            param_ranges: Plages de paramètres
            mutation_rate: Taux de mutation
            
        Returns:
            Individu muté
        """
        mutated = individual.copy()
        
        for param, value in mutated.items():
            # Appliquer une mutation avec une certaine probabilité
            if np.random.random() < mutation_rate:
                # Obtenir la plage pour ce paramètre
                range_min, range_max = param_ranges[param]
                
                # Générer une nouvelle valeur
                mutated[param] = np.random.uniform(range_min, range_max)
                
        return mutated

class BaseStrategy:
    """Abstract base class for all trading strategies."""
    
    def analyze(self, market_data: pd.DataFrame, **kwargs) -> dict:
        """Analyzes market data and returns analysis results."""
        raise NotImplementedError
        
    def generate_signal(self, analysis: dict, **kwargs) -> dict:
        """Generates trading signal from analysis.

        Returns:
            dict: e.g., {'signal': 'buy'/'sell'/'hold', 'confidence': 0.75, 'target_price': 105.0, 'stop_loss': 95.0}
                  Signal should be one of 'buy', 'sell', or 'hold'.
                  Confidence is a float between 0 and 1.
                  target_price and stop_loss are optional.
        """
        raise NotImplementedError
        
    def get_parameters(self) -> dict:
        """Returns strategy parameters."""
        raise NotImplementedError

    def get_name(self) -> str:
        """Returns the name of the strategy."""
        return self.__class__.__name__