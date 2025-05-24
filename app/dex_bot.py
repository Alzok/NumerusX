import asyncio # Added for async sleep and operations
from app.market.market_data import MarketDataProvider # Changed import
from app.trading.trading_engine import TradingEngine # Assuming this is the correct name now
from app.security.security import SecurityChecker # Assuming this is the correct name now
from app.strategy_framework import BaseStrategy
from app.strategy_selector import StrategySelector # Import StrategySelector
from app.logger import DexLogger # Assuming a logger class
from app.database import EnhancedDatabase
import time
from typing import List, Dict, Optional
from app.config import Config
from app.prediction_engine import PricePredictor, PredictionResult # Import necessary classes
from app.risk_manager import RiskManager, Position # Import RiskManager and Position
from app.portfolio_manager import PortfolioManager # Import new PortfolioManager
from app.trade_executor import TradeExecutor # Import TradeExecutor
import pandas as pd

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

    def record_trade_executed(self, pair_address: str, amount_usd: float, entry_price: float, protocol: str, token_symbol: str, trade_id: Optional[str]=None):
        self.db.record_trade({
            'pair': pair_address,
            'amount': amount_usd, # Assuming this is the USD value invested
            'entry_price': entry_price,
            'protocol': protocol,
            # 'token_symbol': token_symbol, # DB schema might need update for this
            # 'trade_id': trade_id # DB schema might need update for this
        })
        self.current_cash_balance -= amount_usd # Reduce cash by amount invested
        # Note: Portfolio value actually changes based on P&L, not just cash reduction.

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
        
        self.trade_executor = TradeExecutor( # Initialize TradeExecutor
            trading_engine=self.trader,
            portfolio_manager=self.portfolio_manager,
            risk_manager=self.risk_manager,
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

    async def run(self):
        if not self.strategy:
            self.logger.error("No strategy loaded, DexBot cannot run. Please check configuration.")
            self.active = False
            return
            
        self.active = True
        self.logger.info(f"Démarrage du bot avec la stratégie: {self.strategy.get_name()}...")
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

        pairs_response = await self.market_data_provider.get_token_pairs_from_dexscreener(
            platform="solana", 
            min_liquidity_usd=self.config.MIN_LIQUIDITY_USD, 
            min_volume_24h_usd=10000, # Example value, can be configured
            sort_by="volume", 
            limit=50 # Example value
        )
        if not pairs_response['success'] or not pairs_response['data']:
            self.logger.warning(f"Aucune paire récupérée ou erreur: {pairs_response.get('error', 'Pas de données')}, cycle de trading sauté.")
            return
        
        pairs = pairs_response['data']
        valid_pairs = []
        for p_data in pairs:
            if await self._security_check(p_data):
                valid_pairs.append(p_data)
        
        if not valid_pairs:
            self.logger.info("Aucune paire valide après vérification de sécurité.")
            return
            
        generated_signals = await self._analyze_and_generate_signals(valid_pairs)
        
        if generated_signals:
            await self._execute_signals(generated_signals)

    async def _security_check(self, pair_data: Dict) -> bool:
        base_token_address = pair_data.get('baseToken', {}).get('address')
        pair_address = pair_data.get('pairAddress')

        if not base_token_address or not pair_address:
            self.logger.warning(f"Adresse du token de base ou de la paire manquante: {pair_data.get('baseToken', {}).get('symbol', pair_address)}")
            return False

        is_safe, risks = await self.security_checker.check_token_security(base_token_address)
        not_blacklisted = not self.portfolio_manager.db.is_blacklisted(pair_address)
        
        if not is_safe:
             self.logger.info(f"Token {base_token_address} (paire {pair_address}) non sûr. Risques: {[r.description for r in risks] if risks else 'N/A'}")
        if not not_blacklisted:
             self.logger.info(f"Paire {pair_address} blacklistée.")

        return is_safe and not_blacklisted

    async def _analyze_and_generate_signals(self, pairs: List[Dict]) -> List[Dict]:
        """Analyzes pairs using the current strategy and generates signals, applying prediction if available."""
        if not self.strategy: # Should be caught by run() but defensive check
            self.logger.error("No strategy available for analysis.")
            return []
            
        all_signals = [] 

        for p_data in pairs:
            pair_address = p_data.get('pairAddress')
            base_token_address = p_data.get('baseToken', {}).get('address')
            token_symbol = p_data.get('baseToken', {}).get('symbol', 'N/A')

            if not pair_address or not base_token_address:
                self.logger.warning(f"Données de paire incomplètes pour {token_symbol if token_symbol != 'N/A' else pair_address}")
                continue

            try:
                historical_data_response = await self.market_data_provider.get_historical_prices(
                    token_address=base_token_address, 
                    timeframe="1h", 
                    limit=100 
                )
                if not historical_data_response['success'] or not historical_data_response['data']:
                    self.logger.warning(f"Pas de données historiques pour {token_symbol} ({base_token_address}) ou erreur: {historical_data_response.get('error')}")
                    continue
                
                try:
                    historical_data_df = pd.DataFrame(historical_data_response['data'])
                    if historical_data_df.empty:
                        self.logger.warning(f"DataFrame historique vide pour {token_symbol} ({base_token_address})")
                        continue
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col in historical_data_df.columns:
                            historical_data_df[col] = pd.to_numeric(historical_data_df[col], errors='coerce')
                except Exception as df_e:
                    self.logger.error(f"Erreur de création/préparation du DataFrame pour {token_symbol} ({base_token_address}): {df_e}")
                    continue
                                
                analysis_result = self.strategy.analyze(historical_data_df, current_pair_metrics=p_data)
                if 'error' in analysis_result:
                    self.logger.warning(f"Erreur d'analyse de la stratégie {self.strategy.get_name()} pour {token_symbol}: {analysis_result['error']}")
                    continue

                signal_info = self.strategy.generate_signal(analysis_result) 
                current_signal_type = signal_info.get('signal', 'hold')
                current_confidence = signal_info.get('confidence', 0.0)

                if self.prediction_engine and current_signal_type in ['buy', 'sell']:
                    self.logger.info(f"Tentative de prédiction pour {token_symbol} ({base_token_address}). Signal Stratégie: {current_signal_type}, Conf: {current_confidence:.2f}")
                    try:
                        prediction_result: Optional[PredictionResult] = await self.prediction_engine.predict_price(
                            token_address=base_token_address, 
                            timeframe="1h"
                        )
                        if prediction_result and prediction_result.confidence > 0.1: 
                            self.logger.info(f"Prédiction pour {token_symbol}: Dir={prediction_result.direction}, Conf={prediction_result.confidence:.2f}")
                            if (current_signal_type == 'buy' and prediction_result.direction == 'up') or \
                               (current_signal_type == 'sell' and prediction_result.direction == 'down'):
                                current_confidence = (current_confidence + prediction_result.confidence) / 2 
                                current_confidence = min(current_confidence * 1.2, 0.99) 
                            elif (current_signal_type == 'buy' and prediction_result.direction == 'down') or \
                                 (current_signal_type == 'sell' and prediction_result.direction == 'up'):
                                current_confidence = current_confidence * (1 - prediction_result.confidence * 0.75) 
                            else: 
                                current_confidence *= 0.9 
                            signal_info['confidence'] = max(0.01, current_confidence) 
                            self.logger.info(f"Confiance ajustée après prédiction pour {token_symbol}: {signal_info['confidence']:.2f}")
                        else:
                            self.logger.warning(f"Pas de résultat de prédiction ou faible confiance pour {token_symbol} ({base_token_address}). Utilisation de la confiance de la stratégie.")
                    except Exception as pred_e:
                        self.logger.error(f"Erreur du moteur de prédiction pour {token_symbol} ({base_token_address}): {pred_e}", exc_info=True)
                
                if current_signal_type in ['buy', 'sell'] and signal_info.get('confidence', 0.0) > self.config.TRADE_CONFIDENCE_THRESHOLD:
                    all_signals.append({'pair_data': p_data, 'signal_info': signal_info})
                elif current_signal_type != 'hold': 
                    self.logger.info(f"Signal {current_signal_type} pour {token_symbol} ignoré (confiance {signal_info.get('confidence', 0.0):.2f} <= seuil {self.config.TRADE_CONFIDENCE_THRESHOLD})")

            except Exception as e:
                self.logger.error(f"Erreur d'analyse/signal pour {token_symbol} ({pair_address}): {e}", exc_info=True)
                continue
        
        return sorted(all_signals, key=lambda x: x['signal_info'].get('confidence', 0.0), reverse=True)

    async def _execute_signals(self, signals_to_execute: List[Dict]):
        """ Iterates through sorted signals and calls TradeExecutor for each. """
        self.logger.info(f"Exécution des signaux: {len(signals_to_execute)} signaux reçus.")
        executed_trades_count = 0

        current_portfolio_val = self.portfolio_manager.get_total_portfolio_value(self.market_data_provider)
        self.risk_manager.update_portfolio_value(current_portfolio_val)

        for signal_package in signals_to_execute:
            pair_data = signal_package['pair_data']
            signal_info = signal_package['signal_info']
            token_symbol = pair_data.get('baseToken', {}).get('symbol', 'N/A')

            if executed_trades_count >= self.config.MAX_OPEN_POSITIONS:
                self.logger.info(f"Limite MAX_OPEN_POSITIONS ({self.config.MAX_OPEN_POSITIONS}) atteinte. Plus de trades pour ce cycle.")
                break
            
            self.logger.info(f"Traitement du signal {signal_info.get('signal')} pour {token_symbol} (paire {pair_data.get('pairAddress')}) avec confiance {signal_info.get('confidence'):.2f}")
            
            success = await self.trade_executor.execute_trade_signal(pair_data, signal_info)
            if success:
                executed_trades_count += 1
                self.performance_monitor.track_trade(pnl=0, success=True) 
            else:
                self.performance_monitor.track_trade(pnl=0, success=False)
            
    def stop(self):
        self.active = False
        self.logger.info("Arrêt du bot demandé...")
        self.logger.info("Bot arrêté.")