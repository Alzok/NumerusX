import pandas as pd
import talib
import numpy as np
from typing import Dict
import logging
from config import Config

class AdvancedTradingStrategy:
    def __init__(self):
        self.logger = logging.getLogger('Analytics')
        
    def analyze(self, data: Dict) -> Dict:
        """Analyse multi-source (Jupiter + DexScreener)"""
        try:
            df = self._prepare_dataframe(data)
            if df.empty or len(df) < 24:
                return {'error': 'Données insuffisantes'}
                
            return {
                'momentum': self._momentum_score(df),
                'volume_quality': self._volume_analysis(data),
                'market_structure': self._market_structure(df),
                'risk': self._risk_score(df)
            }
        except Exception as e:
            self.logger.error(f"Erreur analyse: {str(e)}")
            return {'error': str(e)}

    def _prepare_dataframe(self, data: Dict) -> pd.DataFrame:
        """Convertit les formats API en DataFrame de manière robuste."""
        # Jupiter API format
        if isinstance(data, dict) and 'priceHistory' in data:
            return pd.DataFrame(data['priceHistory'])
        # DexScreener API format
        elif isinstance(data, dict) and 'pairs' in data and len(data.get('pairs', [])) > 0:
            pairs_data = data.get('pairs', [{}])[0]
            if 'priceHistory' in pairs_data:
                return pd.DataFrame(pairs_data['priceHistory'])
        # Generic format handling
        elif isinstance(data, list):
            return pd.DataFrame(data)
        # Fallback empty DataFrame with expected columns
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    def _momentum_score(self, df: pd.DataFrame) -> float:
        close = df['close'].astype(float)
        rsi = talib.RSI(close, 14).iloc[-1]
        macd = talib.MACD(close)[0].iloc[-1]
        stoch = talib.STOCH(df['high'], df['low'], close)[0].iloc[-1]
        return np.mean([rsi * 0.4, macd * 0.3, stoch * 0.3])

    def _volume_analysis(self, data: Dict) -> int:
        """Combine Jupiter volume24h et DexScreener volume.h24"""
        jup_volume = data.get('volume24h', 0)
        dex_volume = data.get('volume', {}).get('h24', 0)
        total = jup_volume + dex_volume
        return 1 if total > Config.MIN_LIQUIDITY else 0

    def _market_structure(self, df: pd.DataFrame) -> float:
        resistance = df['high'].rolling(24).max().iloc[-1]
        support = df['low'].rolling(24).min().iloc[-1]
        current = df['close'].iloc[-1]
        return (current - support) / (resistance - support) if resistance != support else 0.5

    def _risk_score(self, df: pd.DataFrame) -> float:
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)
        atr = talib.ATR(high, low, close, 14).iloc[-1]
        return ((high.iloc[-1] - low.iloc[-1]) / atr) if atr > 0 else 0

    def generate_signal(self, analysis: Dict) -> str:
        if 'error' in analysis:
            return 'hold'
            
        if (analysis['momentum'] > 0.7 
            and analysis['volume_quality'] == 1 
            and analysis['market_structure'] > 0.6):
            return 'strong_buy'
        elif analysis['risk'] > 1.5 or analysis['volume_quality'] == 0:
            return 'sell'
        return 'hold'