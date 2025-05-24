import asyncio # Added for async sleep and operations
from app.market.market_data import MarketDataProvider # Changed import
from app.trading_engine import SolanaTradingEnginePro
from app.security.security import EnhancedSecurity
from app.analytics_engine import AdvancedTradingStrategy
from app.logger import DexLogger
from app.database import EnhancedDatabase
import time
from typing import List, Dict
from app.config import Config

class PortfolioManager:
    def __init__(self):
        self.db = EnhancedDatabase()
        self.current_balance = Config.INITIAL_PORTFOLIO_BALANCE_USD

    def get_available_funds(self) -> float:
        return max(0, self.current_balance - sum(t['amount'] for t in self.db.get_active_trades()))

    def update_exposure(self, pair: Dict, amount: float, protocol: str):
        self.db.record_trade({
            'pair': pair['address'],
            'amount': amount,
            'entry_price': pair.get('priceUsd', pair.get('price', 0.0)),
            'protocol': protocol
        })
        self.current_balance -= amount

class RiskEngine:
    def __init__(self):
        self.max_exposure = 20  # %
        self.auto_stop_loss = True

    def check_liquidity(self, pair: Dict) -> bool:
        liquidity = pair.get('liquidity', {}).get('usd') or pair.get('liquidity')
        return liquidity > Config.MIN_LIQUIDITY_USD

class DexBot:
    def __init__(self):
        self.market_data_provider = MarketDataProvider() # Added MarketDataProvider
        self.trader = SolanaTradingEnginePro()
        self.security = EnhancedSecurity(db_path=Config.DB_PATH)
        self.strategy = AdvancedTradingStrategy()
        self.logger = DexLogger()
        self.portfolio = PortfolioManager()
        self.risk_engine = RiskEngine()
        self.active = False
        self.prediction_engine = None  # Initialized later if available

    async def run(self): # Changed to async
        self.active = True
        self.logger.logger.info("Démarrage du bot...")
        async with self.market_data_provider: # Use async context manager for MDP
            while self.active:
                try:
                    await self._run_cycle() # Changed to await
                    await asyncio.sleep(Config.TRADING_UPDATE_INTERVAL_SECONDS) # Use asyncio.sleep
                except KeyboardInterrupt:
                    self.stop()
                except Exception as e: # Catch other exceptions in the loop
                    self.logger.logger.error(f"Erreur dans le cycle principal du DexBot: {e}", exc_info=True)
                    await asyncio.sleep(Config.TRADING_UPDATE_INTERVAL_SECONDS) # Wait before retrying

    async def _run_cycle(self): # Changed to async
        pairs = await self.market_data_provider.get_token_pairs(chain="solana")
        if not pairs:
            self.logger.logger.warning("Aucune paire récupérée, cycle de trading sauté.")
            return

        valid_pairs = []
        for p in pairs:
            if self._security_check(p): # Security check first
                valid_pairs.append(p)
        
        if not valid_pairs:
            self.logger.logger.info("Aucune paire valide après vérification de sécurité.")
            return
            
        signals = await self._analyze_pairs(valid_pairs)
        if signals:
            await self._execute_signals(signals) # Ensure _execute_signals is async

    def _security_check(self, pair: Dict) -> bool:
        base_token_address = pair.get('baseToken', {}).get('address')
        if not base_token_address:
            self.logger.logger.warning(f"Adresse du token de base manquante pour la paire: {pair.get('pairAddress')}")
            return False

        is_safe, reason = self.security.verify_token(base_token_address) 
        
        liquidity_ok = self.risk_engine.check_liquidity(pair)
        pair_address_to_check = pair.get('pairAddress')
        if not pair_address_to_check:
            self.logger.logger.warning(f"Pair address missing for blacklist check: {pair}")
            return False

        not_blacklisted = not self.portfolio.db.is_blacklisted(pair_address_to_check)
        
        if not is_safe:
             self.logger.logger.info(f"Token {base_token_address} non sûr: {reason}")
        if not liquidity_ok:
             self.logger.logger.info(f"Liquidité insuffisante pour la paire {pair_address_to_check}")
        if not not_blacklisted:
             self.logger.logger.info(f"Paire {pair_address_to_check} blacklistée")

        return all([
            is_safe,
            liquidity_ok,
            not_blacklisted
        ])

    async def _analyze_pairs(self, pairs: List[Dict]) -> List[tuple]:
        analyzed = []
        for p in pairs:
            pair_address = p.get('pairAddress')
            base_token_address = p.get('baseToken', {}).get('address')

            if not pair_address or not base_token_address:
                self.logger.logger.warning(f"Informations de paire incomplètes pour l'analyse: {p}")
                continue

            try:
                historical_data_list = await self.market_data_provider.get_historical_prices(
                    token_address=base_token_address,
                    timeframe="1h", 
                    limit=48
                )
                if not historical_data_list:
                    self.logger.logger.warning(f"Aucune donnée historique pour {pair_address} ({base_token_address})")
                    continue
                
                analysis_input = historical_data_list 
                
                current_pair_metrics = p
                analysis = self.strategy.analyze(historical_data_list, current_pair_metrics=current_pair_metrics)

            except Exception as e:
                self.logger.logger.error(f"Erreur d'obtention/analyse des données pour {pair_address}: {e}", exc_info=True)
                continue
            
            if self.strategy.generate_signal(analysis) == 'buy':
                analyzed.append((p, analysis['momentum']))
                
        return sorted(analyzed, key=lambda x: x[1], reverse=True)

    async def _execute_signals(self, signals: List[tuple]): # Changed to async
        for pair, score in signals[:Config.MAX_OPEN_POSITIONS]:
            try:
                if hasattr(self, 'risk_manager') and self.risk_manager:
                    max_amount = self.risk_manager.calculate_position_size(
                        token_address=pair.get('address'),
                        token_symbol=pair.get('symbol', 'UNKNOWN'),
                        entry_price=pair.get('priceUsd', 0.0)
                    )
                    amount = min(max_amount, Config.MAX_ORDER_SIZE_USD)
                else:
                    amount = min(self.portfolio.get_available_funds() * 0.1, Config.MAX_ORDER_SIZE_USD)
                
                protocol = pair.get('dexId', 'jupiter')
                result = await self.trader.execute_swap(
                    Config.BASE_ASSET,
                    pair.get('baseToken', {}).get('address') or pair.get('mint'),
                    amount
                )
                
                if result.get('success', False):
                    self.portfolio.update_exposure(pair, amount, protocol)
                else:
                    self.logger.log_error('trade_execution', Exception(result.get('error', 'Unknown error')))
                
            except Exception as e:
                self.logger.log_error('trade_execution', e)

    def stop(self):
        self.active = False
        self.logger.logger.info("Arrêt du bot...")

class PerformanceMonitor:
    def __init__(self):
        self.history = []
    
    def track(self, metric: str, value: float):
        self.history.append({
            'timestamp': time.time(),
            'metric': metric,
            'value': value
        })
    
    @property
    def daily_pnl(self) -> float:
        return sum(t['value'] for t in self.history if t['metric'] == 'trade') / Config.INITIAL_PORTFOLIO_BALANCE_USD * 100