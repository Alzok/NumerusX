import sqlite3
import json
import os
from app.config import Config
import logging
from typing import List, Dict

class EnhancedDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH)
        self.logger = logging.getLogger('Database')
        self._init_db()

    def _init_db(self):
        # Ensure the database directory exists
        db_dir = os.path.dirname(Config.DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        with self.conn:
            # Check if the trades table exists first
            cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Migration for existing table
                cursor = self.conn.execute("PRAGMA table_info(trades)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'protocol' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades 
                        ADD COLUMN protocol TEXT DEFAULT 'unknown'
                    ''')
            
            # Create tables if they don't exist
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
                    protocol TEXT DEFAULT 'unknown',
                    status TEXT DEFAULT 'open',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_trades_protocol ON trades(protocol);
            ''')

    def record_trade(self, trade_data: dict):
        try:
            # Input validation
            if not all(k in trade_data for k in ['pair', 'amount']):
                self.logger.error("Missing required keys in trade_data for record_trade.")
                return
            if not isinstance(trade_data['pair'], str) or not trade_data['pair']:
                self.logger.error("Invalid 'pair' in trade_data for record_trade.")
                return
            try:
                amount = float(trade_data['amount'])
                entry_price = float(trade_data.get('entry_price', 0.0))
            except ValueError:
                self.logger.error("Invalid numerical values for 'amount' or 'entry_price' in trade_data.")
                return

            with self.conn:
                self.conn.execute('''
                    INSERT INTO trades 
                    (pair_address, amount, entry_price, protocol)
                    VALUES (?, ?, ?, ?)
                ''', (
                    trade_data['pair'],
                    amount,
                    entry_price,
                    trade_data.get('protocol', 'unknown')
                ))
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
            # Input validation
            if not isinstance(address, str) or not address:
                self.logger.error("Invalid 'address' for add_blacklist.")
                return
            if not isinstance(reason, str) or not reason:
                self.logger.error("Invalid 'reason' for add_blacklist.")
                return
            if not isinstance(metadata, dict):
                self.logger.error("Invalid 'metadata' for add_blacklist, must be a dict.")
                return

            with self.conn:
                self.conn.execute('''
                    INSERT OR REPLACE INTO blacklist 
                    (address, reason, metadata, timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (address, reason, json.dumps(metadata)))
        except sqlite3.IntegrityError:
            # This can happen if two threads try to add the same address at the exact same time,
            # even with INSERT OR REPLACE. Or other integrity issues.
            self.logger.warning(f"IntegrityError while adding to blacklist, likely a concurrent write or invalid data: {address}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error while adding to blacklist {address}: {e}")