import pandas as pd
import talib
import numpy as np
from typing import Dict, List, Optional, Union
import logging
from app.config import Config

class AdvancedTradingStrategy:
    def __init__(self):
        self.logger = logging.getLogger('Analytics')
        
    def analyze(self, historical_data_list: List[Dict], current_pair_metrics: Optional[Dict] = None) -> Dict:
        """Analyse multi-source, now taking historical list and optional current pair metrics."""
        try:
            # _prepare_dataframe expects a list of dicts for historical data
            df = self._prepare_dataframe(historical_data_list)
            if df.empty or len(df) < 24: # Or some other meaningful threshold
                return {'error': 'Données historiques insuffisantes pour l\'analyse'}
            
            # Use current_pair_metrics for volume analysis if available
            volume_quality = self._volume_analysis(current_pair_metrics if current_pair_metrics else {})

            return {
                'momentum': self._momentum_score(df),
                'volume_quality': volume_quality,
                'market_structure': self._market_structure(df),
                'risk': self._risk_score(df)
            }
        except Exception as e:
            self.logger.error(f"Erreur analyse: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def _prepare_dataframe(self, data: Union[List[Dict], Dict]) -> pd.DataFrame:
        """Convertit les formats API en DataFrame de manière robuste.
        Now primarily expects a list of historical data dicts.
        """
        if isinstance(data, list):
            # This is the expected format from MarketDataProvider.get_historical_prices
            df = pd.DataFrame(data)
            # Ensure required columns exist
            expected_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in expected_cols:
                if col not in df.columns:
                    # Add missing column with NaNs or default values if appropriate
                    df[col] = np.nan 
            return df
        elif isinstance(data, dict) and 'priceHistory' in data: # Legacy handling
            return pd.DataFrame(data['priceHistory'])
        elif isinstance(data, dict) and 'pairs' in data and len(data.get('pairs', [])) > 0: # Legacy handling
            pairs_data = data.get('pairs', [{}])[0]
            if 'priceHistory' in pairs_data:
                return pd.DataFrame(pairs_data['priceHistory'])
        
        self.logger.warning(f"Format de données inattendu pour _prepare_dataframe: {type(data)}")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    def _momentum_score(self, df: pd.DataFrame) -> float:
        try:
            close = df['close'].astype(float)
            rsi = talib.RSI(close, 14).iloc[-1]
            macd = talib.MACD(close)[0].iloc[-1]
            stoch = talib.STOCH(df['high'], df['low'], close)[0].iloc[-1]
            return np.mean([rsi * 0.4, macd * 0.3, stoch * 0.3])
        except Exception as e:
            self.logger.error(f"Erreur calcul momentum: {str(e)}")
            return 0.0

    def _volume_analysis(self, pair_data: Dict) -> int:
        """Analyse le volume à partir des données actuelles de la paire (standardisées).
        Utilise 'liquidity_usd' et 'volume_h24' du format standardisé.
        """
        try:
            # Data from MarketDataProvider.get_token_pairs (standardized format)
            # It should have 'liquidity_usd' and 'volume_h24'
            liquidity = pair_data.get('liquidity_usd', 0.0) 
            volume_24h = pair_data.get('volume_h24', 0.0)

            # The original logic used Config.MIN_LIQUIDITY_USD for volume check threshold.
            # This seems like a confusion between liquidity and volume.
            # Let's assume the check is against MIN_LIQUIDITY_USD for liquidity.
            # And perhaps a separate check for volume if needed.
            # For now, replicating the spirit: if liquidity > threshold, quality = 1
            
            # Using MIN_LIQUIDITY_USD as a threshold for *liquidity* quality
            return 1 if liquidity > Config.MIN_LIQUIDITY_USD else 0
        except Exception as e:
            self.logger.error(f"Erreur analyse volume: {str(e)}")
            return 0

    def _market_structure(self, df: pd.DataFrame) -> float:
        try:
            resistance = df['high'].rolling(24).max().iloc[-1]
            support = df['low'].rolling(24).min().iloc[-1]
            current = df['close'].iloc[-1]
            return (current - support) / (resistance - support) if resistance != support else 0.5
        except Exception as e:
            self.logger.error(f"Erreur analyse structure de marché: {str(e)}")
            return 0.5

    def _risk_score(self, df: pd.DataFrame) -> float:
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            atr = talib.ATR(high, low, close, 14).iloc[-1]
            return ((high.iloc[-1] - low.iloc[-1]) / atr) if atr > 0 else 0
        except Exception as e:
            self.logger.error(f"Erreur calcul score de risque: {str(e)}")
            return 0

    def generate_signal(self, analysis: Dict) -> str:
        if 'error' in analysis:
            return 'hold'
            
        try:
            if (analysis['momentum'] > Config.TRADE_CONFIDENCE_THRESHOLD
                and analysis['volume_quality'] == 1 
                and analysis['market_structure'] > 0.6):
                return 'strong_buy'
            elif analysis['risk'] > 1.5 or analysis['volume_quality'] == 0:
                return 'sell'
            return 'hold'
        except Exception as e:
            self.logger.error(f"Erreur génération signal: {str(e)}")
            return 'hold'