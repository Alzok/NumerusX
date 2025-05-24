from typing import Dict, Type, Optional, List
from app.strategy_framework import BaseStrategy
from app.strategies.momentum_strategy import MomentumStrategy
from app.strategies.mean_reversion_strategy import MeanReversionStrategy
from app.strategies.trend_following_strategy import TrendFollowingStrategy
from app.analytics_engine import AdvancedTradingStrategy # This is also a BaseStrategy
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class StrategySelector:
    def __init__(self):
        self.strategies: Dict[str, Type[BaseStrategy]] = {
            AdvancedTradingStrategy().get_name(): AdvancedTradingStrategy,
            MomentumStrategy().get_name(): MomentumStrategy,
            MeanReversionStrategy().get_name(): MeanReversionStrategy,
            TrendFollowingStrategy().get_name(): TrendFollowingStrategy,
            # Add other strategies here as they are created
        }
        self.default_strategy_name = Config.DEFAULT_STRATEGY_NAME
        self.logger = logger

        if self.default_strategy_name not in self.strategies:
            self.logger.warning(
                f"Default strategy '{self.default_strategy_name}' not found in available strategies. "
                f"Falling back to '{AdvancedTradingStrategy().get_name()}'."
            )
            self.default_strategy_name = AdvancedTradingStrategy().get_name()

    def get_strategy_instance(self, strategy_name: Optional[str] = None, **kwargs) -> Optional[BaseStrategy]:
        """ 
        Get an instance of a strategy by name. 
        If no name is provided, returns an instance of the default strategy.
        kwargs are passed to the strategy constructor.
        """
        s_name = strategy_name if strategy_name else self.default_strategy_name
        
        strategy_class = self.strategies.get(s_name)
        if strategy_class:
            try:
                # Check if kwargs are provided, otherwise initialize with defaults
                if kwargs:
                    # TODO: Implement a way to pass only relevant kwargs to strategy constructor
                    # For now, this might fail if strategy doesn't accept all kwargs or has specific needs.
                    # A better approach might involve each strategy exposing its configurable params.
                    # Or, the selector could know which params belong to which strategy.
                    # For simplicity now, if kwargs are present, we assume they are meant for the strategy.
                    # This is a known simplification and needs refinement for robust dynamic instantiation.
                    # For example, if a strategy takes (period=10) and kwargs is {'period': 20, 'other_param': 1}
                    # it should only pass {'period': 20}.
                    # A simple filter: strategy_params = {k: v for k, v in kwargs.items() if k in strategy_class().get_parameters()}
                    # instance = strategy_class(**strategy_params)
                    
                    # Current simplified approach: pass all kwargs. This requires strategies to handle unknown kwargs gracefully
                    # or for the caller to be precise.
                    # Most strategies define defaults, so calling without kwargs is fine.
                    # If specific parameters are needed, they must be passed in kwargs.
                    # Example: get_strategy_instance("MomentumStrategy", rsi_period=20)
                    instance = strategy_class(**kwargs) 
                else:
                    instance = strategy_class() # Initialize with default parameters
                
                self.logger.info(f"Strategy instance '{s_name}' created.")
                return instance
            except Exception as e:
                self.logger.error(f"Error instantiating strategy '{s_name}' with params {kwargs}: {e}", exc_info=True)
                return None # Or fallback to default if instantiation fails
        else:
            self.logger.warning(f"Strategy '{s_name}' not found.")
            return None

    def list_available_strategies(self) -> List[str]:
        return list(self.strategies.keys())

    def get_default_strategy_name(self) -> str:
        return self.default_strategy_name

# Example Usage (for testing or direct use):
if __name__ == '__main__':
    selector = StrategySelector()
    print(f"Available strategies: {selector.list_available_strategies()}")
    print(f"Default strategy: {selector.get_default_strategy_name()}")

    # Get default strategy instance
    default_strategy_instance = selector.get_strategy_instance()
    if default_strategy_instance:
        print(f"Default strategy instance created: {default_strategy_instance.get_name()}")
        print(f"Default strategy params: {default_strategy_instance.get_parameters()}")

    # Get a specific strategy with default params
    momentum_default = selector.get_strategy_instance("MomentumStrategy")
    if momentum_default:
        print(f"Momentum (default params) instance: {momentum_default.get_name()}, Params: {momentum_default.get_parameters()}")

    # Get a specific strategy with custom params
    momentum_custom = selector.get_strategy_instance("MomentumStrategy", rsi_period=21, macd_slow=30)
    if momentum_custom:
        print(f"Momentum (custom params) instance: {momentum_custom.get_name()}, Params: {momentum_custom.get_parameters()}")

    # Try to get a non-existent strategy
    non_existent = selector.get_strategy_instance("NonExistentStrategy")
    if not non_existent:
        print("Successfully handled non-existent strategy request.")

    # Get AdvancedTradingStrategy (which is also BaseStrategy derived)
    advanced_strat = selector.get_strategy_instance(AdvancedTradingStrategy().get_name())
    if advanced_strat:
         print(f"Advanced strategy instance: {advanced_strat.get_name()}, Params: {advanced_strat.get_parameters()}") 