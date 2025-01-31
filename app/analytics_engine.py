import pandas as pd
import talib
import numpy as np

class TradingStrategy:
    def analyze(self, df: pd.DataFrame) -> dict:
        analysis = {
            'rsi': self._calc_rsi(df),
            'macd': self._calc_macd(df),
            'ichimoku': self._calc_ichimoku(df),
            'volume_spike': self._detect_volume_spike(df)
        }
        return analysis

    def _calc_rsi(self, df):
        return talib.RSI(df['close'], timeperiod=14)

    def _calc_macd(self, df):
        macd, signal, _ = talib.MACD(df['close'])
        return macd - signal

    def _calc_ichimoku(self, df):
        return {
            'tenkan': talib.EMA(df['high'], 9) + talib.EMA(df['low'], 9) / 2,
            'kijun': talib.EMA(df['high'], 26) + talib.EMA(df['low'], 26) / 2
        }

    def _detect_volume_spike(self, df):
        return df['volume'] > (df['volume'].rolling(24).mean() * 3)