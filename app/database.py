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
                if 'token_symbol' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN token_symbol TEXT
                    ''')
                if 'trade_id_external' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN trade_id_external TEXT 
                    ''')
                if 'side' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN side TEXT 
                    ''')
                if 'jupiter_quote_response' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN jupiter_quote_response TEXT
                    ''')
                if 'jupiter_transaction_data' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN jupiter_transaction_data TEXT
                    ''')
                if 'slippage_bps' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN slippage_bps INTEGER
                    ''')
                if 'transaction_signature' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN transaction_signature TEXT
                    ''')
                if 'last_valid_block_height' not in columns:
                    self.conn.execute('''
                        ALTER TABLE trades
                        ADD COLUMN last_valid_block_height INTEGER
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
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    token_symbol TEXT, 
                    trade_id_external TEXT, 
                    side TEXT, 
                    jupiter_quote_response TEXT, 
                    jupiter_transaction_data TEXT, 
                    slippage_bps INTEGER,
                    transaction_signature TEXT,
                    last_valid_block_height INTEGER
                );

                CREATE INDEX IF NOT EXISTS idx_trades_protocol ON trades(protocol);
                CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side);
                CREATE INDEX IF NOT EXISTS idx_trades_token_symbol ON trades(token_symbol);
                CREATE INDEX IF NOT EXISTS idx_trades_transaction_signature ON trades(transaction_signature);
            ''')

    def record_trade(self, trade_data: dict):
        try:
            # Input validation
            if not all(k in trade_data for k in ['pair', 'amount']):
                self.logger.error("Missing required keys in trade_data for record_trade (pair, amount).")
                return
            if not isinstance(trade_data['pair'], str) or not trade_data['pair']:
                self.logger.error("Invalid 'pair' in trade_data for record_trade.")
                return
            try:
                amount = float(trade_data['amount'])
                entry_price = float(trade_data.get('entry_price', 0.0))
                slippage_bps = int(trade_data.get('slippage_bps', Config.JUPITER_DEFAULT_SLIPPAGE_BPS if hasattr(Config, 'JUPITER_DEFAULT_SLIPPAGE_BPS') else 50))
                last_valid_block_height_raw = trade_data.get('last_valid_block_height')
                last_valid_block_height = int(last_valid_block_height_raw) if last_valid_block_height_raw is not None else None
            except ValueError:
                self.logger.error("Invalid numerical values for 'amount', 'entry_price', 'slippage_bps', or 'last_valid_block_height' in trade_data.")
                return

            # Handle JSON fields carefully
            jupiter_quote_response_json = json.dumps(trade_data.get('jupiter_quote_response')) if trade_data.get('jupiter_quote_response') else None
            jupiter_transaction_data_json = json.dumps(trade_data.get('jupiter_transaction_data')) if trade_data.get('jupiter_transaction_data') else None

            with self.conn:
                self.conn.execute('''
                    INSERT INTO trades 
                    (pair_address, amount, entry_price, protocol, token_symbol, trade_id_external, side, 
                     jupiter_quote_response, jupiter_transaction_data, slippage_bps, transaction_signature, last_valid_block_height)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data['pair'],
                    amount,
                    entry_price,
                    trade_data.get('protocol', 'Jupiter'),
                    trade_data.get('token_symbol'),
                    trade_data.get('trade_id'),
                    trade_data.get('side'),
                    jupiter_quote_response_json,
                    jupiter_transaction_data_json,
                    slippage_bps,
                    trade_data.get('transaction_signature'),
                    last_valid_block_height
                ))
        except sqlite3.Error as e:
            self.logger.error(f"Erreur enregistrement trade: {str(e)}")

    def get_active_trades(self) -> List[Dict]:
        cursor = self.conn.execute('''
            SELECT id, pair_address, amount, entry_price, protocol, timestamp, token_symbol, trade_id_external, side, 
                   jupiter_quote_response, jupiter_transaction_data, slippage_bps, transaction_signature, last_valid_block_height
            FROM trades WHERE status = 'open'
        ''')
        column_names = [description[0] for description in cursor.description]
        return [dict(zip(column_names, row)) for row in cursor.fetchall()]

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