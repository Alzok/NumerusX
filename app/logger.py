import logging
from config import Config

class DexLogger:
    def __init__(self):
        self.logger = logging.getLogger('NumerusX')
        self.logger.setLevel(Config.LOG_LEVEL)
        
        formatter = logging.Formatter(Config.LOG_FORMAT)
        
        # Fichier
        file_handler = logging.FileHandler('data/trading.log')
        file_handler.setFormatter(formatter)
        
        # Console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)
    
    def log_trade(self, action: str, pair: str, details: dict):
        self.logger.info(f"{action.upper()} | {pair} | {details}")