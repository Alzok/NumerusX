import sqlite3
import logging
from config import Config

class DexDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_NAME)
        self._init_db()
    
    def _init_db(self):
        with self.conn:
            # Tables initialisées via schema.sql
            pass
            
    def store_data(self, data):
        # Implémentation existante
        pass

    def load_blacklists(self):
        # Chargement des blacklists
        pass