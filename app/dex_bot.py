import asyncio # Added for async sleep and operations
import logging
from app.market.market_data import MarketDataProvider # Changed import
from app.trading.trading_engine import TradingEngine # Assuming this is the correct name now
from app.security.security import SecurityChecker # Assuming this is the correct name now
from app.strategy_framework import BaseStrategy
from app.strategy_selector import StrategySelector # Import StrategySelector
from app.logger import DexLogger # Assuming a logger class
from app.database import EnhancedDatabase
import time
import logging
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
from datetime import datetime # Added for timestamp_utc
import uuid # Added for request_id

from app.models.ai_inputs import (
    AggregatedInputs,
    MarketDataInput,
    SignalSourceInput,
    PredictionEngineInput,
    RiskManagerInput,
    PortfolioManagerInput,
    SecurityCheckerInput
)
from app.socket_manager import get_socket_manager
import logging

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
        
        # Initialize Socket.io manager
        try:
            self.socket_manager = get_socket_manager()
            logger.info("Socket.io manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Socket.io manager: {e}")
            self.socket_manager = None
        
        self.performance_monitor = PerformanceMonitor() # Keep for now
        # Initial portfolio value tracking will be in an async setup method
        
        self.active = False
        self.main_loop_task: Optional[asyncio.Task] = None
        logger.info("DexBot initialized successfully.")

    async def _initialize_async_dependencies(self):
        """Handles initialization steps that require async operations, like fetching initial portfolio value."""
        try:
            initial_portfolio_value = await self.portfolio_manager.get_total_portfolio_value()
            # Ensure RiskManager has the latest portfolio value. This could be a direct update or managed internally by RM.
            self.risk_manager.update_current_portfolio_value(initial_portfolio_value)
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

    async def _gather_ai_agent_inputs(self, target_symbol: str, target_mint: str, base_mint_for_pair: str, base_symbol_for_pair: str) -> Optional[AggregatedInputs]:
        """
        Gathers all necessary inputs from various bot components and assembles
        them into the AggregatedInputs Pydantic model for the AIAgent.
        This corresponds to todo/02-todo-ai-api-gemini.md Tâche 3.1.5
        """
        request_id = str(uuid.uuid4())
        timestamp_utc = datetime.utcnow()
        current_pair_symbol_str = f"{target_symbol}/{base_symbol_for_pair}"
        logger.info(f"Gathering inputs for AIAgent (request_id: {request_id}, pair: {current_pair_symbol_str})")

        target_pair_info = TargetPairInfo(
            symbol=current_pair_symbol_str,
            input_mint=target_mint, # Assuming target_mint is the one we want to buy/sell
            output_mint=base_mint_for_pair # And base_mint is the quote currency
        )

        # 1. Market Data
        market_data_input: Optional[MarketDataInput] = None
        try:
            md_price_result = await self.market_data_provider.get_token_price(target_mint, base_mint_for_pair)
            md_ohlcv_result = await self.market_data_provider.get_ohlcv_data_dexscreener(current_pair_symbol_str, '1h', limit=24) # Example: 1h, last 24 periods
            md_liquidity_result = await self.market_data_provider.get_liquidity_info_dexscreener(current_pair_symbol_str)
            # TODO: Add calls for trend, support/resistance, volatility, volume if available
            
            ohlcv_list = []
            if md_ohlcv_result['success'] and md_ohlcv_result['data']:
                for bar in md_ohlcv_result['data'][:24]: # Take up to 24 candles for the prompt
                    ohlcv_list.append(OHLCV(t=int(bar['timestamp']/1000), o=bar['open'], h=bar['high'], l=bar['low'], c=bar['close'], v=bar['volumeUsd']))

            market_data_input = MarketDataInput(
                current_price=md_price_result['data']['price'] if md_price_result['success'] else None,
                recent_ohlcv_1h=ohlcv_list if ohlcv_list else None,
                liquidity_depth_usd=md_liquidity_result['data']['liquidity_usd'] if md_liquidity_result['success'] and md_liquidity_result['data'] else None,
                # Fields like recent_trend_1h, key_support_resistance, volatility_1h_atr_percentage, trading_volume_24h_usd need to be populated
                # For now, we'll leave them as None or with placeholder logic if easy
                trading_volume_24h_usd=md_liquidity_result['data']['volume_24h_usd'] if md_liquidity_result['success'] and md_liquidity_result['data'] else None
            )
        except Exception as e:
            logger.error(f"Error gathering market data for AIAgent: {e}", exc_info=True)
            # Decide if this is critical; for now, we might proceed with partial data

        if not market_data_input or not market_data_input.current_price:
            logger.warning("Critical market data (current price) missing for AIAgent. Skipping decision.")
            return None

        # 2. Signal Sources (Strategies, Analytics Engine)
        signal_sources_inputs: List[SignalSourceInput] = []
        try:
            if self.strategy:
                # This needs to be async if strategy.analyze or generate_signal is async
                # For now, assuming synchronous or handled within strategy methods
                # The strategy's output needs to be adapted to SignalSourceInput format
                strategy_output = await self.strategy.generate_signal_async() # Assuming an async method returning a dict
                if strategy_output and strategy_output.get('signal') != 'NEUTRAL': # Example: only add non-neutral signals
                    signal_sources_inputs.append(SignalSourceInput(
                        source_name=self.strategy.get_name(),
                        signal=strategy_output.get('signal', 'ERROR').upper(), # Ensure uppercase standard
                        confidence=strategy_output.get('confidence'),
                        indicators=strategy_output.get('indicators'),
                        reasoning_snippet=strategy_output.get('reasoning')
                    ))
            # TODO: Add AdvancedAnalyticsEngine if it becomes a separate signal provider
        except Exception as e:
            logger.error(f"Error gathering signal sources for AIAgent: {e}", exc_info=True)

        # 3. Prediction Engine Outputs
        prediction_engine_outputs_input: Optional[PredictionEngineInput] = None
        try:
            if self.prediction_engine:
                # Assuming PricePredictor has a method get_formatted_predictions_for_agent
                # or we adapt its current output here.
                # For now, let's assume a simplified structure or placeholder
                raw_predictions = await self.prediction_engine.predict_price_async(target_symbol) # Assuming it takes target_symbol
                if raw_predictions and raw_predictions.predicted_price_4h is not None:
                    price_pred = PricePrediction(
                        target_price_min=raw_predictions.predicted_price_4h * 0.98, # Example
                        target_price_max=raw_predictions.predicted_price_4h * 1.02, # Example
                        prediction_period_hours=4,
                        confidence=raw_predictions.confidence, # Assuming predictor gives this
                        model_name=raw_predictions.model_name
                    )
                    prediction_engine_outputs_input = PredictionEngineInput(price_prediction_4h=price_pred)
                # TODO: Populate market_regime_1h and sentiment_analysis if PredictionEngine provides them
        except Exception as e:
            logger.error(f"Error gathering prediction engine outputs for AIAgent: {e}", exc_info=True)

        # 4. Risk Manager Inputs
        risk_manager_inputs_model: Optional[RiskManagerInput] = None
        try:
            # RiskManager might need the target_symbol to give context-specific risk advice, or it provides general limits.
            # Let's assume it provides general limits for now.
            # Ensure portfolio value is up-to-date in RiskManager before these calls.
            # This was handled in _initialize_async_dependencies and should be updated periodically.
            await self.portfolio_manager.update_portfolio_value() # Ensure portfolio value is fresh
            current_portfolio_value = self.portfolio_manager.total_portfolio_value_usd
            self.risk_manager.update_current_portfolio_value(current_portfolio_value)

            max_trade_size_usd = self.risk_manager.calculate_max_trade_size_usd(target_symbol) # target_symbol might be optional
            available_capital = self.portfolio_manager.get_available_cash_usdc() # USDC assumed

            risk_manager_inputs_model = RiskManagerInput(
                max_exposure_per_trade_percentage=self.config.MAX_PORTFOLIO_EXPOSURE_PER_TRADE, # From global config
                current_portfolio_value_usd=current_portfolio_value,
                available_capital_usdc=available_capital,
                max_trade_size_usd=max_trade_size_usd,
                overall_portfolio_risk_level=self.risk_manager.get_overall_portfolio_risk_level() # Example method
            )
        except Exception as e:
            logger.error(f"Error gathering risk manager inputs for AIAgent: {e}", exc_info=True)
        
        if not risk_manager_inputs_model:
            logger.warning("Critical risk manager inputs missing for AIAgent. Skipping decision.")
            return None

        # 5. Portfolio Manager Inputs
        portfolio_manager_inputs_model: Optional[PortfolioManagerInput] = None
        try:
            active_positions_raw = await self.portfolio_manager.get_active_trades() # Assuming this gets current positions
            pydantic_positions = []
            if active_positions_raw:
                for pos_dict in active_positions_raw:
                    # This needs current price for the asset to calculate current_value_usd and PNL
                    # Assuming PortfolioManager handles this or we fetch it here.
                    # For simplicity, we'll use entry price as current if not available.
                    current_asset_price = pos_dict.get('current_price_usd', pos_dict['entry_price_usd'])
                    amount_tokens = pos_dict['amount_input_token']
                    entry_price_usd = pos_dict['entry_price_usd']
                    current_value_usd = amount_tokens * current_asset_price
                    unrealized_pnl_usd = (current_asset_price - entry_price_usd) * amount_tokens
                    unrealized_pnl_percentage = ((current_asset_price - entry_price_usd) / entry_price_usd) * 100 if entry_price_usd else 0

                    pydantic_positions.append(PortfolioPositionInput(
                        symbol=pos_dict['token_pair'],
                        amount_tokens=amount_tokens,
                        entry_price_usd=entry_price_usd,
                        current_price_usd=current_asset_price,
                        current_value_usd=current_value_usd,
                        unrealized_pnl_usd=unrealized_pnl_usd,
                        unrealized_pnl_percentage=unrealized_pnl_percentage
                    ))
            
            realized_pnl_24h = await self.portfolio_manager.get_realized_pnl_last_24h()

            portfolio_manager_inputs_model = PortfolioManagerInput(
                current_positions=pydantic_positions if pydantic_positions else None,
                total_pnl_realized_24h_usd=realized_pnl_24h
            )
        except Exception as e:
            logger.error(f"Error gathering portfolio manager inputs for AIAgent: {e}", exc_info=True)

        if not portfolio_manager_inputs_model:
            logger.warning("Critical portfolio manager inputs missing for AIAgent. Skipping decision.")
            return None

        # 6. Security Checker Inputs
        security_checker_inputs_model: Optional[SecurityCheckerInput] = None
        try:
            # Assuming SecurityChecker has a method to get combined score and alerts for a token
            security_info = await self.security_checker.check_token_security_async(target_mint)
            if security_info and security_info.get('score') is not None:
                alerts = []
                if security_info.get('alerts'): # Assuming alerts is a list of dicts
                    for alert_dict in security_info['alerts']:
                        alerts.append(TokenSecurityRisk(**alert_dict)) # Validate with Pydantic model
                
                security_checker_inputs_model = SecurityCheckerInput(
                    target_token_symbol=target_symbol,
                    target_token_security_score=security_info['score'],
                    target_token_recent_security_alerts=alerts if alerts else None
                )
        except Exception as e:
            logger.error(f"Error gathering security checker inputs for AIAgent: {e}", exc_info=True)
        
        # Assemble final AggregatedInputs
        try:
            aggregated_inputs = AggregatedInputs(
                request_id=request_id,
                timestamp_utc=timestamp_utc,
                target_pair=target_pair_info,
                market_data=market_data_input, # Already validated as non-None
                signal_sources=signal_sources_inputs,
                prediction_engine_outputs=prediction_engine_outputs_input,
                risk_manager_inputs=risk_manager_inputs_model, # Already validated as non-None
                portfolio_manager_inputs=portfolio_manager_inputs_model, # Already validated as non-None
                security_checker_inputs=security_checker_inputs_model
            )
            logger.info(f"Successfully gathered inputs for AIAgent (request_id: {request_id}).")
            return aggregated_inputs
        except Exception as e: # Catch Pydantic validation errors or other issues
            logger.critical(f"Failed to assemble final AggregatedInputs for AIAgent (request_id: {request_id}): {e}", exc_info=True)
            return None

    async def _run_cycle(self):
        """Exécute un cycle complet de logique de trading."""
        try:
            # 0. Determine target pair for this cycle (using config for now)
            target_pair_info_tuple = await self._get_target_pair_mints(self.config.TARGET_TRADING_PAIR)
            if not target_pair_info_tuple:
                logger.error(f"Could not get mint info for target pair {self.config.TARGET_TRADING_PAIR}. Skipping cycle.")
                return
            
            target_symbol, target_mint, base_mint_for_pair, base_symbol_for_pair = target_pair_info_tuple
            current_pair_symbol_str = f"{target_symbol}/{base_symbol_for_pair}"
            logger.info(f"Processing cycle for pair: {current_pair_symbol_str}")

            # 1. Gather all inputs for the AIAgent
            # This step now returns a Pydantic model instance or None
            aggregated_inputs_model: Optional[AggregatedInputs] = await self._gather_ai_agent_inputs(
                target_symbol, target_mint, base_mint_for_pair, base_symbol_for_pair
            )

            if not aggregated_inputs_model:
                logger.warning(f"Failed to gather complete inputs for AIAgent for pair {current_pair_symbol_str}. Skipping AI decision.")
                # Potential: notify UI, increment error counter, etc.
                return

            # 2. Get decision from AIAgent
            # AIAgent.decide_trade now expects an AggregatedInputs object
            ai_decision_dict = await self.ai_agent.decide_trade(aggregated_inputs_model)

            # Record the AI's decision in database
            try:
                decision_data = {
                    "decision_id": aggregated_inputs_model.request_id,
                    "timestamp_utc": datetime.utcnow().isoformat(),
                    "decision_type": ai_decision_dict.get("decision", "HOLD"),
                    "token_pair": current_pair_symbol_str,
                    "amount_usd": ai_decision_dict.get("amount_usd"),
                    "confidence": ai_decision_dict.get("confidence", 0.0),
                    "stop_loss_price": ai_decision_dict.get("stop_loss_price"),
                    "take_profit_price": ai_decision_dict.get("take_profit_price"),
                    "reasoning": ai_decision_dict.get("reasoning", "No reasoning provided"),
                    "full_prompt": ai_decision_dict.get("full_prompt"),
                    "raw_response": ai_decision_dict.get("raw_response"),
                    "aggregated_inputs": aggregated_inputs_model.model_dump(),
                    "execution_status": "PENDING",
                    "gemini_tokens_input": ai_decision_dict.get("usage_metadata", {}).get("prompt_token_count"),
                    "gemini_tokens_output": ai_decision_dict.get("usage_metadata", {}).get("candidates_token_count"),
                    "gemini_cost_usd": ai_decision_dict.get("usage_metadata", {}).get("total_cost_usd")
                }
                
                decision_id = self.database.record_ai_decision(decision_data)
                if decision_id:
                    logger.info(f"AI decision recorded: {decision_id}")
                    
                    # Emit to Socket.io clients
                    if hasattr(self, 'socket_manager'):
                        await self.socket_manager.emit_ai_agent_decision({
                            "decision_id": decision_id,
                            "decision": ai_decision_dict.get("decision"),
                            "confidence": ai_decision_dict.get("confidence"),
                            "reasoning": ai_decision_dict.get("reasoning", "")[:100],  # Truncated for UI
                            "token_pair": current_pair_symbol_str
                        })
                else:
                    logger.error("Failed to record AI decision in database")
                    
            except Exception as log_e:
                logger.error(f"Error recording AI agent decision: {log_e}", exc_info=True)

            # 3. Execute trade if BUY or SELL decision
            if ai_decision_dict and ai_decision_dict.get("decision") in ["BUY", "SELL"]:
                logger.info(f"AIAgent decided to {ai_decision_dict['decision']} {current_pair_symbol_str}. Attempting execution.")
                
                # Pass the entire decision dictionary to TradeExecutor
                # TradeExecutor.execute_agent_order will extract necessary fields
                # and perform further checks (e.g., amount_usd is not None).
                trade_result = await self.trade_executor.execute_agent_order(ai_decision_dict)
                
                if trade_result['success']:
                    logger.info(f"Trade executed successfully for {current_pair_symbol_str}. Signature: {trade_result.get('signature')}")
                    self.performance_monitor.track_trade(trade_result.get('pnl_usd', 0), True) # Assuming PNL is part of result
                else:
                    logger.error(f"Trade execution failed for {current_pair_symbol_str}: {trade_result.get('error')}. Details: {trade_result.get('details')}")
                    self.performance_monitor.track_trade(0, False)
            elif ai_decision_dict and ai_decision_dict.get("decision") == "HOLD":
                logger.info(f"AIAgent decided to HOLD for {current_pair_symbol_str}. Reasoning: {ai_decision_dict.get('reasoning')}")
            else:
                logger.warning(f"AIAgent returned an invalid or no decision for {current_pair_symbol_str}: {ai_decision_dict}")

            # 4. Update portfolio value for RiskManager and PerformanceMonitor after potential trade
            current_portfolio_value = await self.portfolio_manager.get_total_portfolio_value()
            self.risk_manager.update_current_portfolio_value(current_portfolio_value)
            self.performance_monitor.track_portfolio_value(current_portfolio_value)
            logger.debug(f"Portfolio value updated post-cycle: ${current_portfolio_value:.2f}")

        except DataCollectionError as dce: # Specific error for data gathering issues
            logger.error(f"Data collection error in DexBot cycle: {dce}", exc_info=True)
            # Potentially pause bot or increase sleep interval on repeated errors
        except NumerusXBaseError as nxe: # Catch custom app errors
            logger.error(f"NumerusX specific error in DexBot cycle: {nxe}", exc_info=True)
        except asyncio.CancelledError:
            logger.info("DexBot cycle was cancelled.")
            raise # Re-raise to be caught by the run method's handler
        except Exception as e:
            logger.critical(f"Unexpected critical error in DexBot cycle: {e}", exc_info=True)
            # This might indicate a need to stop the bot if errors persist
            # For now, it will log and the main_loop will attempt to continue after sleep
            
    async def _get_market_data_for_pair(self, target_symbol: str, base_symbol: str, target_mint: str, base_mint: str) -> Dict[str, Any]:
        """Helper to fetch and structure market data for a given pair."""
        # This method might be deprecated or simplified if _gather_ai_agent_inputs handles all data directly.
        # For now, keeping it as a potential internal helper for specific data points if needed elsewhere.
        pair_data = {}
        try:
            price_info = await self.market_data_provider.get_token_price(target_mint, base_mint)
            if price_info['success']:
                pair_data['price'] = price_info['data']['price']
            else:
                logger.warning(f"Could not fetch price for {target_symbol}/{base_symbol}: {price_info.get('error')}")
                pair_data['price'] = None
            
            # Add more data points as needed: volume, liquidity, indicators etc.
            # Example for volume (assuming a method in MarketDataProvider exists or is added)
            # volume_info = await self.market_data_provider.get_volume_24h(f"{target_symbol}/{base_symbol}")
            # if volume_info['success']:
            #     pair_data['volume_24h'] = volume_info['data']['volume_usd']

        except Exception as e:
            logger.error(f"Error fetching market data for {target_symbol}/{base_symbol}: {e}", exc_info=True)
            # Ensure basic structure even on error
            if 'price' not in pair_data: pair_data['price'] = None
        return pair_data

    def stop(self):
        """Arrête le bot de trading de manière propre."""
        if not self.active:
            logger.info("DexBot is not running.")
            return
        
        self.active = False
        if self.main_loop_task:
            self.main_loop_task.cancel()
            # await self.main_loop_task # Wait for it to actually cancel, handle exceptions
        logger.info("DexBot has been signaled to stop.")

    async def close(self):
        """Ferme proprement toutes les connexions et ressources."""
        logger.info("Closing DexBot resources...")
        if self.active or self.main_loop_task:
            self.stop()
            # Give a bit of time for the loop to cancel if it hasn't already been awaited
            if self.main_loop_task and not self.main_loop_task.done():
                try:
                    await asyncio.wait_for(self.main_loop_task, timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for main loop to finish during close.")
                except asyncio.CancelledError:
                    pass # Expected

        # Close JupiterApiClient (which closes Solana AsyncClient)
        # Already handled by async with in run() method if it exits cleanly.
        # Explicit call here is for cases where run() might not have completed its context management.
        # if self.jupiter_client:
        #     await self.jupiter_client.close_async_client()
        #     logger.info("JupiterApiClient closed.")

        if self.market_data_provider:
            await self.market_data_provider.close_session() # If MarketDataProvider has a session
            logger.info("MarketDataProvider session closed.")
            
        # if self.trading_engine: # TradingEngine might also have resources to close
        #     await self.trading_engine.close_resources() 
        #     logger.info("TradingEngine resources closed.")

        logger.info("DexBot closed.")

async def main():
    # Load configuration
    config = Config()
    
    # Configure logging (basic example)
    log_level = logging.DEBUG if config.DEBUG_MODE else logging.INFO
    logging.basicConfig(level=log_level, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]) # Add file handler for production

    logger.info("Starting NumerusX DexBot application...")
    bot = DexBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("DexBot run interrupted by user (KeyboardInterrupt).")
    except RuntimeError as e:
        logger.critical(f"DexBot failed to start or run due to a runtime error: {e}", exc_info=True)
    finally:
        logger.info("DexBot shutting down...")
        await bot.close()
        logger.info("DexBot has shut down.")

if __name__ == "__main__":
    asyncio.run(main())