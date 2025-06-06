import pandas as pd
try:
    import talib
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
    import pandas as pd
import numpy as np
import logging
from app.config_v2 import get_config
from app.strategy_framework import BaseStrategy

class AdvancedTradingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('Analytics')
        self.parameters = {
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stoch_k': 14,
            'stoch_d': 3,
            'stoch_smooth_k': 3,
            'atr_period': 14,
            'rolling_structure_period': 24
        }

    def get_parameters(self) -> dict:
        return self.parameters

    def analyze(self, market_data_df: pd.DataFrame, **kwargs) -> Dict:
        """Analyse market data DataFrame and optional current pair metrics."""
        current_pair_metrics = kwargs.get('current_pair_metrics')
        try:
            df = market_data_df
            if df.empty or len(df) < max(self.parameters['rsi_period'], self.parameters['macd_slow'], self.parameters['atr_period'], self.parameters['rolling_structure_period']): 
                self.logger.warning("Données historiques insuffisantes pour l'analyse complète.")
                return {'error': 'Données historiques insuffisantes pour l\'analyse'}
            
            volume_quality = self._volume_analysis(current_pair_metrics if current_pair_metrics else {})
            momentum, rsi, macd, stoch_k = self._momentum_score(df)

            return {
                'momentum_score': momentum,
                'rsi': rsi,
                'macd': macd,
                'stoch_k': stoch_k,
                'volume_quality': volume_quality,
                'market_structure_ratio': self._market_structure(df),
                'risk_score': self._risk_score(df),
                'last_price': df['close'].iloc[-1] if not df['close'].empty else None
            }
        except Exception as e:
            self.logger.error(f"Erreur analyse: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def _prepare_dataframe(self, data: Union[List[Dict], Dict]) -> pd.DataFrame:
        if isinstance(data, list):
            df = pd.DataFrame(data)
            expected_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = np.nan 
            return df
        elif isinstance(data, dict) and 'priceHistory' in data: 
            return pd.DataFrame(data['priceHistory'])
        elif isinstance(data, dict) and 'pairs' in data and len(data.get('pairs', [])) > 0: 
            pairs_data = data.get('pairs', [{}])[0]
            if 'priceHistory' in pairs_data:
                return pd.DataFrame(pairs_data['priceHistory'])
        
        self.logger.warning(f"Format de données inattendu pour _prepare_dataframe: {type(data)}")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    def _momentum_score(self, df: pd.DataFrame) -> tuple[float, Optional[float], Optional[float], Optional[float]]:
        try:
            close = df['close'].astype(float)
            high = df['high'].astype(float)
            low = df['low'].astype(float)

            rsi = talib.RSI(close, timeperiod=self.parameters['rsi_period']).iloc[-1]
            macd_line, macd_signal, _ = talib.MACD(close, 
                                                fastperiod=self.parameters['macd_fast'], 
                                                slowperiod=self.parameters['macd_slow'], 
                                                signalperiod=self.parameters['macd_signal'])
            stoch_k, _ = talib.STOCH(high, low, close, 
                                     fastk_period=self.parameters['stoch_k'],
                                     slowk_period=self.parameters['stoch_d'],
                                     slowd_period=self.parameters['stoch_d'])
            
            valid_indicators = []
            if pd.notna(rsi): valid_indicators.append(rsi / 100)
            if pd.notna(macd_line.iloc[-1]) and pd.notna(macd_signal.iloc[-1]):
                valid_indicators.append(0.5 + (macd_line.iloc[-1] - macd_signal.iloc[-1]) * 0.1)
            if pd.notna(stoch_k.iloc[-1]): valid_indicators.append(stoch_k.iloc[-1] / 100)

            score = np.mean(valid_indicators) if valid_indicators else 0.5
            return score, rsi, macd_line.iloc[-1], stoch_k.iloc[-1]
        except Exception as e:
            self.logger.error(f"Erreur calcul momentum: {str(e)}", exc_info=True)
            return 0.5, None, None, None

    def _volume_analysis(self, pair_data: Dict) -> int:
        try:
            liquidity = pair_data.get('liquidity_usd', 0.0) 
            return 1 if liquidity > get_config().MIN_LIQUIDITY_USD else 0
        except Exception as e:
            self.logger.error(f"Erreur analyse volume: {str(e)}")
            return 0

    def _market_structure(self, df: pd.DataFrame) -> float:
        try:
            period = self.parameters['rolling_structure_period']
            resistance = df['high'].rolling(period).max().iloc[-1]
            support = df['low'].rolling(period).min().iloc[-1]
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
            atr = talib.ATR(high, low, close, timeperiod=self.parameters['atr_period']).iloc[-1]
            return ((high.iloc[-1] - low.iloc[-1]) / atr) if atr is not None and atr > 0 else 0.0
        except Exception as e:
            self.logger.error(f"Erreur calcul score de risque: {str(e)}")
            return 0.0

    def generate_signal(self, analysis: Dict, **kwargs) -> Dict:
        if 'error' in analysis or not analysis.get('last_price'):
            return {'signal': 'hold', 'confidence': 0.0, 'reason': analysis.get('error', 'Missing analysis data')}
            
        try:
            momentum_score = analysis.get('momentum_score', 0.5)
            volume_quality = analysis.get('volume_quality', 0)
            market_structure_ratio = analysis.get('market_structure_ratio', 0.5)
            last_price = analysis['last_price']

            signal = 'hold'
            confidence = 0.5

            if volume_quality == 0:
                return {'signal': 'hold', 'confidence': 0.1, 'reason': 'Low volume quality'}

            if momentum_score > get_config().TRADE_CONFIDENCE_THRESHOLD and market_structure_ratio > 0.6:
                signal = 'buy'
                confidence = min(0.95, momentum_score * 0.8 + market_structure_ratio * 0.2)
            elif momentum_score < (1 - get_config().TRADE_CONFIDENCE_THRESHOLD) and market_structure_ratio < 0.4:
                signal = 'sell'
                confidence = min(0.95, (1-momentum_score) * 0.8 + (1-market_structure_ratio) * 0.2)

            return {
                'signal': signal,
                'confidence': float(confidence),
                'target_price': last_price * 1.05 if signal == 'buy' else (last_price * 0.95 if signal == 'sell' else None), 
                'stop_loss': last_price * 0.98 if signal == 'buy' else (last_price * 1.02 if signal == 'sell' else None) 
            }
        except Exception as e:
            self.logger.error(f"Erreur génération signal: {str(e)}", exc_info=True)
            return {'signal': 'hold', 'confidence': 0.0, 'reason': f'Error in signal generation: {e}'}