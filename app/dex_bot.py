import asyncio # Added for async sleep and operations
from app.market.market_data import MarketDataProvider # Changed import
from app.trading.trading_engine import TradingEngine # Assuming this is the correct name now
from app.security.security import SecurityChecker # Assuming this is the correct name now
from app.strategy_framework import BaseStrategy
from app.strategy_selector import StrategySelector # Import StrategySelector
from app.logger import DexLogger # Assuming a logger class
from app.database import EnhancedDatabase
import time
from typing import List, Dict, Optional, Any, Tuple # Added Tuple
from app.config import Config
from app.prediction_engine import PricePredictor, PredictionResult # Import necessary classes
from app.risk_manager import RiskManager, Position # Import RiskManager and Position
from app.portfolio_manager import PortfolioManager # Ensure this is the main PortfolioManager
from app.trade_executor import TradeExecutor # Import TradeExecutor
import pandas as pd
from app.ai_agent import AIAgent # Import the new AIAgent
import json # For logging agent decisions
from app.utils.jupiter_api_client import JupiterApiClient # Added
from app.utils.exceptions import NumerusXBaseError, DataCollectionError # For general error handling and DataCollectionError

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.history = [] 
        self.trades = [] 
    
    def track_portfolio_value(self, value: float):
        self.history.append({
            'timestamp': time.time(),
            'metric': 'portfolio_value',
            'value': value
        })
    
    def track_trade(self, pnl: float, success: bool):
        self.trades.append({
            'timestamp': time.time(),
            'pnl': pnl,
            'success': success
        })
    
    @property
    def daily_pnl_percentage(self) -> float:
        if not self.trades or Config.INITIAL_PORTFOLIO_BALANCE_USD == 0:
            return 0.0
        now = time.time()
        pnl_24h = sum(t['pnl'] for t in self.trades if now - t['timestamp'] <= 86400)
        return (pnl_24h / Config.INITIAL_PORTFOLIO_BALANCE_USD) * 100

