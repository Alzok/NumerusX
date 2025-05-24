import pandas as pd
# import pandas_ta as ta # Uncomment if using pandas_ta for Bollinger Bands
from app.strategy_framework import BaseStrategy
from typing import Dict

class MeanReversionStrategy(BaseStrategy):
    """Strategy based on mean reversion using Bollinger Bands."""

    def __init__(self, bb_period: int = 20, bb_std_dev: float = 2.0):
        super().__init__()
        self.bb_period = bb_period
        self.bb_std_dev = bb_std_dev
        self.parameters = {
            'bb_period': self.bb_period,
            'bb_std_dev': self.bb_std_dev
        }

    def _calculate_bollinger_bands(self, series: pd.Series, period: int, std_dev: float) -> pd.DataFrame:
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return pd.DataFrame({
            'middle_band': sma,
            'upper_band': upper_band,
            'lower_band': lower_band
        })

    def analyze(self, market_data: pd.DataFrame, **kwargs) -> Dict:
        """Implements Bollinger Bands analysis.
        Assumes market_data has a 'close' column for price.
        """
        analysis_results = {'indicators': {}}
        if 'close' not in market_data.columns or market_data['close'].empty:
            return {'error': 'Close price not found or empty in market_data'}
        
        if len(market_data['close']) < self.bb_period:
            return {'error': f'Not enough data for Bollinger Bands (need {self.bb_period}, got {len(market_data['close'])})'}

        # Using pandas_ta if available:
        # try:
        #     bbands_df = market_data.ta.bbands(length=self.bb_period, std=self.bb_std_dev)
        #     # pandas_ta appends columns like BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        #     # Ensure to use the correct column names based on your pandas_ta version and settings
        #     lower_band_col = f'BBL_{self.bb_period}_{self.bb_std_dev:.1f}'
        #     middle_band_col = f'BBM_{self.bb_period}_{self.bb_std_dev:.1f}'
        #     upper_band_col = f'BBU_{self.bb_period}_{self.bb_std_dev:.1f}'
            
        #     if lower_band_col in bbands_df and upper_band_col in bbands_df and middle_band_col in bbands_df:
        #         analysis_results['indicators']['bb_lower'] = bbands_df[lower_band_col].iloc[-1]
        #         analysis_results['indicators']['bb_middle'] = bbands_df[middle_band_col].iloc[-1]
        #         analysis_results['indicators']['bb_upper'] = bbands_df[upper_band_col].iloc[-1]
        #     else:
        #         # Fallback or error if columns not found as expected
        #         bbands_manual_df = self._calculate_bollinger_bands(market_data['close'], self.bb_period, self.bb_std_dev)
        #         analysis_results['indicators']['bb_lower'] = bbands_manual_df['lower_band'].iloc[-1]
        #         analysis_results['indicators']['bb_middle'] = bbands_manual_df['middle_band'].iloc[-1]
        #         analysis_results['indicators']['bb_upper'] = bbands_manual_df['upper_band'].iloc[-1]
        # except Exception as e:
        #     # Fallback to manual calculation if pandas_ta fails
        #     # self.logger.warning(f"pandas_ta bbands failed: {e}, using manual calculation.") # If logger is available
        bbands_manual_df = self._calculate_bollinger_bands(market_data['close'], self.bb_period, self.bb_std_dev)
        if not bbands_manual_df.empty:
            analysis_results['indicators']['bb_lower'] = bbands_manual_df['lower_band'].iloc[-1]
            analysis_results['indicators']['bb_middle'] = bbands_manual_df['middle_band'].iloc[-1]
            analysis_results['indicators']['bb_upper'] = bbands_manual_df['upper_band'].iloc[-1]
        else:
            analysis_results['indicators']['bb_lower'] = None
            analysis_results['indicators']['bb_middle'] = None
            analysis_results['indicators']['bb_upper'] = None

        analysis_results['last_price'] = market_data['close'].iloc[-1]
        return analysis_results

    def generate_signal(self, analysis: Dict, **kwargs) -> Dict:
        """Generates trading signal from Bollinger Bands analysis."""
        bb_lower = analysis.get('indicators', {}).get('bb_lower')
        bb_upper = analysis.get('indicators', {}).get('bb_upper')
        last_price = analysis.get('last_price')

        signal = 'hold'
        confidence = 0.5 # Default confidence

        if bb_lower is None or bb_upper is None or last_price is None:
            return {'signal': 'hold', 'confidence': 0.0, 'reason': 'Missing Bollinger Band or price data'}

        # Buy Signal: Price touches or crosses below the lower Bollinger Band
        if last_price <= bb_lower:
            signal = 'buy'
            # Confidence could be higher the further price is below lower band, or based on other factors.
            confidence = 0.70 + min(0.25, (bb_lower - last_price) / (bb_lower * 0.05 if bb_lower > 0 else 0.01)) # Max confidence around 0.95

        # Sell Signal: Price touches or crosses above the upper Bollinger Band
        elif last_price >= bb_upper:
            signal = 'sell'
            confidence = 0.70 + min(0.25, (last_price - bb_upper) / (bb_upper * 0.05 if bb_upper > 0 else 0.01))
        
        # Optional: Add logic for mean reversion towards middle band as target, or other conditions.

        return {
            'signal': signal,
            'confidence': min(0.95, confidence), # Cap confidence
            'target_price': analysis.get('indicators', {}).get('bb_middle') if signal != 'hold' else None, # Target middle band
            'stop_loss': (bb_lower * 0.98) if signal == 'buy' else (bb_upper * 1.02 if signal == 'sell' else None) # Example stop loss
        }

    def get_parameters(self) -> dict:
        return self.parameters 