import pandas as pd
import talib
import numpy as np
from typing import Dict
import logging
from config import Config

class AdvancedTradingStrategy:
    def __init__(self):
        self.logger = logging.getLogger('Analytics')
        
    def analyze(self, df: pd.DataFrame) -> Dict:
        """Analyse multi-critères avec gestion des erreurs"""
        try:
            if df.empty or len(df) < 24:
                return {'error': 'Données insuffisantes'}
                
            return {
                'momentum': self._momentum_score(df),
                'volume_quality': self._volume_analysis(df),
                'market_structure': self._market_structure(df),
                'risk': self._risk_score(df)
            }
        except KeyError as e:
            self.logger.error(f"Colonne manquante: {str(e)}")
            return {'error': str(e)}

    def _momentum_score(self, df: pd.DataFrame) -> float:
        close = df['close'].astype(float)
        rsi = talib.RSI(close, 14).iloc[-1]
        macd = talib.MACD(close)[0].iloc[-1]
        stoch = talib.STOCH(df['high'], df['low'], close)[0].iloc[-1]
        return np.mean([rsi * 0.4, macd * 0.3, stoch * 0.3])

    def _volume_analysis(self, df: pd.DataFrame) -> int:
        volume = df['volume'].astype(float)
        mean = volume.rolling(24).mean().iloc[-1]
        std = volume.rolling(24).std().iloc[-1]
        z_score = abs((volume.iloc[-1] - mean) / std) if std > 0 else 0
        return 0 if z_score > Config.VOLUME_ZSCORE_LIMIT else 1

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