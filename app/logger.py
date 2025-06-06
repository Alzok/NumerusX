import logging
import json
from logging.handlers import RotatingFileHandler
from app.config import get_config

class DexLogger:
    def __init__(self):
        self.logger = logging.getLogger('DexBot')
        self.logger.setLevel(get_config().LOG_LEVEL)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Configuration du fichier de logs
        file_handler = RotatingFileHandler(
            'data/dex_bot.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # Configuration de la console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_trade(self, action: str, details: dict):
        """Journalisation structurée des trades"""
        log_entry = {
            'action': action,
            'pair': details.get('address', 'unknown'),
            'baseToken': details.get('baseToken', {}).get('symbol', '?'),
            'quoteToken': details.get('quoteToken', {}).get('symbol', '?'),
            'price': details.get('priceUsd', 0)
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_error(self, context: str, error: Exception):
        """Journalisation détaillée des erreurs"""
        self.logger.error(
            f"ERREUR [{context}] - {str(error)}", 
            exc_info=isinstance(error, Exception)
        )
    
    def log_performance(self, metrics: dict):
        """Journalisation des métriques de performance"""
        self.logger.info(f"PERF - {json.dumps(metrics)}")