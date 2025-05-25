import asyncio # Added for async sleep and operations
from app.market.market_data import MarketDataProvider # Changed import
from app.trading.trading_engine import TradingEngine # Assuming this is the correct name now
from app.security.security import SecurityChecker # Assuming this is the correct name now
from app.strategy_framework import BaseStrategy
from app.strategy_selector import StrategySelector # Import StrategySelector
from app.logger import DexLogger # Assuming a logger class
from app.database import EnhancedDatabase
import time
from typing import List, Dict, Optional, Any
from app.config import Config
from app.prediction_engine import PricePredictor, PredictionResult # Import necessary classes
from app.risk_manager import RiskManager, Position # Import RiskManager and Position
from app.portfolio_manager import PortfolioManager # Import new PortfolioManager
from app.trade_executor import TradeExecutor # Import TradeExecutor
import pandas as pd
from app.ai_agent import AIAgent # Import the new AIAgent
import json # For logging agent decisions

class PortfolioManager:
    def __init__(self):
        self.db = EnhancedDatabase()
        self.current_cash_balance = Config.INITIAL_PORTFOLIO_BALANCE_USD # Renamed for clarity
        # TODO: Need a method to calculate total portfolio value (cash + open positions value)

    def get_available_cash(self) -> float: # Renamed for clarity
        # This is a simplified view, doesn't account for value of open positions if current_cash_balance is total equity
        # For now, assuming current_cash_balance is free cash for new trades.
        # A proper portfolio manager would track assets and their current market value.
        active_trades_value = 0
        for trade in self.db.get_active_trades(): # Assuming get_active_trades returns dicts with 'amount'
            active_trades_value += trade.get('amount', 0) # Assuming 'amount' is cost basis or current value
        # This logic is likely flawed for actual available funds. Needs review.
        # Returning self.current_cash_balance for now, to be refined.
        return self.current_cash_balance 

    def record_trade_executed(self, pair_address: str, amount_usd: float, entry_price: float, protocol: str, token_symbol: str, trade_id: Optional[str]=None, side: Optional[str]=None):
        trade_data_for_db = {
            'pair': pair_address,
            'amount': amount_usd, # Assuming this is the USD value invested/received
            'entry_price': entry_price,
            'protocol': protocol,
            'token_symbol': token_symbol, # Ensure DB schema handles this
            'trade_id': trade_id, # Ensure DB schema handles this
            'side': side # Ensure DB schema handles this
        }
        self.db.record_trade(trade_data_for_db)
        
        # Adjust cash balance based on trade side
        if side == 'BUY':
            self.current_cash_balance -= amount_usd # Reduce cash by amount invested
        elif side == 'SELL':
            self.current_cash_balance += amount_usd # Increase cash by amount received
        # Note: Portfolio value actually changes based on P&L, not just cash reduction/increase.

    def get_total_portfolio_value(self, market_data_provider: MarketDataProvider) -> float:
        # This is a placeholder and needs proper implementation
        # It should fetch current prices of open positions and sum with cash
        # For now, returning the initial balance + P&L (if tracked) or just cash balance as a rough estimate.
        # This is critical for accurate risk management.
        # Let's simulate it simply for now, assuming self.current_cash_balance is somewhat representative
        # of total equity if not many positions are open or if they are small.
        # A better approach: sum self.current_cash_balance + value of all open positions at current market price.
        return self.current_cash_balance # Placeholder - VERY IMPORTANT TODO

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
        self.logger = DexLogger().logger # Initialize logger early
        self.market_data_provider = MarketDataProvider()
        self.trader = TradingEngine(wallet_path=self.config.WALLET_PATH)
        self.security_checker = SecurityChecker(db_path=self.config.DB_PATH, market_data_provider=self.market_data_provider)
        
        # Initialize Strategy using StrategySelector
        self.strategy_selector = StrategySelector()
        self.strategy: Optional[BaseStrategy] = self.strategy_selector.get_strategy_instance()
        
        if not self.strategy:
            self.logger.critical("CRITICAL: No strategy could be initialized. DexBot cannot start.")
            # Depending on desired behavior, either raise an exception or ensure bot cannot run.
            # For now, self.strategy will be None, and run() should handle this.
            # Alternatively: raise RuntimeError("Failed to initialize a trading strategy.")
        else:
            self.logger.info(f"DexBot initialized with strategy: {self.strategy.get_name()}")
                                        
        self.portfolio_manager = PortfolioManager()
        self.risk_manager = RiskManager()
        initial_portfolio_value = self.portfolio_manager.get_total_portfolio_value(self.market_data_provider)
        self.risk_manager.update_portfolio_value(initial_portfolio_value)
        
        self.trade_executor = TradeExecutor( 
            trading_engine=self.trader,
            portfolio_manager=self.portfolio_manager,
            risk_manager=self.risk_manager,
            market_data_provider=self.market_data_provider,
            logger=self.logger
        )
        
        self.active = False
        try:
            self.prediction_engine = PricePredictor(
                model_dir=self.config.PREDICTION_MODEL_DIR,
                data_dir=self.config.PREDICTION_DATA_DIR
            )
            self.logger.info("PredictionEngine initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize PredictionEngine: {e}", exc_info=True)
            self.prediction_engine = None
        
        self.performance_monitor = PerformanceMonitor() # Initialize performance monitor
        self.performance_monitor.track_portfolio_value(initial_portfolio_value)

        # Initialize the AIAgent
        self.ai_agent = AIAgent(config=self.config)
        self.logger.info("AIAgent initialized within DexBot.")

    async def run(self):
        if not self.strategy:
            self.logger.error("No strategy loaded, DexBot cannot run effectively (AIAgent might lack a key input).")
            # Decide if this is critical enough to stop. For now, it will run but log this.
            # self.active = False 
            # return
            
        self.active = True
        self.logger.info(f"Démarrage du bot avec la stratégie (comme input pour l'agent): {self.strategy.get_name() if self.strategy else 'Aucune'}...")
        # Ensure MarketDataProvider and TradingEngine are used as async context managers
        async with self.market_data_provider, self.trader:
            while self.active:
                try:
                    await self._run_cycle()
                    await asyncio.sleep(self.config.TRADING_UPDATE_INTERVAL_SECONDS)
                except KeyboardInterrupt:
                    self.logger.info("Arrêt manuel du bot détecté.")
                    self.stop()
                except Exception as e:
                    self.logger.error(f"Erreur dans le cycle principal du DexBot: {e}", exc_info=True)
                    # Potentially add a longer sleep here on repeated critical errors
                    await asyncio.sleep(self.config.TRADING_UPDATE_INTERVAL_SECONDS) 

    async def _run_cycle(self):
        current_portfolio_val = self.portfolio_manager.get_total_portfolio_value(self.market_data_provider)
        self.risk_manager.update_portfolio_value(current_portfolio_val)
        self.performance_monitor.track_portfolio_value(current_portfolio_val)
        self.logger.info(f"Valeur actuelle estimée du portefeuille: ${current_portfolio_val:.2f}")

        # --- Inputs Collection for AIAgent ---
        aggregated_inputs: Dict[str, Any] = {
            'market_data': {},
            'predictions': {},
            'strategy_signals': [],
            'risk_assessment': {},
            'security_info': {},
            'portfolio_status': {},
            'current_time': time.time()
        }

        # 1. Portfolio Status
        aggregated_inputs['portfolio_status'] = {
            'available_cash_usd': self.portfolio_manager.get_available_cash(),
            'total_portfolio_value_usd': current_portfolio_val,
            'open_positions': self.portfolio_manager.db.get_active_trades() # Assuming this gives enough detail
        }

        # 2. Risk Assessment (basic example, RiskManager might offer more complex data)
        aggregated_inputs['risk_assessment'] = {
            'max_allowed_risk_per_trade_usd': self.risk_manager.calculate_max_trade_size_usd(current_portfolio_val),
            'current_total_exposure_usd': self.risk_manager.get_current_exposure_usd(), # Requires implementation in RiskManager
            'global_risk_level': self.risk_manager.get_global_risk_level() # Requires implementation
        }
        
        # 3. Market Data & Security Info (Iterate through potential pairs)
        # For now, let's keep fetching pairs like before, and pass this general market view.
        # The AIAgent can then decide if it wants to focus on specific tokens from this list or ask for more data.
        pairs_response = await self.market_data_provider.get_token_pairs_from_dexscreener(
            platform="solana", 
            min_liquidity_usd=self.config.MIN_LIQUIDITY_USD, 
            min_volume_24h_usd=10000, # Example value, can be configured
            sort_by="volume", 
            limit=10 # Reduced limit for agent input processing initially
        )

        if not pairs_response['success'] or not pairs_response['data']:
            self.logger.warning(f"Aucune paire récupérée de DexScreener ou erreur: {pairs_response.get('error', 'Pas de données')}.")
            # Agent might still make decisions based on portfolio or other data, so don't return yet.
            aggregated_inputs['market_data']['dexscreener_pairs'] = []
        else:
            aggregated_inputs['market_data']['dexscreener_pairs'] = pairs_response['data']
            # Perform security check for these pairs and enrich security_info
            # The AIAgent can then use this pre-filtered security information
            for p_data in pairs_response['data']:
                base_token_addr = p_data.get('baseToken', {}).get('address')
                if base_token_addr:
                    is_safe, risks = await self.security_checker.check_token_security(base_token_addr)
                    # Ensure risks are serializable for JSON logging if agent decision is logged in detail
                    serializable_risks = [r.__dict__ for r in risks] if risks else []
                    aggregated_inputs['security_info'][base_token_addr] = {'is_safe': is_safe, 'risks': serializable_risks}

        # 4. Strategy Signals (from the primary loaded strategy)
        # The strategy might need to be adapted to analyze a broader market view or specific tokens
        # identified by the agent, or the agent might interpret raw strategy outputs.
        # For now, let's assume the strategy can still generate some general signals or analyses
        # if given a list of (potentially safe) pairs.
        # This part needs careful thought on how strategies become "signal providers" vs. "deciders".
        if self.strategy and aggregated_inputs['market_data'].get('dexscreener_pairs'):
            # The existing _analyze_and_generate_signals might be too coarse.
            # A strategy might now return a more structured analysis per pair.
            # Let's simulate getting signals for a few top pairs for now.
            # This is a placeholder for how strategy inputs would be generated.
            # The AIAgent's `decide_trade` docstring expects `strategy_signals` to be a list.
            
            # Simplified: Get analysis from strategy for the (safer) pairs.
            # The `analyze` method of BaseStrategy and its children might need to be adapted
            # to return a more generic "analysis output" rather than a direct BUY/SELL signal dict.
            # For now, we'll simulate that the strategy's `analyze` method is called.
            # The `pairs` argument for `analyze` was `List[pd.DataFrame]`.
            # We need to adapt this flow.
            
            # TEMPORARY: We will bypass detailed strategy signal generation for now
            # as it requires refactoring the strategy framework itself.
            # The AI Agent will initially rely more on market data, predictions, risk, security.
            pass # Placeholder - strategy signal integration needs more work aligning with AIAgent needs

        # 5. Predictions (from PredictionEngine)
        if self.prediction_engine and aggregated_inputs['market_data'].get('dexscreener_pairs'):
            self.logger.debug(f"Attempting to get predictions for up to 5 pairs.")
            for p_data in aggregated_inputs['market_data']['dexscreener_pairs'][:5]: # Example: predictions for top 5 pairs
                base_token_addr = p_data.get('baseToken', {}).get('address')
                token_symbol = p_data.get('baseToken', {}).get('symbol', 'N/A')

                if base_token_addr:
                    self.logger.debug(f"Fetching prediction for {token_symbol} ({base_token_addr})")
                    try:
                        # PredictionEngine.predict_price is an async method
                        prediction_result: Optional[PredictionResult] = await self.prediction_engine.predict_price(
                            token_address=base_token_addr, 
                            timeframe="1h" # Default timeframe for now
                        )
                        if prediction_result:
                            self.logger.info(f"Prediction for {token_symbol}: Target ${prediction_result.target_price:.6f}, Dir: {prediction_result.direction}, Conf: {prediction_result.confidence:.2f}")
                            # Store the prediction result object directly, or its __dict__ if preferred by AIAgent
                            aggregated_inputs['predictions'][base_token_addr] = prediction_result.__dict__ 
                        else:
                            self.logger.warning(f"No prediction returned for {token_symbol} ({base_token_addr}).")
                    except Exception as e:
                        self.logger.error(f"Error getting prediction for {token_symbol} ({base_token_addr}): {e}", exc_info=True)
                else:
                    self.logger.debug("Skipping prediction for pair with no base_token_addr.")
        else:
            self.logger.debug("PredictionEngine not available or no pairs to predict for.")
        
        # --- Agent Decision Making ---
        agent_decision = self.ai_agent.decide_trade(aggregated_inputs)
        
        # Log the agent's decision and reasoning
        self.logger.info(f"Decision de l'Agent IA: {agent_decision.get('action')}, Raison: {agent_decision.get('reasoning')}")
        if agent_decision.get('action') not in ['HOLD', None] and agent_decision.get('pair') and agent_decision.get('amount'):
             self.logger.debug(f"Détails de la décision de l'Agent: {json.dumps(agent_decision, indent=2, default=str)}")
        
        # --- Execute Agent's Decision ---
        if agent_decision and agent_decision.get('action') != 'HOLD':
            # Call the new method in TradeExecutor
            self.logger.info(f"Transmission de l'ordre de l'Agent IA à TradeExecutor: {agent_decision.get('action')} {agent_decision.get('pair')}")
            await self.trade_executor.execute_agent_order(agent_decision)
            # The old signal_for_executor mapping and direct call to execute_trade_from_signal is removed.
        else:
            if agent_decision.get('action') == 'HOLD':
                 self.logger.info("Action de l'Agent IA: HOLD. Aucune transaction exécutée.")
            else:
                 self.logger.info("Action de l'Agent IA non exécutable ou non spécifiée. Aucune transaction exécutée.")
        
        # The old logic for _analyze_and_generate_signals and _execute_signals is now replaced by the agent's decision cycle.
        # So, we don't call them anymore.
        # if not valid_pairs: # valid_pairs was from old logic
        #     self.logger.info("Aucune paire valide après vérification de sécurité.")
        #     return
            
        # generated_signals = await self._analyze_and_generate_signals(valid_pairs) # OLD
        
        # if generated_signals: # OLD
        #     await self._execute_signals(generated_signals) # OLD

    async def _security_check(self, pair_data: Dict) -> bool:
        base_token_address = pair_data.get('baseToken', {}).get('address')
        pair_address = pair_data.get('pairAddress')
        token_symbol = pair_data.get('baseToken', {}).get('symbol', 'N/A')

        if not base_token_address or not pair_address:
            self.logger.warning(f"Données de paire incomplètes pour le contrôle de sécurité : {pair_data}")
            return False

        is_safe, risks = await self.security_checker.check_token_security(base_token_address)
        if not is_safe:
            self.logger.warning(f"Token {token_symbol} ({base_token_address}) jugé non sécurisé. Risques: {[r.description for r in risks]}")
            return False
        
        # Additional check: is the pair blacklisted in our DB?
        # This might be redundant if security_checker already handles this concept via its risk sources
        if self.portfolio_manager.db.is_blacklisted(pair_address): # Assuming PortfolioManager has access to DB
            self.logger.warning(f"Paire {pair_address} ({token_symbol}) est sur liste noire.")
            return False
            
        not_blacklisted = not self.config.BLACKLIST_TOKENS.get(base_token_address, False)
        if not not_blacklisted:
            self.logger.warning(f"Token {token_symbol} ({base_token_address}) est sur la liste noire de configuration.")
        
        return is_safe and not_blacklisted

    # Methods _analyze_and_generate_signals and _execute_signals are now removed.

    def stop(self):
        self.active = False
        self.logger.info("Bot arrêté.")

# Example Usage (if you want to run DexBot directly for testing, ensure async context)
# if __name__ == "__main__":
#     async def main():
#         bot = DexBot()
#         try:
#             await bot.run()
#         except KeyboardInterrupt:
#             bot.stop()
#         finally:
#             # Ensure any cleanup for async resources if not handled by __aexit__ in components
#             if bot.market_data_provider.session: # Example cleanup
#                 await bot.market_data_provider.session.close()
#             if bot.trader.client: # Example cleanup for TradingEngine's AsyncClient
#                 await bot.trader.client.close()
#             if bot.trader._api_session: # Example cleanup for TradingEngine's own session
#                 await bot.trader._api_session.close()
                
#     asyncio.run(main())