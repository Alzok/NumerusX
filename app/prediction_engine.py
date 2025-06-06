import logging
import time
import numpy as np
import pandas as pd
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("prediction_engine")

@dataclass
class PredictionResult:
    """Classe représentant le résultat d'une prédiction."""
    target_price: float
    confidence: float  # 0-1
    timeframe: str
    direction: str  # "up", "down", "sideways"
    supporting_factors: Dict[str, float]
    model_name: str
    timestamp: float

class MarketRegimeClassifier:
    """Classe pour identifier le régime de marché actuel."""
    
    TREND_REGIME = "trending"
    RANGE_REGIME = "ranging"
    VOLATILE_REGIME = "volatile"
    
    def __init__(self, window_size: int = 20):
        """
        Initialise le classificateur de régime.
        
        Args:
            window_size: Taille de la fenêtre d'analyse
        """
        self.window_size = window_size
        
    def classify(self, price_data: pd.DataFrame) -> str:
        """
        Classifie le régime de marché actuel.
        
        Args:
            price_data: DataFrame contenant les données de prix
            
        Returns:
            Type de régime de marché
        """
        if len(price_data) < self.window_size:
            return self.RANGE_REGIME  # Par défaut
            
        # Calculer l'ADX (Average Directional Index) pour mesurer la force de la tendance
        adx = self._calculate_adx(price_data)
        
        # Calculer la volatilité (ATR/Prix moyen)
        atr = self._calculate_atr(price_data)
        avg_price = price_data['close'].mean()
        volatility = atr / avg_price
        
        # Calculer la largeur du range (plus haut - plus bas) / prix moyen
        highest = price_data['high'].max()
        lowest = price_data['low'].min()
        range_width = (highest - lowest) / avg_price
        
        # Classifier le régime
        if adx > 25:
            return self.TREND_REGIME
        elif volatility > 0.03:  # 3% de volatilité quotidienne
            return self.VOLATILE_REGIME
        else:
            return self.RANGE_REGIME
            
    def _calculate_adx(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calcule l'ADX (Average Directional Index)."""
        # Implémentation simplifiée de l'ADX
        df = price_data.copy()
        
        # Calcul du True Range
        df['tr0'] = abs(df['high'] - df['low'])
        df['tr1'] = abs(df['high'] - df['close'].shift(1))
        df['tr2'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
        
        # Calcul du Directional Movement
        df['up_move'] = df['high'] - df['high'].shift(1)
        df['down_move'] = df['low'].shift(1) - df['low']
        
        df['plus_dm'] = 0
        df.loc[(df['up_move'] > df['down_move']) & (df['up_move'] > 0), 'plus_dm'] = df['up_move']
        
        df['minus_dm'] = 0
        df.loc[(df['down_move'] > df['up_move']) & (df['down_move'] > 0), 'minus_dm'] = df['down_move']
        
        # Calcul des indicateurs exponentiels
        df['tr_ema'] = df['tr'].ewm(span=period, adjust=False).mean()
        df['plus_di'] = 100 * (df['plus_dm'].ewm(span=period, adjust=False).mean() / df['tr_ema'])
        df['minus_di'] = 100 * (df['minus_dm'].ewm(span=period, adjust=False).mean() / df['tr_ema'])
        
        # Calcul du DX puis de l'ADX
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].ewm(span=period, adjust=False).mean()
        
        return df['adx'].iloc[-1]
        
    def _calculate_atr(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calcule l'ATR (Average True Range)."""
        df = price_data.copy()
        
        # Calcul du True Range
        df['tr0'] = abs(df['high'] - df['low'])
        df['tr1'] = abs(df['high'] - df['close'].shift(1))
        df['tr2'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
        
        # Calcul de l'ATR
        df['atr'] = df['tr'].rolling(window=period).mean()
        
        return df['atr'].iloc[-1]

class PricePredictor:
    """Classe principale pour les prévisions de prix basées sur l'apprentissage automatique."""
    
    def __init__(self, model_dir: str = "models", data_dir: str = "data"):
        """
        Initialise le prédicteur de prix.
        
        Args:
            model_dir: Répertoire de stockage des modèles
            data_dir: Répertoire des données historiques
        """
        self.model_dir = model_dir
        self.data_dir = data_dir
        self.models = {}
        self.scalers = {}
        self.features = {}
        self.market_regime_classifier = MarketRegimeClassifier()
        self.last_training = {}
        
        # Créer les répertoires si nécessaire
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        
        # Chargement des modèles existants
        self._load_models()

    def _load_models(self) -> None:
        """Charge les modèles préentraînés."""
        try:
            for model_file in os.listdir(self.model_dir):
                if model_file.endswith('.joblib'):
                    model_name = model_file.split('.')[0]
                    model_path = os.path.join(self.model_dir, model_file)
                    
                    # Charger le modèle
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"Modèle chargé: {model_name}")
                    
                    # Charger le scaler associé
                    scaler_path = os.path.join(self.model_dir, f"{model_name}_scaler.joblib")
                    if os.path.exists(scaler_path):
                        self.scalers[model_name] = joblib.load(scaler_path)
                    
                    # Charger les caractéristiques
                    features_path = os.path.join(self.model_dir, f"{model_name}_features.json")
                    if os.path.exists(features_path):
                        with open(features_path, 'r') as f:
                            self.features[model_name] = json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")

    async def predict_price(self, token_address: str, timeframe: str = "1h") -> PredictionResult:
        """
        Prédit le prix futur d'un token.
        
        Args:
            token_address: Adresse du token
            timeframe: Intervalle de temps (1m, 5m, 15m, 1h, 4h, 1d)
            
        Returns:
            Résultat de la prédiction
        """
        try:
            # Identifier le bon modèle pour ce token et cette période
            model_name = f"{token_address}_{timeframe}_predictor"
            
            if (model_name not in self.models) and (f"generic_{timeframe}_predictor" not in self.models):
                # Si aucun modèle spécifique n'est disponible, utiliser un modèle générique
                model_name = f"generic_{timeframe}_predictor"
                if model_name not in self.models:
                    # Entraîner un nouveau modèle générique
                    logger.info(f"Aucun modèle disponible pour {token_address} sur {timeframe}, création d'un nouveau modèle...")
                    await self.train_model(token_address, timeframe)
            
            # Obtenir les données récentes pour la prédiction
            recent_data = await self._get_recent_data(token_address, timeframe)
            if recent_data.empty:
                raise ValueError(f"Pas assez de données pour {token_address} sur {timeframe}")
                
            # Préparer les caractéristiques pour la prédiction
            features_df = self._prepare_features(recent_data)
            
            # Standardiser les caractéristiques
            if model_name in self.scalers:
                X = self.scalers[model_name].transform(features_df)
            else:
                X = features_df.values
                
            # Faire la prédiction
            model = self.models[model_name]
            prediction = model.predict(X)
            
            # Calculer la confiance de la prédiction
            confidence = self._calculate_confidence(model, X, recent_data)
            
            # Déterminer la direction
            current_price = recent_data['close'].iloc[-1]
            predicted_price = prediction[0]
            direction = "up" if predicted_price > current_price * 1.01 else "down" if predicted_price < current_price * 0.99 else "sideways"
            
            # Déterminer les facteurs de support
            supporting_factors = self._determine_supporting_factors(model, features_df)
            
            return PredictionResult(
                target_price=float(predicted_price),
                confidence=float(confidence),
                timeframe=timeframe,
                direction=direction,
                supporting_factors=supporting_factors,
                model_name=model_name,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction pour {token_address} sur {timeframe}: {e}")
            raise

    async def train_model(self, token_address: str, timeframe: str) -> bool:
        """
        Entraîne ou met à jour un modèle de prédiction.
        
        Args:
            token_address: Adresse du token
            timeframe: Intervalle de temps
            
        Returns:
            True si l'entraînement a réussi
        """
        try:
            # Générer un nom pour ce modèle
            model_name = f"{token_address}_{timeframe}_predictor"
            
            # Vérifier si un entraînement récent a eu lieu
            if model_name in self.last_training:
                last_time = self.last_training[model_name]
                if time.time() - last_time < 3600:  # Limite à un entraînement par heure
                    logger.info(f"Entraînement ignoré pour {model_name}, dernier entraînement il y a moins d'une heure")
                    return False
            
            # Obtenir les données historiques
            historical_data = await self._get_historical_data(token_address, timeframe)
            if len(historical_data) < 100:  # Besoin de suffisamment de données
                logger.warning(f"Pas assez de données pour entraîner un modèle pour {token_address} sur {timeframe}")
                return False
                
            # Préparer les caractéristiques et les cibles
            features_df = self._prepare_features(historical_data)
            targets = self._prepare_targets(historical_data)
            
            # Division en ensembles d'entraînement et de test
            X_train, X_test, y_train, y_test = train_test_split(features_df, targets, test_size=0.2, shuffle=False)
            
            # Standardisation des caractéristiques
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Choisir l'algorithme approprié selon le régime de marché
            market_regime = self.market_regime_classifier.classify(historical_data)
            model = self._select_model_by_regime(market_regime)
            
            # Entraînement du modèle
            model.fit(X_train_scaled, y_train)
            
            # Évaluation du modèle
            train_predictions = model.predict(X_train_scaled)
            test_predictions = model.predict(X_test_scaled)
            
            train_rmse = np.sqrt(mean_squared_error(y_train, train_predictions))
            test_rmse = np.sqrt(mean_squared_error(y_test, test_predictions))
            test_r2 = r2_score(y_test, test_predictions)
            
            logger.info(f"Modèle {model_name} entraîné. RMSE train: {train_rmse:.4f}, RMSE test: {test_rmse:.4f}, R²: {test_r2:.4f}")
            
            # Sauvegarder le modèle et les métadonnées associées
            model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
            scaler_path = os.path.join(self.model_dir, f"{model_name}_scaler.joblib")
            features_path = os.path.join(self.model_dir, f"{model_name}_features.json")
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            with open(features_path, 'w') as f:
                json.dump(list(features_df.columns), f)
                
            # Mettre à jour les dictionnaires en mémoire
            self.models[model_name] = model
            self.scalers[model_name] = scaler
            self.features[model_name] = list(features_df.columns)
            self.last_training[model_name] = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle pour {token_address} sur {timeframe}: {e}")
            return False

    def _select_model_by_regime(self, market_regime: str):
        """
        Sélectionne le type de modèle approprié en fonction du régime de marché.
        
        Args:
            market_regime: Type de régime de marché ('trending', 'ranging', 'volatile')
            
        Returns:
            Instance de modèle scikit-learn appropriée
        """
        if market_regime == MarketRegimeClassifier.TREND_REGIME:
            # Pour les marchés avec tendance, un gradient boosting fonctionne bien
            return GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                loss='huber'  # Moins sensible aux valeurs aberrantes
            )
        elif market_regime == MarketRegimeClassifier.VOLATILE_REGIME:
            # Pour les marchés volatils, un réseau de neurones peut mieux capturer la complexité
            return MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                alpha=0.001,
                random_state=42,
                max_iter=1000
            )
        else:  # RANGE_REGIME ou par défaut
            # Pour les marchés sans tendance claire, Random Forest est souvent stable
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=8,
                random_state=42
            )

    async def _get_historical_data(self, token_address: str, timeframe: str) -> pd.DataFrame:
        """
        Obtient les données historiques pour un token.
        
        Args:
            token_address: Adresse du token
            timeframe: Intervalle de temps
            
        Returns:
            DataFrame contenant les données historiques
        """
        try:
            # Cette méthode nécessiterait d'obtenir des données historiques depuis une API
            # Ici, nous simulons la récupération des données
            file_path = os.path.join(self.data_dir, f"{token_address}_{timeframe}.csv")
            
            # Vérifier si les données sont déjà disponibles localement
            if os.path.exists(file_path):
                return pd.read_csv(file_path, parse_dates=['timestamp'])
            
            # Sinon, récupérer les données depuis une API externe
            # Dans cet exemple, nous simulons des données (à remplacer par un appel API réel)
            # Par exemple, en utilisant la classe MarketDataProvider
            
            # Simulation de données
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            dates = pd.date_range(start=start_date, end=end_date, freq='H')
            np.random.seed(42)
            
            price = 100
            prices = []
            for _ in range(len(dates)):
                change = np.random.normal(0, 0.01)
                price *= (1 + change)
                prices.append(price)
                
            df = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
                'close': [p * (1 + np.random.normal(0, 0.002)) for p in prices],
                'volume': [abs(np.random.normal(1000000, 500000)) for _ in prices]
            })
            
            # Sauvegarder les données pour une utilisation future
            df.to_csv(file_path, index=False)
            
            return df
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données historiques: {e}")
            return pd.DataFrame()
            
    async def _get_recent_data(self, token_address: str, timeframe: str) -> pd.DataFrame:
        """
        Obtient les données récentes pour un token.
        
        Args:
            token_address: Adresse du token
            timeframe: Intervalle de temps
            
        Returns:
            DataFrame contenant les données récentes
        """
        # Obtenir les données historiques et extraire les plus récentes
        historical_data = await self._get_historical_data(token_address, timeframe)
        
        # Prendre les 50 dernières observations pour la prédiction
        return historical_data.tail(50)
        
    def _prepare_features(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prépare les caractéristiques pour l'analyse et la prédiction.
        
        Args:
            price_data: DataFrame contenant les données de prix
            
        Returns:
            DataFrame contenant les caractéristiques extraites
        """
        # Créer une copie pour éviter de modifier les données originales
        df = price_data.copy()
        
        # Caractéristiques de base
        # Rendements (returns)
        df['return_1'] = df['close'].pct_change(1)
        df['return_5'] = df['close'].pct_change(5)
        df['return_10'] = df['close'].pct_change(10)
        
        # Volatilité
        df['volatility_5'] = df['return_1'].rolling(window=5).std()
        df['volatility_10'] = df['return_1'].rolling(window=10).std()
        
        # Moyennes mobiles
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        
        # Moyennes mobiles exponentielles
        df['ema_5'] = df['close'].ewm(span=5, adjust=False).mean()
        df['ema_10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        
        # Indicateurs techniques
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD (Moving Average Convergence Divergence)
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Ratio volume / prix
        df['volume_price_ratio'] = df['volume'] / df['close']
        
        # Caractéristiques de tendance
        df['trend_5_10'] = df['sma_5'] / df['sma_10'] - 1
        df['trend_10_20'] = df['sma_10'] / df['sma_20'] - 1
        
        # Distances aux supports/résistances
        df['dist_to_upper'] = (df['bb_upper'] - df['close']) / df['close']
        df['dist_to_lower'] = (df['close'] - df['bb_lower']) / df['close']
        
        # Supprimer les lignes avec des valeurs manquantes
        df = df.dropna()
        
        # Exclure les colonnes non nécessaires pour les features
        exclude_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        feature_columns = [col for col in df.columns if col not in exclude_columns]
        
        return df[feature_columns].iloc[-1:].reset_index(drop=True)
        
    def _prepare_targets(self, price_data: pd.DataFrame) -> np.ndarray:
        """
        Prépare les cibles pour l'entraînement.
        
        Args:
            price_data: DataFrame contenant les données de prix
            
        Returns:
            Tableau numpy des valeurs cibles
        """
        # Préparer les prix futurs comme cibles
        # Par exemple, prédire le prix de clôture dans 5 périodes
        df = price_data.copy()
        df['target'] = df['close'].shift(-5)  # Le prix dans 5 périodes
        df = df.dropna()
        
        return df['target'].values
        
    def _calculate_confidence(self, model, X: np.ndarray, recent_data: pd.DataFrame) -> float:
        """
        Calcule la confiance de la prédiction.
        
        Args:
            model: Modèle de prédiction
            X: Caractéristiques d'entrée
            recent_data: Données récentes
            
        Returns:
            Score de confiance entre 0 et 1
        """
        # Plusieurs facteurs peuvent influencer la confiance:
        confidence = 0.5  # Valeur de base
        
        # 1. Volatilité récente (plus faible = plus confiant)
        if 'volatility_10' in recent_data.columns:
            recent_volatility = recent_data['volatility_10'].iloc[-1]
            # Normaliser entre 0 et 0.2
            vol_factor = max(0, 0.2 * (1 - min(recent_volatility * 10, 1)))
            confidence += vol_factor
            
        # 2. Cohérence des indicateurs (si disponibles)
        trend_indicators = []
        if 'rsi_14' in recent_data.columns:
            rsi = recent_data['rsi_14'].iloc[-1]
            trend_indicators.append(1 if rsi > 50 else -1)
            
        if 'macd' in recent_data.columns and 'macd_signal' in recent_data.columns:
            macd_trend = 1 if recent_data['macd'].iloc[-1] > recent_data['macd_signal'].iloc[-1] else -1
            trend_indicators.append(macd_trend)
            
        if 'ema_5' in recent_data.columns and 'ema_20' in recent_data.columns:
            ema_trend = 1 if recent_data['ema_5'].iloc[-1] > recent_data['ema_20'].iloc[-1] else -1
            trend_indicators.append(ema_trend)
            
        if trend_indicators:
            # Calculer la cohérence (tous les indicateurs dans la même direction)
            agreement = abs(sum(trend_indicators)) / len(trend_indicators)
            confidence += 0.2 * agreement
            
        # 3. Performance historique du modèle (si disponible)
        if hasattr(model, 'feature_importances_'):
            # Un modèle avec des importances de caractéristiques plus distribuées est généralement plus fiable
            importances = model.feature_importances_
            importance_entropy = -sum((imp * np.log(imp) if imp > 0 else 0) for imp in importances)
            # Normaliser à 0.1 max
            confidence += min(0.1, importance_entropy / 10)
            
        return min(0.95, confidence)  # Plafonner à 0.95 pour éviter l'excès de confiance
        
    def _determine_supporting_factors(self, model, features_df: pd.DataFrame) -> Dict[str, float]:
        """
        Détermine les facteurs qui soutiennent la prédiction.
        
        Args:
            model: Modèle de prédiction
            features_df: DataFrame des caractéristiques
            
        Returns:
            Dictionnaire des facteurs de support et leur importance
        """
        # Si le modèle a des importances de caractéristiques, les utiliser
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_names = features_df.columns
            
            # Créer un dictionnaire des caractéristiques importantes
            feature_importances = dict(zip(feature_names, importances))
            
            # Ne garder que les caractéristiques les plus importantes
            top_features = dict(sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)[:5])
            
            # Normaliser pour que la somme soit 1
            total = sum(top_features.values())
            if total > 0:
                top_features = {k: v / total for k, v in top_features.items()}
                
            return top_features
        else:
            # Si le modèle n'a pas d'importances de caractéristiques, renvoyer un dict vide
            return {}

class SentimentAnalyzer:
    """Analyseur de sentiment pour les tokens crypto."""
    
    def __init__(self):
        """Initialise l'analyseur de sentiment."""
        self.sources = ["twitter", "discord", "reddit"]
        self.sentiment_cache = {}
        
    async def get_sentiment(self, token_address: str) -> Dict[str, Any]:
        """
        Analyse le sentiment pour un token spécifique.
        
        Args:
            token_address: Adresse du token
            
        Returns:
            Dictionnaire avec le score de sentiment et les métadonnées
        """
        # Vérifier si nous avons des données en cache récentes
        cache_key = f"{token_address}_sentiment"
        if cache_key in self.sentiment_cache:
            cache_time, cache_data = self.sentiment_cache[cache_key]
            # Utiliser le cache si moins de 30 minutes
            if time.time() - cache_time < 1800:
                return cache_data
        
        # Initialiser le résultat
        result = {
            "overall_score": 0,
            "sources": {},
            "timestamp": time.time(),
            "volume": 0
        }
        
        try:
            # Obtenir le sentiment de chaque source
            sentiment_tasks = [
                self._get_twitter_sentiment(token_address),
                self._get_discord_sentiment(token_address),
                self._get_reddit_sentiment(token_address)
            ]
            
            source_sentiments = await asyncio.gather(*sentiment_tasks, return_exceptions=True)
            
            valid_sentiments = []
            total_volume = 0
            
            # Agréger les sentiments de différentes sources
            for i, sentiment in enumerate(source_sentiments):
                if isinstance(sentiment, Exception):
                    logger.warning(f"Erreur lors de l'analyse du sentiment depuis {self.sources[i]}: {sentiment}")
                    continue
                    
                if sentiment["volume"] > 0:
                    source_name = self.sources[i]
                    result["sources"][source_name] = sentiment
                    valid_sentiments.append(sentiment["score"] * sentiment["volume"])
                    total_volume += sentiment["volume"]
            
            # Calculer le score global pondéré par le volume
            if total_volume > 0:
                result["overall_score"] = sum(valid_sentiments) / total_volume
                result["volume"] = total_volume
                
            # Mettre en cache le résultat
            self.sentiment_cache[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du sentiment pour {token_address}: {e}")
            return {
                "overall_score": 0,
                "error": str(e),
                "timestamp": time.time(),
                "volume": 0
            }
            
    async def _get_twitter_sentiment(self, token_address: str) -> Dict[str, Any]:
        """Analyse le sentiment sur Twitter."""
        # Ici, on simulerait un appel à l'API Twitter pour obtenir les tweets récents
        # et les analyser avec NLP
        
        # Simuler un sentiment aléatoire pour cette démo
        await asyncio.sleep(0.5)  # Simuler un délai réseau
        return {
            "score": np.random.uniform(-1, 1),
            "volume": np.random.randint(10, 1000),
            "positive_ratio": np.random.uniform(0.2, 0.8),
            "negative_ratio": np.random.uniform(0.2, 0.8),
            "neutral_ratio": np.random.uniform(0.1, 0.3)
        }
        
    async def _get_discord_sentiment(self, token_address: str) -> Dict[str, Any]:
        """Analyse le sentiment sur Discord."""
        # Simuler un sentiment
        await asyncio.sleep(0.3)
        return {
            "score": np.random.uniform(-1, 1),
            "volume": np.random.randint(5, 500),
            "positive_ratio": np.random.uniform(0.2, 0.8),
            "negative_ratio": np.random.uniform(0.2, 0.8),
            "neutral_ratio": np.random.uniform(0.1, 0.3)
        }
        
    async def _get_reddit_sentiment(self, token_address: str) -> Dict[str, Any]:
        """Analyse le sentiment sur Reddit."""
        # Simuler un sentiment
        await asyncio.sleep(0.4)
        return {
            "score": np.random.uniform(-1, 1),
            "volume": np.random.randint(5, 800),
            "positive_ratio": np.random.uniform(0.2, 0.8),
            "negative_ratio": np.random.uniform(0.2, 0.8),
            "neutral_ratio": np.random.uniform(0.1, 0.3)
        }

class ReinforcementLearner:
    """
    Système d'apprentissage par renforcement pour optimiser les paramètres de trading.
    """
    
    def __init__(self, model_dir: str = "rl_models"):
        """
        Initialise l'agent d'apprentissage par renforcement.
        
        Args:
            model_dir: Répertoire de stockage des modèles RL
        """
        self.model_dir = model_dir
        self.models = {}
        self.learning_rate = 0.001
        self.discount_factor = 0.95
        self.exploration_rate = 0.1
        
        os.makedirs(model_dir, exist_ok=True)
        
    async def optimize_parameters(self, token_address: str, current_params: Dict[str, Any],
                               performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimise les paramètres de trading en utilisant l'apprentissage par renforcement.
        
        Args:
            token_address: Adresse du token
            current_params: Paramètres actuels
            performance_history: Historique des performances
            
        Returns:
            Paramètres optimisés
        """
        try:
            # Charger ou créer un modèle pour ce token
            model_key = token_address
            if model_key not in self.models:
                await self._initialize_model(model_key, current_params)
                
            # Si l'historique des performances est insuffisant, renvoyer les paramètres actuels
            if len(performance_history) < 5:
                return current_params
                
            # Convertir l'historique des performances en état et récompense
            state = self._extract_state(performance_history)
            reward = self._calculate_reward(performance_history)
            
            # Mettre à jour le modèle avec cette expérience
            self._update_model(model_key, state, reward)
            
            # Obtenir de nouveaux paramètres en fonction de l'état actuel
            new_params = self._get_action(model_key, state)
            
            # Limiter les modifications pour éviter des changements trop brusques
            optimized_params = self._constrain_parameters(current_params, new_params)
            
            logger.info(f"Paramètres optimisés pour {token_address}: {optimized_params}")
            return optimized_params
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation des paramètres: {e}")
            return current_params
            
    async def _initialize_model(self, model_key: str, initial_params: Dict[str, Any]) -> None:
        """Initialise un nouveau modèle RL."""
        # Dans une implémentation réelle, nous utiliserions une bibliothèque comme PyTorch,
        # Stable Baselines, ou une autre bibliothèque RL
        
        # Pour cet exemple, nous créons un modèle très simplifié
        model_path = os.path.join(self.model_dir, f"{model_key}.joblib")
        
        if os.path.exists(model_path):
            try:
                self.models[model_key] = joblib.load(model_path)
                logger.info(f"Modèle RL chargé pour {model_key}")
            except Exception as e:
                logger.warning(f"Échec du chargement du modèle RL: {e}. Création d'un nouveau modèle.")
                self._create_new_model(model_key, initial_params)
        else:
            self._create_new_model(model_key, initial_params)
            
    def _create_new_model(self, model_key: str, initial_params: Dict[str, Any]) -> None:
        """Crée un nouveau modèle RL."""
        # Modèle simplifié pour cet exemple
        self.models[model_key] = {
            "q_table": {},  # Table Q pour l'apprentissage par renforcement
            "params_history": [initial_params],
            "reward_history": [],
            "last_state": None,
            "last_action": None
        }
        logger.info(f"Nouveau modèle RL créé pour {model_key}")
        
    def _extract_state(self, performance_history: List[Dict[str, Any]]) -> Tuple:
        """
        Extrait un état à partir de l'historique des performances.
        
        Args:
            performance_history: Historique des performances
            
        Returns:
            Tuple représentant l'état
        """
        # Extraire les métriques pertinentes des 5 dernières périodes
        recent_history = performance_history[-5:]
        
        # Calculer des indicateurs sur les performances récentes
        returns = [p.get('return', 0) for p in recent_history]
        avg_return = sum(returns) / len(returns) if returns else 0
        
        win_rate = sum(1 for p in recent_history if p.get('return', 0) > 0) / len(recent_history)
        
        volatility = np.std(returns) if len(returns) > 1 else 0
        
        # Discrétiser les valeurs pour créer un état fini
        return (
            self._discretize(avg_return, bins=[-0.1, -0.03, 0, 0.03, 0.1]),
            self._discretize(win_rate, bins=[0.2, 0.4, 0.6, 0.8]),
            self._discretize(volatility, bins=[0.01, 0.03, 0.05, 0.1])
        )
        
    def _discretize(self, value: float, bins: List[float]) -> int:
        """Discrétise une valeur continue en fonction des seuils."""
        for i, threshold in enumerate(bins):
            if value < threshold:
                return i
        return len(bins)
        
    def _calculate_reward(self, performance_history: List[Dict[str, Any]]) -> float:
        """
        Calcule la récompense à partir de l'historique des performances.
        
        Args:
            performance_history: Historique des performances
            
        Returns:
            Valeur de récompense
        """
        # Utiliser principalement les performances récentes
        if not performance_history:
            return 0
            
        # Mettre l'accent sur les performances les plus récentes
        recent_returns = [p.get('return', 0) for p in performance_history[-3:]]
        if not recent_returns:
            return 0
            
        # Combiner rendement et stabilité
        avg_return = sum(recent_returns) / len(recent_returns)
        stability = 1 / (1 + np.std(recent_returns)) if len(recent_returns) > 1 else 1
        
        # Pénaliser les pertes importantes
        drawdown_penalty = abs(min(0, min(recent_returns))) * 2 if recent_returns else 0
        
        reward = avg_return * 100 + stability * 0.5 - drawdown_penalty
        return reward
        
    def _update_model(self, model_key: str, state: Tuple, reward: float) -> None:
        """
        Met à jour le modèle RL avec une nouvelle expérience.
        
        Args:
            model_key: Clé du modèle
            state: État actuel
            reward: Récompense reçue
        """
        model = self.models[model_key]
        
        # Si c'est la première expérience, enregistrer simplement l'état
        if model["last_state"] is None or model["last_action"] is None:
            model["last_state"] = state
            return
            
        # Mise à jour de la table Q (Q-learning)
        last_state = model["last_state"]
        last_action = model["last_action"]
        
        # Créer une clé pour la table Q
        state_key = str(last_state)
        if state_key not in model["q_table"]:
            model["q_table"][state_key] = {}
        if last_action not in model["q_table"][state_key]:
            model["q_table"][state_key][last_action] = 0
            
        # Estimer la valeur optimale pour le nouvel état
        new_state_key = str(state)
        if new_state_key not in model["q_table"]:
            model["q_table"][new_state_key] = {}
            max_q = 0
        else:
            max_q = max(model["q_table"][new_state_key].values()) if model["q_table"][new_state_key] else 0
            
        # Mise à jour de la valeur Q
        current_q = model["q_table"][state_key][last_action]
        model["q_table"][state_key][last_action] = current_q + self.learning_rate * (
            reward + self.discount_factor * max_q - current_q
        )
        
        # Mettre à jour l'état actuel
        model["last_state"] = state
        
        # Enregistrer la récompense
        model["reward_history"].append(reward)
        
        # Sauvegarder le modèle périodiquement
        if len(model["reward_history"]) % 10 == 0:
            self._save_model(model_key)
            
    def _get_action(self, model_key: str, state: Tuple) -> Dict[str, Any]:
        """
        Détermine l'action (paramètres de trading) à prendre dans l'état actuel.
        
        Args:
            model_key: Clé du modèle
            state: État actuel
            
        Returns:
            Nouveaux paramètres de trading
        """
        model = self.models[model_key]
        state_key = str(state)
        
        # Exploration vs exploitation
        if np.random.random() < self.exploration_rate or state_key not in model["q_table"]:
            # Exploration: générer des paramètres aléatoires autour des derniers paramètres
            last_params = model["params_history"][-1]
            new_params = self._generate_random_params(last_params)
            action_key = str(new_params)
        else:
            # Exploitation: choisir les paramètres avec la valeur Q la plus élevée
            q_values = model["q_table"][state_key]
            if not q_values:
                # Si aucune valeur Q n'est disponible, exploration
                last_params = model["params_history"][-1]
                new_params = self._generate_random_params(last_params)
                action_key = str(new_params)
            else:
                action_key = max(q_values.items(), key=lambda x: x[1])[0]
                new_params = eval(action_key)  # Convertir la chaîne en dictionnaire
                
        # Enregistrer l'action choisie
        model["last_action"] = action_key
        model["params_history"].append(new_params)
        
        return new_params
        
    def _generate_random_params(self, base_params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des paramètres aléatoires autour des paramètres de base."""
        new_params = base_params.copy()
        for key in new_params:
            if isinstance(new_params[key], (int, float)):
                new_params[key] *= np.random.uniform(0.9, 1.1)  # Variation de ±10%
        return new_params
        
    def _constrain_parameters(self, current_params: Dict[str, Any], new_params: Dict[str, Any]) -> Dict[str, Any]:
        """Contraint les nouveaux paramètres pour éviter des changements trop brusques."""
        constrained_params = current_params.copy()
        for key in new_params:
            if key in constrained_params:
                constrained_params[key] = (constrained_params[key] + new_params[key]) / 2  # Moyenne des deux
        return constrained_params
        
    def _save_model(self, model_key: str) -> None:
        """Sauvegarde le modèle RL."""
        model_path = os.path.join(self.model_dir, f"{model_key}.joblib")
        joblib.dump(self.models[model_key], model_path)
        logger.info(f"Modèle RL sauvegardé pour {model_key}")