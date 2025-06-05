import pandas as pd
try:
    import talib # For ADX and MAs, if preferred over pandas_ta or manual
    HAS_TALIB = True
except ImportError:
    HAS_TALIB = False
# import pandas_ta as ta # Uncomment if using pandas_ta
from app.strategy_framework import BaseStrategy
from typing import Dict

class TrendFollowingStrategy(BaseStrategy):
    """Strategy based on trend identification using Moving Averages and ADX."""

    def __init__(self, short_ma_period: int = 10, long_ma_period: int = 50, adx_period: int = 14, adx_threshold: float = 25):
        super().__init__()
        self.short_ma_period = short_ma_period
        self.long_ma_period = long_ma_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold # Minimum ADX value to consider a trend strong enough
        self.parameters = {
            'short_ma_period': self.short_ma_period,
            'long_ma_period': self.long_ma_period,
            'adx_period': self.adx_period,
            'adx_threshold': self.adx_threshold
        }

    def analyze(self, market_data: pd.DataFrame, **kwargs) -> Dict:
        """Implements trend analysis using SMAs/EMAs and ADX.
        Assumes market_data has 'high', 'low', 'close' columns.
        """
        analysis_results = {'indicators': {}}
        required_cols = ['high', 'low', 'close']
        for col in required_cols:
            if col not in market_data.columns or market_data[col].empty:
                return {'error': f'{col} price not found or empty in market_data'}
        
        min_data_length = max(self.long_ma_period, self.adx_period)
        if len(market_data) < min_data_length:
            return {'error': f'Not enough data (need {min_data_length}, got {len(market_data)})'}

        close_prices = market_data['close'].astype(float)
        high_prices = market_data['high'].astype(float)
        low_prices = market_data['low'].astype(float)

        # Moving Averages (using SMA for simplicity, could use EMA via talib.EMA or pandas_ta.ema)
        # Using pandas_ta:
        # market_data.ta.sma(length=self.short_ma_period, append=True) # -> SMA_10
        # market_data.ta.sma(length=self.long_ma_period, append=True)  # -> SMA_50
        # analysis_results['indicators']['short_ma'] = market_data[f'SMA_{self.short_ma_period}'].iloc[-1]
        # analysis_results['indicators']['long_ma'] = market_data[f'SMA_{self.long_ma_period}'].iloc[-1]
        analysis_results['indicators']['short_ma'] = close_prices.rolling(window=self.short_ma_period).mean().iloc[-1]
        analysis_results['indicators']['long_ma'] = close_prices.rolling(window=self.long_ma_period).mean().iloc[-1]

        # ADX (Average Directional Index)
        # Using pandas_ta:
        # market_data.ta.adx(length=self.adx_period, append=True) # -> ADX_14, DMP_14, DMN_14
        # analysis_results['indicators']['adx'] = market_data[f'ADX_{self.adx_period}'].iloc[-1]
        # analysis_results['indicators']['plus_di'] = market_data[f'DMP_{self.adx_period}'].iloc[-1]
        # analysis_results['indicators']['minus_di'] = market_data[f'DMN_{self.adx_period}'].iloc[-1]
        try:
            adx_values = talib.ADX(high_prices, low_prices, close_prices, timeperiod=self.adx_period)
            plus_di_values = talib.PLUS_DI(high_prices, low_prices, close_prices, timeperiod=self.adx_period)
            minus_di_values = talib.MINUS_DI(high_prices, low_prices, close_prices, timeperiod=self.adx_period)
            analysis_results['indicators']['adx'] = adx_values.iloc[-1] if not pd.isna(adx_values.iloc[-1]) else None
            analysis_results['indicators']['plus_di'] = plus_di_values.iloc[-1] if not pd.isna(plus_di_values.iloc[-1]) else None
            analysis_results['indicators']['minus_di'] = minus_di_values.iloc[-1] if not pd.isna(minus_di_values.iloc[-1]) else None
        except Exception as e:
            # self.logger.error(f"Error calculating ADX with talib: {e}") # If logger available
            analysis_results['indicators']['adx'] = None
            analysis_results['indicators']['plus_di'] = None
            analysis_results['indicators']['minus_di'] = None

        analysis_results['last_price'] = close_prices.iloc[-1]
        return analysis_results

    def generate_signal(self, analysis: Dict, **kwargs) -> Dict:
        """Generates trading signal from MA crossover and ADX trend strength."""
        short_ma = analysis.get('indicators', {}).get('short_ma')
        long_ma = analysis.get('indicators', {}).get('long_ma')
        adx = analysis.get('indicators', {}).get('adx')
        plus_di = analysis.get('indicators', {}).get('plus_di')
        minus_di = analysis.get('indicators', {}).get('minus_di')
        last_price = analysis.get('last_price')

        signal = 'hold'
        confidence = 0.5

        if None in [short_ma, long_ma, adx, plus_di, minus_di, last_price]:
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'Missing indicator or price data'}

        is_trending = adx > self.adx_threshold

        # Buy Signal: Short MA crosses above Long MA, and ADX indicates a trend, and +DI > -DI
        if short_ma > long_ma and is_trending and plus_di > minus_di:
            signal = 'buy'
            # Confidence based on ADX strength and MA separation
            confidence = 0.60 + (adx / 200) + ((short_ma - long_ma) / long_ma) * 0.5 # Example scaling
            confidence = min(0.95, confidence) 

        # Sell Signal: Short MA crosses below Long MA, and ADX indicates a trend, and -DI > +DI
        elif short_ma < long_ma and is_trending and minus_di > plus_di:
            signal = 'sell'
            confidence = 0.60 + (adx / 200) + ((long_ma - short_ma) / short_ma) * 0.5 # Example scaling
            confidence = min(0.95, confidence)
        
        # Could add exit signals if trend weakens (ADX falls below threshold) or MAs cross back

        return {
            'signal': signal,
            'confidence': confidence,
            'target_price': last_price * 1.10 if signal == 'buy' else (last_price * 0.90 if signal == 'sell' else None), # Example aggressive target
            'stop_loss': (long_ma * 0.99) if signal == 'buy' else (long_ma * 1.01 if signal == 'sell' else None) # Stop below/above long MA
        }

    def get_parameters(self) -> dict:
        return self.parameters 