class DexBot:
    def __init__(self):
        self.config = Config()
        logger.info("Initializing DexBot components...")

        # Core Clients & Providers
        try:
            self.jupiter_client = JupiterApiClient(
                solana_private_key_bs58=self.config.SOLANA_PRIVATE_KEY_BS58,
                rpc_url=self.config.RPC_URL, # JupiterApiClient will use default if None
                config=self.config 
            )
            logger.info("JupiterApiClient initialized.")

            self.market_data_provider = MarketDataProvider(
                config=self.config,
                jupiter_client=self.jupiter_client
            )
            logger.info("MarketDataProvider initialized.")

            self.trading_engine = TradingEngine(
                config=self.config,
                jupiter_client=self.jupiter_client
            )
            logger.info("TradingEngine initialized.")

        except Exception as e:
            logger.critical(f"Failed to initialize core clients (Jupiter, MarketData, TradingEngine): {e}", exc_info=True)
            raise RuntimeError("DexBot core client initialization failed.") from e

        # Managers & Checkers
        try:
            self.portfolio_manager = PortfolioManager(
                db_path=self.config.DB_PATH,
                market_data_provider=self.market_data_provider
            )
            logger.info("PortfolioManager initialized.")

            self.risk_manager = RiskManager(
                portfolio_manager=self.portfolio_manager,
                market_data_provider=self.market_data_provider,
                config=self.config # Pass config if RiskManager needs it
            )
            logger.info("RiskManager initialized.")
            
            # Initialize RiskManager with current portfolio value
            # This needs to be async if get_total_portfolio_value is async
            # For now, assuming a synchronous way or it's handled in an async setup method

            self.security_checker = SecurityChecker(
                # db_path=self.config.DB_PATH, # SecurityChecker might not need DB
                market_data_provider=self.market_data_provider,
                config=self.config
            )
            logger.info("SecurityChecker initialized.")
            
            self.trade_executor = TradeExecutor(
                config=self.config,
                trading_engine=self.trading_engine,
                portfolio_manager=self.portfolio_manager,
                risk_manager=self.risk_manager,
                market_data_provider=self.market_data_provider
            )
            logger.info("TradeExecutor initialized.")

        except Exception as e:
            logger.critical(f"Failed to initialize managers (Portfolio, Risk, Security, TradeExecutor): {e}", exc_info=True)
            raise RuntimeError("DexBot manager initialization failed.") from e

        # Strategy (Input Source for AIAgent)
        self.strategy_selector = StrategySelector(config=self.config) # Pass config if selector needs it
        self.strategy: Optional[BaseStrategy] = self.strategy_selector.get_strategy_instance()
        if not self.strategy:
            logger.warning("No default strategy could be initialized by StrategySelector. AIAgent might lack this input.")
        else:
            logger.info(f"Default strategy selected as input source: {self.strategy.get_name()}")

        # Prediction Engine (Input Source for AIAgent)
        try:
            self.prediction_engine = PricePredictor(
                model_dir=self.config.PREDICTION_MODEL_DIR,
                data_dir=self.config.PREDICTION_DATA_DIR,
                config=self.config # Pass config if predictor needs it
            )
            logger.info("PredictionEngine initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize PredictionEngine: {e}", exc_info=True)
            self.prediction_engine = None # Bot can run without it, AIAgent will get None for predictions

        # AI Agent (Core Decider)
        try:
            self.ai_agent = AIAgent(config=self.config) # AIAgent takes config
            logger.info("AIAgent initialized.")
        except Exception as e:
            logger.critical(f"Failed to initialize AIAgent: {e}", exc_info=True)
            raise RuntimeError("DexBot AIAgent initialization failed.") from e
        
        self.performance_monitor = PerformanceMonitor() # Keep for now
        # Initial portfolio value tracking will be in an async setup method
        
        self.active = False
        self.main_loop_task: Optional[asyncio.Task] = None
        logger.info("DexBot initialized successfully.")

    async def _initialize_async_dependencies(self):
        """Handles initialization steps that require async operations, like fetching initial portfolio value."""
        try:
            initial_portfolio_value = await self.portfolio_manager.get_total_portfolio_value()
            self.risk_manager.update_portfolio_value(initial_portfolio_value) # Assuming this is sync
            self.performance_monitor.track_portfolio_value(initial_portfolio_value)
            logger.info(f"Initial portfolio value for RiskManager and PerformanceMonitor: ${initial_portfolio_value:.2f}")
        except Exception as e:
            logger.error(f"Error during async initialization (portfolio value): {e}", exc_info=True)
            # Decide if this is critical. For now, bot might proceed with default/zero values.

    async def run(self):
        if self.active:
            logger.info("DexBot is already running.")
            return

        self.active = True
        logger.info(f"Starting DexBot. Strategy for AIAgent input: {self.strategy.get_name() if self.strategy else 'None'}.")
        
        await self._initialize_async_dependencies()

        # Manage contexts for JupiterApiClient, MarketDataProvider, and TradingEngine
        # TradingEngine and MarketDataProvider manage their internal resources if needed,
        # but JupiterApiClient is the primary one with a Solana client connection.
        async with self.jupiter_client, self.market_data_provider, self.trading_engine:
            self.main_loop_task = asyncio.create_task(self._main_loop())
            try:
                await self.main_loop_task
            except asyncio.CancelledError:
                logger.info("DexBot main loop was cancelled.")
            except Exception as e: # Catch any other unexpected errors from the main loop
                logger.critical(f"DexBot main loop exited due to an unhandled exception: {e}", exc_info=True)
                self.active = False # Ensure bot stops on critical loop error

    async def _main_loop(self):
        while self.active:
            try:
                cycle_start_time = time.monotonic()
                logger.info("--- Starting new DexBot cycle ---")
                await self._run_cycle()
                
                cycle_duration = time.monotonic() - cycle_start_time
                logger.info(f"--- DexBot cycle finished in {cycle_duration:.2f}s ---")
                
                sleep_duration = max(0, self.config.TRADING_UPDATE_INTERVAL_SECONDS - cycle_duration)
                if sleep_duration > 0 :
                    await asyncio.sleep(sleep_duration)
                else:
                    logger.warning(f"Cycle duration ({cycle_duration:.2f}s) exceeded TRADING_UPDATE_INTERVAL_SECONDS ({self.config.TRADING_UPDATE_INTERVAL_SECONDS}s). Running next cycle immediately.")

            except asyncio.CancelledError:
                logger.info("DexBot cycle processing cancelled.")
                self.active = False # Ensure loop terminates
                break # Exit the while loop
            except Exception as e:
                logger.error(f"Error in DexBot trading cycle: {e}", exc_info=True)
                # Potentially add a longer sleep here on repeated critical errors or specific error handling
                if self.active: # Avoid sleeping if stop() was called
                    await asyncio.sleep(self.config.TRADING_UPDATE_INTERVAL_SECONDS) # Wait before retrying cycle

    async def _get_target_pair_mints(self, pair_symbol_str: str) -> Optional[Tuple[str, str, str, str]]:
        """Parses pair_symbol_str (e.g., "SOL/USDC") and returns (target_symbol, base_symbol, target_mint, base_mint)."""
        parts = pair_symbol_str.split('/')
        if len(parts) != 2:
            logger.error(f"Invalid target pair format '{pair_symbol_str}'. Expected 'TOKEN1/TOKEN2'.")
            return None

        symbol1, symbol2 = parts[0].upper(), parts[1].upper()
        base_asset_sym = self.config.BASE_ASSET_SYMBOL.upper()
        
        target_symbol: Optional[str] = None
        base_symbol_for_pair: Optional[str] = None # This will be the other token in the pair, not necessarily THE base asset of the bot

        if symbol1 == base_asset_sym: # e.g., USDC/SOL, so SOL is target
            target_symbol = symbol2
            base_symbol_for_pair = symbol1
        elif symbol2 == base_asset_sym: # e.g., SOL/USDC, so SOL is target
            target_symbol = symbol1
            base_symbol_for_pair = symbol2
        else:
            # If neither is the bot's BASE_ASSET_SYMBOL, we can't easily determine direction
            # or which one is the "asset of interest". AIAgent needs this context.
            # For now, we require one to be the BASE_ASSET_SYMBOL for clarity in AIAgent prompt.
            logger.warning(f"Target pair '{pair_symbol_str}' does not include BASE_ASSET_SYMBOL '{base_asset_sym}'. Skipping for AIAgent input.")
            return None

        try:
            target_token_info_res = await self.market_data_provider.get_token_info(target_symbol)
            if not target_token_info_res.get('success') or not target_token_info_res['data']:
                logger.error(f"Could not fetch token info for target_symbol '{target_symbol}'. Error: {target_token_info_res.get('error')}")
                return None
            target_mint = target_token_info_res['data']['mint']
            
            # The "base" for the pair might be the bot's actual base asset (e.g. USDC) or another token.
            # If it's the bot's base asset, we use its mint from config.
            # Otherwise, we fetch its info too.
            if base_symbol_for_pair == base_asset_sym:
                base_mint = self.config.BASE_ASSET # Mint address of USDC, etc.
            else:
                # This case is currently excluded by the logic above, but if supported in future:
                base_token_info_res = await self.market_data_provider.get_token_info(base_symbol_for_pair)
                if not base_token_info_res.get('success') or not base_token_info_res['data']:
                    logger.error(f"Could not fetch token info for base_symbol_for_pair '{base_symbol_for_pair}'. Error: {base_token_info_res.get('error')}")
                    return None
                base_mint = base_token_info_res['data']['mint']
            
            return target_symbol, base_symbol_for_pair, target_mint, base_mint
        except Exception as e:
            logger.error(f"Error resolving mints for pair '{pair_symbol_str}': {e}", exc_info=True)
            return None

    async def _gather_ai_agent_inputs(self, target_symbol: str, target_mint: str, base_mint_for_pair: str, base_symbol_for_pair: str) -> Optional[Dict[str, Any]]:
        """Gathers all necessary inputs for the AIAgent for a specific target token and its pair."""
        logger.info(f"Gathering AI Agent inputs for target: {target_symbol} ({target_mint}) paired with {base_symbol_for_pair} ({base_mint_for_pair})...")
        inputs: Dict[str, Any] = {
            'timestamp_utc': time.time(),
            'target_pair_info': {
                'target_token_symbol': target_symbol,
                'target_token_mint': target_mint,
                'base_token_symbol_for_pair': base_symbol_for_pair, # The other token in the pair (e.g. USDC)
                'base_token_mint_for_pair': base_mint_for_pair
            },
            'market_data': { 'current_price': None, 'ohlcv_data': None, 'liquidity_info': None, 'trends': None },
            'signal_sources': { 'strategy_analysis': None },
            'prediction_engine_outputs': { 'price_prediction': None, 'market_regime': None },
            'risk_manager_inputs': {},
            'portfolio_manager_inputs': {},
            'security_checker_inputs': { 'target_token_security': None, 'base_token_security': None }
        }

        try:
            # 1. Market Data for Target Pair
            price_res = await self.market_data_provider.get_token_price(target_mint, base_mint_for_pair)
            inputs['market_data']['current_price'] = price_res['data'] if price_res.get('success') else None
            
            ohlcv_res = await self.market_data_provider.get_ohlcv_data(target_mint, base_mint_for_pair, timeframe='1h', limit=100)
            inputs['market_data']['ohlcv_data'] = ohlcv_res['data'] if ohlcv_res.get('success') else None
            
            # TODO: Add more market data: liquidity, trends (from MDP methods)
            # liquidity_res = await self.market_data_provider.get_liquidity_for_pair(target_mint, base_mint_for_pair) 
            # inputs['market_data']['liquidity_info'] = liquidity_res['data'] if liquidity_res.get('success') else None

            # 2. Signal Sources (Strategy Analysis)
            if self.strategy:
                # The strategy's `analyze` method needs to be adapted.
                # For now, assume it can take mints and return a dict of features.
                # This is a placeholder. The actual strategy `analyze` method might need `market_data` for its input.
                try:
                    strategy_input_data = inputs['market_data'] # Strategy might need current market data
                    # Strategy `analyze` method needs to be defined to accept this and return serializable dict
                    analysis_output = await self.strategy.analyze(target_mint, base_mint_for_pair, strategy_input_data)
                    inputs['signal_sources']['strategy_analysis'] = analysis_output
                except Exception as e:
                    logger.warning(f"Failed to get analysis from strategy '{self.strategy.get_name()}' for {target_symbol}: {e}", exc_info=True)
                    inputs['signal_sources']['strategy_analysis'] = {"error": str(e)}
            
            # 3. Prediction Engine Outputs
            if self.prediction_engine:
                try:
                    prediction: Optional[PredictionResult] = await self.prediction_engine.predict_price(target_mint, timeframe='1h')
                    if prediction:
                        inputs['prediction_engine_outputs']['price_prediction'] = prediction.to_dict() # Use to_dict()
                        # TODO: Market regime if PredictionEngine provides it
                    else:
                         inputs['prediction_engine_outputs']['price_prediction'] = None
                except Exception as e:
                    logger.warning(f"Failed to get prediction for {target_symbol}: {e}", exc_info=True)
                    inputs['prediction_engine_outputs']['price_prediction'] = {"error": str(e)}

            # 4. Risk Manager Inputs
            current_portfolio_value = await self.portfolio_manager.get_total_portfolio_value() # Refresh for latest
            self.risk_manager.update_portfolio_value(current_portfolio_value)
            inputs['risk_manager_inputs'] = {
                'max_risk_per_trade_usd': self.risk_manager.calculate_max_risk_per_trade_usd(),
                'current_total_exposure_usd': self.risk_manager.get_current_total_exposure_usd(),
                'global_risk_level': self.risk_manager.get_global_risk_level(),
                'available_capital_for_new_trade_usd': self.risk_manager.get_available_capital_for_new_trade_usd(target_mint)
            }

            # 5. Portfolio Manager Inputs
            inputs['portfolio_manager_inputs'] = {
                'available_cash_usd': self.portfolio_manager.get_available_cash_for_trading(),
                'total_portfolio_value_usd': current_portfolio_value,
                'open_positions': await self.portfolio_manager.get_open_positions_summary(output_format='dict'),
                'target_token_position': await self.portfolio_manager.get_position_details(target_mint)
            }

            # 6. Security Checker Inputs
            target_is_safe, target_risks = await self.security_checker.check_token_security(target_mint)
            inputs['security_checker_inputs']['target_token_security'] = {
                'is_safe': target_is_safe,
                'risks': [r.to_dict() for r in target_risks] if target_risks else []
            }
            if base_mint_for_pair != self.config.BASE_ASSET: # Only check non-USDC base
                base_is_safe, base_risks = await self.security_checker.check_token_security(base_mint_for_pair)
                inputs['security_checker_inputs']['base_token_security'] = {
                    'is_safe': base_is_safe,
                    'risks': [r.to_dict() for r in base_risks] if base_risks else []
                }
            else:
                 inputs['security_checker_inputs']['base_token_security'] = {'is_safe': True, 'risks': [], 'info': 'Bot base asset (e.g. USDC)'}
            
            logger.info(f"Successfully gathered AI inputs for {target_symbol}.")
            return inputs

        except Exception as e:
            logger.error(f"Critical error gathering AI Agent inputs for {target_symbol} ({target_mint}): {e}", exc_info=True)
            # Raise a custom error to be caught by _run_cycle if data collection fails catastrophically
            raise DataCollectionError(f"Failed to gather inputs for {target_symbol}: {e}") from e

    async def _run_cycle(self):
        try:
            # Update portfolio value at the start of the cycle for general monitoring
            current_portfolio_val = await self.portfolio_manager.get_total_portfolio_value()
            self.risk_manager.update_portfolio_value(current_portfolio_val)
            self.performance_monitor.track_portfolio_value(current_portfolio_val)
            logger.info(f"Current estimated portfolio value: ${current_portfolio_val:.2f}")
        except Exception as e:
            logger.error(f"Error updating portfolio value for cycle: {e}", exc_info=True)
            # Not raising here, as the bot might still function or attempt recovery

        # Determine target pair for this cycle
        # For now, use a primary pair from config. Can be expanded to loop through multiple pairs.
        primary_pair_str = self.config.PRIMARY_TRADING_PAIR_SYMBOLS
        if not primary_pair_str:
            logger.warning("PRIMARY_TRADING_PAIR_SYMBOLS not set in config. DexBot cannot select a target pair.")
            return

        target_pair_details = await self._get_target_pair_mints(primary_pair_str)
        if not target_pair_details:
            logger.error(f"Could not resolve mints for primary trading pair '{primary_pair_str}'. Skipping cycle.")
            return
        
        target_symbol, base_symbol_for_pair, target_mint, base_mint_for_pair = target_pair_details
        logger.info(f"Processing cycle for target pair: {target_symbol}/{base_symbol_for_pair} ({target_mint}/{base_mint_for_pair})")

        aggregated_inputs: Optional[Dict[str, Any]] = None
        try:
            aggregated_inputs = await self._gather_ai_agent_inputs(target_symbol, target_mint, base_mint_for_pair, base_symbol_for_pair)
        except DataCollectionError as dce:
            logger.error(f"Data collection failed for {target_symbol}, cannot proceed with AI decision: {dce}")
            return # Skip AI decision and execution if critical data is missing
        except Exception as e:
            logger.critical(f"Unexpected error during input gathering for {target_symbol}: {e}", exc_info=True)
            return # Safety stop for this cycle

        if not aggregated_inputs:
            logger.warning(f"No aggregated inputs gathered for {target_symbol}. Skipping AI decision.")
            return

        # Log aggregated inputs (or a summary for brevity)
        # logger.debug(f"Aggregated inputs for AIAgent ({target_symbol}): {json.dumps(aggregated_inputs, indent=2, default=str)}")
        # For production, consider logging to a separate file or a structured logging system if too verbose.
        logger.info(f"Sending inputs for {target_symbol} to AIAgent.")

        ai_decision_response: Optional[Dict[str, Any]] = None
        try:
            # ai_decision_response is the raw output dict from AIAgent.decide_trade
            ai_decision_response = await self.ai_agent.decide_trade(aggregated_inputs)
        except Exception as e:
            logger.error(f"Error during AIAgent.decide_trade for {target_symbol}: {e}", exc_info=True)
            # Continue, maybe log the failure and do not trade

        if not ai_decision_response:
            logger.warning(f"AIAgent returned no decision for {target_symbol}.")
            return

        logger.info(f"AIAgent decision for {target_symbol}: {ai_decision_response.get('decision')}, AmountUSD: {ai_decision_response.get('amount_usd')}, Confidence: {ai_decision_response.get('confidence')}")
        logger.debug(f"AIAgent full response for {target_symbol}: {json.dumps(ai_decision_response, indent=2, default=str)}")

        # Execute trade if decision is not HOLD and essential fields are present
        if ai_decision_response.get('decision') and ai_decision_response.get('decision').upper() != 'HOLD':
            # TradeExecutor expects a specific format from agent_order, which ai_decision_response should match
            # as defined in 02-todo-ai-api-gemini.md (output of Task 3.3)
            # Ensure `token_pair` is in "SYMBOL/SYMBOL" format for TradeExecutor if it internally parses it,
            # or pass mints directly if TradeExecutor is adapted. Our TradeExecutor now parses "SYMBOL/SYMBOL".
            # The ai_decision_response already contains `token_pair` as per spec.
            
            required_fields = ['decision', 'token_pair', 'amount_usd'] # Confidence, SL/TP are optional for execution
            if not all(field in ai_decision_response and ai_decision_response[field] is not None for field in required_fields):
                logger.error(f"AIAgent decision for {target_symbol} is missing required fields for execution. Decision: {ai_decision_response}")
                return
            
            if ai_decision_response['token_pair'].upper() != primary_pair_str.upper():
                 logger.warning(f"AIAgent returned decision for pair '{ai_decision_response['token_pair']}' which does not match current cycle target '{primary_pair_str}'. This might be valid if agent can suggest other pairs, but for now, aligning execution. Check agent's prompt and capabilities.")
                 # For now, we will proceed if the agent specified a pair, assuming it knows what it's doing.
                 # But it highlights a point of control/validation.

            logger.info(f"Transmitting AI order for {ai_decision_response['token_pair']} to TradeExecutor: {ai_decision_response.get('decision')} amount ${ai_decision_response.get('amount_usd')}")
            try:
                trade_successful = await self.trade_executor.execute_agent_order(ai_decision_response)
                if trade_successful:
                    logger.info(f"Trade based on AI decision for {ai_decision_response['token_pair']} submitted successfully by TradeExecutor.")
                else:
                    logger.error(f"Trade based on AI decision for {ai_decision_response['token_pair']} failed or was aborted by TradeExecutor.")
            except Exception as e:
                logger.critical(f"Critical error during TradeExecutor.execute_agent_order for {ai_decision_response['token_pair']}: {e}", exc_info=True)
        else:
            logger.info(f"AIAgent decision is HOLD or no valid action for {target_symbol}. No trade executed.")

    def stop(self):
        if not self.active:
            logger.info("DexBot is not running.")
            return
            
        self.active = False
        logger.info("Stopping DexBot...")
        if self.main_loop_task and not self.main_loop_task.done():
            self.main_loop_task.cancel()
            logger.info("Main loop cancellation requested.")
        else:
            logger.info("Main loop task was not running or already completed.")
        # Further cleanup (like closing client sessions) is handled by async context managers' __aexit__

    async def close(self):
        """Explicitly closes resources if needed, supplementing __aexit__ from context managers."""
        logger.info("DexBot close() called. Resources should be managed by context managers mostly.")
        # JupiterApiClient, MarketDataProvider, TradingEngine have __aexit__

# Example of how DexBot might be run (e.g., in app/main.py or a run script)
async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    bot = DexBot()
    try:
        await bot.run()
    except RuntimeError as e:
        logger.critical(f"Failed to start DexBot due to runtime error: {e}")
    except KeyboardInterrupt:
        logger.info("DexBot run interrupted by user.")
    finally:
        logger.info("Shutting down DexBot...")
        bot.stop() # Request stop
        # Allow time for cancellation to propagate and __aexit__ methods to run
        # In a real app, you might await a bot.wait_for_shutdown() method
        if bot.main_loop_task:
            try:
                await asyncio.wait_for(bot.main_loop_task, timeout=5.0) 
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for main loop to cleanly shut down.")
            except asyncio.CancelledError: # Expected if stop() worked
                pass
        await bot.close() # Final explicit cleanup
        logger.info("DexBot shutdown complete.")

if __name__ == '__main__':
    # This is for basic testing of DexBot initialization and run/stop.
    # In a real application, DexBot would be managed by a higher-level application structure.
    asyncio.run(main())