import time
import logging
from database import DexDatabase
from dex_api import DexAPI
from analytics_engine import AnalyticsEngine
from trading_engine import BananaGunTrader
from telegram_bot import TelegramBot
from config import Config

class DexBot:
    def __init__(self):
        self.db = DexDatabase()
        self.tg_bot = TelegramBot()
        self.analytics = AnalyticsEngine(self.db)
        self.trader = BananaGunTrader()
        
    def run(self):
        self.tg_bot.start_polling()
        while True:
            try:
                pairs = DexAPI.fetch_pairs()
                filtered = self.preprocess_data(pairs)
                signals = self.analytics.generate_signals(filtered)
                self.execute_trades(signals)
                time.sleep(60)
                
            except KeyboardInterrupt:
                self.shutdown()

if __name__ == "__main__":
    DexBot().run()