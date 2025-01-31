import time
from dex_api import DexAPI
from trading_engine import CEXTrader, TradingStrategy
from security import ContractVerifier, SecurityManager
from database import DexDatabase
from logger import DexLogger

class DexBot:
    def __init__(self):
        self.logger = DexLogger()
        self.db = DexDatabase()
        self.trader = CEXTrader()
        self.strategy = TradingStrategy()
        self.verifier = ContractVerifier()
    
    def run(self):
        """Fonction principale d'exécution"""
        self.logger.logger.info("DEX Bot started")
        while True:
            try:
                pairs = DexAPI().get_pairs()
                valid_pairs = self._filter_pairs(pairs)
                signals = self._analyze(valid_pairs)
                self._execute(signals)
                time.sleep(Config.UPDATE_INTERVAL)
            except KeyboardInterrupt:
                break

    def _filter_pairs(self, pairs):
        """Filtrage des paires valides"""
        return [
            p for p in pairs 
            if self.verifier.verify_contract(p['baseToken']['address'])
            and not self.db.is_blacklisted(p['pairAddress'])
        ]
    
    def _analyze(self, pairs):
        """Analyse technique des paires"""
        signals = []
        for pair in pairs:
            data = self.db.get_historical_data(pair['pairAddress'])
            analysis = self.strategy.analyze(pd.DataFrame(data))
            if analysis['volume_spike'].iloc[-1]:
                signals.append(pair)
        return signals
    
    def _execute(self, signals):
        """Exécution des trades"""
        for signal in signals:
            try:
                self.trader.execute_order(
                    symbol=f"{signal['baseToken']['symbol']}/USDT",
                    side='buy',
                    amount=self._calc_position_size()
                )
            except Exception as e:
                self.logger.logger.error(f"Trade failed: {str(e)}")