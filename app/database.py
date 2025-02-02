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
            # Migration sécurisée pour ajouter 'protocol'
            cursor = self.conn.execute("PRAGMA table_info(trades)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'protocol' not in columns:
                self.conn.execute('''
                    ALTER TABLE trades 
                    ADD COLUMN protocol TEXT DEFAULT 'unknown'
                ''')

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
                    protocol TEXT,
                    status TEXT DEFAULT 'open',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_trades_protocol ON trades(protocol);
            ''')

    def record_trade(self, trade_data: dict):
        try:
            self.conn.execute('''
                INSERT INTO trades 
                (pair_address, amount, entry_price, protocol)
                VALUES (?, ?, ?, ?)
            ''', (
                trade_data['pair'],
                trade_data['amount'],
                trade_data.get('entry_price', 0.0),
                trade_data.get('protocol', 'unknown')
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Erreur enregistrement trade: {str(e)}")

    def get_active_trades(self) -> List[Dict]:
        cursor = self.conn.execute('''
            SELECT id, pair_address, amount, entry_price, protocol, timestamp 
            FROM trades WHERE status = 'open'
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def is_blacklisted(self, address: str) -> bool:
        cursor = self.conn.execute(
            'SELECT 1 FROM blacklist WHERE address = ?', 
            (address,)
        )
        return cursor.fetchone() is not None

    def add_blacklist(self, address: str, reason: str, metadata: dict):
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO blacklist 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (address, reason, json.dumps(metadata)))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass