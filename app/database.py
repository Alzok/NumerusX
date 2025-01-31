import sqlite3
import json
from config import Config
import logging
from typing import List, Dict

class EnhancedDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH)
        self.logger = logging.getLogger('Database')
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    address TEXT PRIMARY KEY,
                    reason TEXT,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pair_address TEXT,
                    amount REAL,
                    entry_price REAL,
                    status TEXT DEFAULT 'open',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX idx_trades_status ON trades(status);
            ''')

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
                INSERT INTO trades (pair_address, amount, entry_price)
                VALUES (?, ?, ?)
            ''', (
                trade_data['pair'],
                trade_data['amount'],
                trade_data['entry_price']
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Erreur d'enregistrement: {str(e)}")

    def get_active_trades(self) -> List[Dict]:
        cursor = self.conn.execute('''
            SELECT 
                id,
                pair_address,
                amount,
                entry_price,
                timestamp 
            FROM trades 
            WHERE status = 'open'
        ''')
        return [dict(row) for row in cursor.fetchall()]

    @property
    def blacklist_count(self) -> int:
        return self.conn.execute('SELECT COUNT(*) FROM blacklist').fetchone()[0]