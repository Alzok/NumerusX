from .dex_api import DexAPI
from .trading_engine import SolanaTradingEnginePro
from .security import EnhancedSecurity
from .analytics_engine import AdvancedTradingStrategy
from .logger import DexLogger
from .database import EnhancedDatabase
import time
from config import Config

class PortfolioManager:
    def __init__(self):
        self.db = EnhancedDatabase()
        self.current_balance = Config.INITIAL_BALANCE

    def get_available_funds(self):
        """Calcule les fonds disponibles en temps réel"""
        committed = sum(t['amount'] for t in self.db.get_active_trades())
        return max(0, self.current_balance - committed)

    def update_exposure(self, pair, amount):
        """Met à jour l'exposition au risque"""
        self.db.record_trade({
            'pair': pair['address'],
            'amount': amount,
            'timestamp': time.time()
        })
        self.current_balance -= amount

class RiskEngine:
    def __init__(self):
        self.db = EnhancedDatabase()

    def check_liquidity(self, pair):
        """Vérifie la liquidité selon plusieurs critères"""
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        if liquidity < Config.MIN_LIQUIDITY:
            return False
            
        history = self.db.get_token_history(pair['baseToken']['address'])
        if history.get('liquidity_change_24h', 0) < -0.3:
            return False
            
        return True

class DexBotPro:
    def __init__(self):
        self.dex_api = DexAPI()
        self.trader = SolanaTradingEnginePro()
        self.security = EnhancedSecurity(EnhancedDatabase())
        self.strategy = AdvancedTradingStrategy()
        self.logger = DexLogger()
        self.portfolio = PortfolioManager()
        self.risk_engine = RiskEngine()
        self.active = True

    def run(self):
        """Boucle principale de trading"""
        self.logger.logger.info("Démarrage du bot en mode PRO")
        while self.active:
            try:
                pairs = self.dex_api.get_solana_pairs()
                valid_pairs = self._filter_pairs(pairs)
                signals = self._analyze_pairs(valid_pairs)
                self._execute_signals(signals)
                time.sleep(Config.UPDATE_INTERVAL)
            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                self.logger.log_error('main_loop', e)

    def _filter_pairs(self, pairs):
        return [p for p in pairs if self._deep_security_check(p)]

    def _deep_security_check(self, pair):
        checks = [
            self.security.verify_token(pair['baseToken']['address'])[0],
            self.risk_engine.check_liquidity(pair),
            not self.portfolio.db.is_blacklisted(pair['baseToken']['address'])
        ]
        return all(checks)

    def _analyze_pairs(self, pairs):
        scored = []
        for p in pairs:
            data = self.dex_api.get_historical_data(p['address'])
            score = self.strategy.calculate_score(data)
            if score >= Config.TRADE_THRESHOLD:
                scored.append((p, score))
        return sorted(scored, key=lambda x: x[1], reverse=True)

    def _execute_signals(self, signals):
        budget = self.portfolio.get_available_funds()
        for signal in signals[:Config.MAX_POSITIONS]:
            try:
                amount = min(budget * 0.1, Config.MAX_ORDER_SIZE)
                self.trader.execute_swap(
                    Config.BASE_ASSET,
                    signal[0]['baseToken']['address'],
                    amount
                )
                self.portfolio.update_exposure(signal[0], amount)
                self.logger.log_trade('buy', signal[0])
                budget -= amount
            except Exception as e:
                self.logger.log_error('execution', e)

    def stop(self):
        self.active = False
        self.logger.logger.info("Arrêt propre du bot")