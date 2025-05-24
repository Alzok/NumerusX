import pandas as pd
from app.strategy_framework import BaseStrategy
# import pandas_ta as ta # Uncomment if you want to use pandas_ta for indicators

class MomentumStrategy(BaseStrategy):
    """Strategy based on price momentum indicators like RSI and MACD."""
    
    def __init__(self, rsi_period: int = 14, rsi_oversold: float = 30, rsi_overbought: float = 70, 
                 macd_fast: int = 12, macd_slow: int = 26, macd_signal: int = 9):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.parameters = {
            'rsi_period': self.rsi_period,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'macd_fast': self.macd_fast,
            'macd_slow': self.macd_slow,
            'macd_signal': self.macd_signal
        }

    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, series: pd.Series, fast: int, slow: int, signal: int) -> pd.DataFrame:
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return pd.DataFrame({'MACD': macd, 'Signal': signal_line, 'Histogram': histogram})

    def analyze(self, market_data: pd.DataFrame, **kwargs) -> dict:
        """Implements momentum analysis using RSI and MACD.
        Assumes market_data has a 'close' column for price.
        """
        analysis_results = {'indicators': {}}
        if 'close' not in market_data.columns:
            # Or raise an error, or return empty analysis
            return {'error': 'Close price not found in market_data'}

        # Calculate RSI
        # if 'rsi' in market_data.columns: # Check if already provided
        #     analysis_results['indicators']['rsi'] = market_data['rsi'].iloc[-1]
        # else:
        # Using pandas_ta if available:
        # market_data.ta.rsi(length=self.rsi_period, append=True) 
        # analysis_results['indicators']['rsi'] = market_data[f'RSI_{self.rsi_period}'].iloc[-1] if f'RSI_{self.rsi_period}' in market_data else None
        rsi_series = self._calculate_rsi(market_data['close'], self.rsi_period)
        analysis_results['indicators']['rsi'] = rsi_series.iloc[-1] if not rsi_series.empty else None

        # Calculate MACD
        # if 'macd_line' in market_data.columns and 'macd_signal' in market_data.columns and 'macd_hist' in market_data.columns:
        #     analysis_results['indicators']['macd'] = market_data['macd_line'].iloc[-1]
        #     analysis_results['indicators']['macd_signal'] = market_data['macd_signal'].iloc[-1]
        #     analysis_results['indicators']['macd_hist'] = market_data['macd_hist'].iloc[-1]
        # else:
        # Using pandas_ta if available:
        # market_data.ta.macd(fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal, append=True)
        # analysis_results['indicators']['macd'] = market_data[f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'].iloc[-1] if f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}' in market_data else None
        # analysis_results['indicators']['macd_signal'] = market_data[f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'].iloc[-1] if f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}' in market_data else None
        # analysis_results['indicators']['macd_hist'] = market_data[f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'].iloc[-1] if f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}' in market_data else None
        macd_df = self._calculate_macd(market_data['close'], self.macd_fast, self.macd_slow, self.macd_signal)
        if not macd_df.empty:
            analysis_results['indicators']['macd'] = macd_df['MACD'].iloc[-1]
            analysis_results['indicators']['macd_signal'] = macd_df['Signal'].iloc[-1]
            analysis_results['indicators']['macd_hist'] = macd_df['Histogram'].iloc[-1]
        else:
            analysis_results['indicators']['macd'] = None
            analysis_results['indicators']['macd_signal'] = None
            analysis_results['indicators']['macd_hist'] = None

        # Add other relevant data for signal generation if needed
        analysis_results['last_price'] = market_data['close'].iloc[-1] if not market_data['close'].empty else None
        
        return analysis_results

    def generate_signal(self, analysis: dict, **kwargs) -> dict:
        """Generates trading signal from RSI and MACD analysis."""
        rsi = analysis.get('indicators', {}).get('rsi')
        macd = analysis.get('indicators', {}).get('macd')
        macd_signal = analysis.get('indicators', {}).get('macd_signal')
        # macd_hist = analysis.get('indicators', {}).get('macd_hist') # Histogram can also be used
        last_price = analysis.get('last_price')

        signal = 'hold'
        confidence = 0.5 # Default confidence

        if rsi is None or macd is None or macd_signal is None or last_price is None:
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'Missing indicator data'}

        # Basic Buy Signal: RSI oversold and MACD bullish crossover
        if rsi < self.rsi_oversold and macd > macd_signal:
            signal = 'buy'
            # Confidence can be scaled by how oversold RSI is and strength of MACD crossover
            confidence = 0.70 + (self.rsi_oversold - rsi) / (self.rsi_oversold * 2) # Max ~0.85 if rsi is 0
            confidence = min(confidence, 0.95) # Cap confidence

        # Basic Sell Signal: RSI overbought and MACD bearish crossover
        elif rsi > self.rsi_overbought and macd < macd_signal:
            signal = 'sell'
            confidence = 0.70 + (rsi - self.rsi_overbought) / ((100 - self.rsi_overbought) * 2) # Max ~0.85 if rsi is 100
            confidence = min(confidence, 0.95) # Cap confidence
        
        # More nuanced logic can be added here, e.g., considering MACD histogram, divergences etc.

        return {
            'signal': signal,
            'confidence': confidence,
            'target_price': last_price * 1.05 if signal == 'buy' else (last_price * 0.95 if signal == 'sell' else None), # Example target
            'stop_loss': last_price * 0.98 if signal == 'buy' else (last_price * 1.02 if signal == 'sell' else None) # Example stop loss
        }

    def get_parameters(self) -> dict:
        return self.parameters 