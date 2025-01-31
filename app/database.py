import sqlite3
import json
from config import Config
import logging

class EnhancedDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH)
        self.logger = logging.getLogger('Database')
        self._init_db()

    def _init_db(self):
        with self.conn:
            try:
                self.conn.executescript('''
                    CREATE TABLE IF NOT EXISTS blacklist (
                        address TEXT PRIMARY KEY,
                        reason TEXT,
                        metadata TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_bl_timestamp ON blacklist(timestamp);
                    
                    CREATE TABLE IF NOT EXISTS token_metrics (
                        address TEXT,
                        timestamp DATETIME,
                        price REAL,
                        liquidity REAL,
                        volume REAL,
                        PRIMARY KEY (address, timestamp)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_tm_address ON token_metrics(address);
                    
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair_address TEXT,
                        amount REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT
                    );
                ''')
            except sqlite3.Error as e:
                self.logger.error(f"Erreur d'initialisation DB: {str(e)}")

    def add_blacklist(self, address: str, reason: str, metadata: dict):
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO blacklist 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (address, reason, json.dumps(metadata)))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def is_blacklisted(self, address: str) -> bool:
        cursor = self.conn.execute(
            'SELECT 1 FROM blacklist WHERE address = ?', 
            (address,)
        )
        return cursor.fetchone() is not None

    def record_trade(self, trade_data: dict):
        try:
            self.conn.execute('''
                INSERT INTO trades (pair_address, amount, status)
                VALUES (?, ?, ?)
            ''', (trade_data['pair'], trade_data['amount'], 'open'))
            self.conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Erreur d'enregistrement trade: {str(e)}")

    def get_active_trades(self):
        return self.conn.execute(
            'SELECT * FROM trades WHERE status = "open"'
        ).fetchall()