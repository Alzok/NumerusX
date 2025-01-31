import time
from database import DexDatabase
from dex_api import DexAPI
from analytics_engine import PatternEngine, VerificationHub
from trading_engine import BananaGunTrader
from telegram_bot import TelegramInterface

class DexBot:
    def __init__(self):
        self.db = DexDatabase()
        self.tg = TelegramInterface()
        self.verifier = VerificationHub()
        self.trader = BananaGunTrader()
    
    def run(self):
        self.tg.start()
        while True:
            pairs = DexAPI().get_pair_data()
            valid_pairs = [p for p in pairs if self.verifier.full_verification(p['address'])]
            
            for pair in valid_pairs:
                if PatternEngine().detect_pump(pair):
                    self.trader.execute_trade(pair, 'BUY')
                    self.tg.alert(f"New BUY: {pair['baseToken']['symbol']}")
            
            time.sleep(60)

if __name__ == "__main__":
    DexBot().run()