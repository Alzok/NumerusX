import sqlite3
import logging
from config import Config, BLACKLIST_REASON

class DexDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('data/dex_data.db')
        self._init_db()
    
    def _init_db(self):
        with self.conn:
            self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS tokens (
                    address TEXT PRIMARY KEY,
                    symbol TEXT,
                    last_price REAL,
                    liquidity REAL
                );
                
                CREATE TABLE IF NOT EXISTS blacklist (
                    address TEXT PRIMARY KEY,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')

    def add_to_blacklist(self, address: str, reason: BLACKLIST_REASON):
        self.conn.execute('''
            INSERT OR REPLACE INTO blacklist 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (address, reason.value))