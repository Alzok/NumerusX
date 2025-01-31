from .dex_api import DexAPI
from .trading_engine import SolanaTradingEnginePro
from .security import EnhancedSecurity
from .analytics_engine import AdvancedTradingStrategy
from .logger import DexLogger
from .database import EnhancedDatabase
import time
from typing import List, Dict
from config import Config

class PortfolioManager:
    def __init__(self):
        self.db = EnhancedDatabase()
        self.current_balance = Config.INITIAL_BALANCE

    def get_available_funds(self) -> float:
        return max(0, self.current_balance - sum(t['amount'] for t in self.db.get_active_trades()))

    def update_exposure(self, pair: Dict, amount: float):
        self.db.record_trade({
            'pair': pair['address'],
            'amount': amount,
            'entry_price': pair['priceUsd']
        })
        self.current_balance -= amount

class RiskEngine:
    def __init__(self):
        self.max_exposure = 20  # %
        self.auto_stop_loss = True
        self.current_risk = 0

    def check_liquidity(self, pair: Dict) -> bool:
        return pair['liquidity']['usd'] > Config.MIN_LIQUIDITY

class DexBot:
    def __init__(self):
        self.dex_api = DexAPI()
        self.trader = SolanaTradingEnginePro()
        self.security = EnhancedSecurity(EnhancedDatabase())
        self.strategy = AdvancedTradingStrategy()
        self.logger = DexLogger()
        self.portfolio = PortfolioManager()
        self.risk_engine = RiskEngine()
        self.active = False
        self.speed = 3
        self.performance = PerformanceMonitor()

    @property
    def active_trades(self) -> List[Dict]:
        return self.db.get_active_trades()

    def run(self):
        self.active = True
        self.logger.logger.info("Démarrage du bot")
        while self.active:
            try:
                self._run_cycle()
                time.sleep(Config.UPDATE_INTERVAL / self.speed)
            except KeyboardInterrupt:
                self.stop()

    def _run_cycle(self):
        pairs = self.dex_api.get_solana_pairs()
        valid_pairs = [p for p in pairs if self._security_check(p)]
        signals = self._analyze_pairs(valid_pairs)
        self._execute_signals(signals)

    def _security_check(self, pair: Dict) -> bool:
        return all([
            self.security.verify_token(pair['baseToken']['address'])[0],
            self.risk_engine.check_liquidity(pair),
            not self.portfolio.db.is_blacklisted(pair['address'])
        ])

    def _analyze_pairs(self, pairs: List[Dict]) -> List[Dict]:
        return [
            p for p in pairs
            if self.strategy.generate_signal(
                self.strategy.analyze(
                    self.dex_api.get_historical_data(p['address'])
                )
            ) == 'buy'
        ]

    def _execute_signals(self, signals: List[Dict]):
        for signal in signals[:Config.MAX_POSITIONS]:
            try:
                amount = min(
                    self.portfolio.get_available_funds() * 0.1,
                    Config.MAX_ORDER_SIZE
                )
                self.trader.execute_swap(
                    Config.BASE_ASSET,
                    signal['baseToken']['address'],
                    amount
                )
                self.portfolio.update_exposure(signal, amount)
                self.performance.track('trade', amount)
            except Exception as e:
                self.logger.log_error('execution', e)

    def stop(self):
        self.active = False
        self.logger.logger.info("Arrêt du bot")

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
        return sum(t['value'] for t in self.history if t['metric'] == 'trade') / Config.INITIAL_BALANCE * 100