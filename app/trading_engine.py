import ccxt
import logging
from config import Config

class CEXTrader:
    def __init__(self, exchange='binance'):
        self.exchange = getattr(ccxt, exchange)({
            'apiKey': os.getenv("CEX_API_KEY"),
            'secret': os.getenv("CEX_API_SECRET"),
            'enableRateLimit': True
        })
    
    def execute_order(self, symbol: str, side: str, amount: float):
        try:
            return self.exchange.create_market_order(symbol, side, amount)
        except ccxt.InsufficientFunds as e:
            logging.error(f"Funds insuffisants: {str(e)}")
            raise