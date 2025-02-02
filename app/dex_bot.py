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
        return liquidity > Config.MIN_LIQUIDITY

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

    def run(self):
        self.active = True
        self.logger.logger.info("Démarrage du bot...")
        while self.active:
            try:
                self._run_cycle()
                time.sleep(Config.UPDATE_INTERVAL)
            except KeyboardInterrupt:
                self.stop()

    def _run_cycle(self):
        pairs = self.dex_api.get_solana_pairs()
        valid_pairs = [p for p in pairs if self._security_check(p)]
        signals = self._analyze_pairs(valid_pairs)
        self._execute_signals(signals)

    def _security_check(self, pair: Dict) -> bool:
        base_token = pair.get('baseToken', {}).get('address') or pair.get('mint')
        return all([
            self.security.verify_token(base_token)[0],
            self.risk_engine.check_liquidity(pair),
            not self.portfolio.db.is_blacklisted(pair['address'])
        ])

    def _analyze_pairs(self, pairs: List[Dict]) -> List[tuple]:
        analyzed = []
        for p in pairs:
            data = self.dex_api.get_historical_data(p['address'])
            analysis = self.strategy.analyze(data)
            if self.strategy.generate_signal(analysis) == 'buy':
                analyzed.append((p, analysis['momentum']))
        return sorted(analyzed, key=lambda x: x[1], reverse=True)

    def _execute_signals(self, signals: List[tuple]):
        for pair, score in signals[:Config.MAX_POSITIONS]:
            try:
                amount = min(self.portfolio.get_available_funds() * 0.1, Config.MAX_ORDER_SIZE)
                
                # Détection du protocole
                protocol = 'jupiter' if 'route' in pair else 'raydium'
                self.trader.execute_swap(
                    Config.BASE_ASSET,
                    pair.get('baseToken', {}).get('address') or pair['mint'],
                    amount
                )
                self.portfolio.update_exposure(pair, amount, protocol)
                
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
        return sum(t['value'] for t in self.history if t['metric'] == 'trade') / Config.INITIAL_BALANCE * 100