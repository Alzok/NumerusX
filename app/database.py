import sqlite3
import json
import os
from app.config import Config
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class EnhancedDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        self.logger = logging.getLogger('Database')
        self._init_db()

    def _init_db(self):
        # Ensure the database directory exists
        db_dir = os.path.dirname(self.db_path)
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
                
                # Add missing columns to trades table
                migrations = [
                    ('protocol', 'ALTER TABLE trades ADD COLUMN protocol TEXT DEFAULT "unknown"'),
                    ('token_symbol', 'ALTER TABLE trades ADD COLUMN token_symbol TEXT'),
                    ('trade_id_external', 'ALTER TABLE trades ADD COLUMN trade_id_external TEXT'),
                    ('side', 'ALTER TABLE trades ADD COLUMN side TEXT'),
                    ('jupiter_quote_response', 'ALTER TABLE trades ADD COLUMN jupiter_quote_response TEXT'),
                    ('jupiter_transaction_data', 'ALTER TABLE trades ADD COLUMN jupiter_transaction_data TEXT'),
                    ('slippage_bps', 'ALTER TABLE trades ADD COLUMN slippage_bps INTEGER'),
                    ('transaction_signature', 'ALTER TABLE trades ADD COLUMN transaction_signature TEXT'),
                    ('last_valid_block_height', 'ALTER TABLE trades ADD COLUMN last_valid_block_height INTEGER'),
                    ('ai_decision_id', 'ALTER TABLE trades ADD COLUMN ai_decision_id TEXT'),
                    ('execution_time_ms', 'ALTER TABLE trades ADD COLUMN execution_time_ms INTEGER'),
                    ('gas_used', 'ALTER TABLE trades ADD COLUMN gas_used INTEGER'),
                    ('confidence_score', 'ALTER TABLE trades ADD COLUMN confidence_score REAL')
                ]
                
                for column, query in migrations:
                    if column not in columns:
                        self.conn.execute(query)
            
            # Create all tables
            self.conn.executescript('''
                -- Blacklist table
                CREATE TABLE IF NOT EXISTS blacklist (
                    address TEXT PRIMARY KEY,
                    reason TEXT,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Enhanced trades table
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
                    last_valid_block_height INTEGER,
                    ai_decision_id TEXT,
                    execution_time_ms INTEGER,
                    gas_used INTEGER,
                    confidence_score REAL,
                    FOREIGN KEY (ai_decision_id) REFERENCES ai_decisions(decision_id)
                );

                -- AI Decisions table
                CREATE TABLE IF NOT EXISTS ai_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT UNIQUE NOT NULL,
                    timestamp_utc DATETIME NOT NULL,
                    decision_type TEXT NOT NULL CHECK (decision_type IN ('BUY', 'SELL', 'HOLD')),
                    token_pair TEXT NOT NULL,
                    amount_usd REAL,
                    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                    stop_loss_price REAL,
                    take_profit_price REAL,
                    reasoning TEXT NOT NULL,
                    full_prompt TEXT,
                    raw_response TEXT,
                    aggregated_inputs TEXT NOT NULL,
                    execution_status TEXT DEFAULT 'PENDING' CHECK (execution_status IN ('PENDING', 'EXECUTED', 'FAILED', 'CANCELLED')),
                    execution_trade_id INTEGER REFERENCES trades(id),
                    gemini_tokens_input INTEGER,
                    gemini_tokens_output INTEGER,
                    gemini_cost_usd REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- System logs table
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc DATETIME NOT NULL,
                    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                    module TEXT NOT NULL,
                    message TEXT NOT NULL,
                    extra_data TEXT,
                    trade_id INTEGER REFERENCES trades(id),
                    ai_decision_id TEXT REFERENCES ai_decisions(decision_id),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Market snapshots table
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc DATETIME NOT NULL,
                    token_pair TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume_24h_usd REAL,
                    liquidity_usd REAL,
                    bid_ask_spread_bps INTEGER,
                    volatility_1h REAL,
                    source TEXT NOT NULL,
                    raw_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Portfolio snapshots table
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc DATETIME NOT NULL,
                    total_value_usd REAL NOT NULL,
                    cash_usdc REAL NOT NULL,
                    positions TEXT NOT NULL,
                    pnl_24h_usd REAL,
                    pnl_7d_usd REAL,
                    pnl_30d_usd REAL,
                    risk_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            # Create indexes for performance
            self.conn.executescript('''
                -- Trades indexes
                CREATE INDEX IF NOT EXISTS idx_trades_protocol ON trades(protocol);
                CREATE INDEX IF NOT EXISTS idx_trades_side ON trades(side);
                CREATE INDEX IF NOT EXISTS idx_trades_token_symbol ON trades(token_symbol);
                CREATE INDEX IF NOT EXISTS idx_trades_transaction_signature ON trades(transaction_signature);
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
                CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
                CREATE INDEX IF NOT EXISTS idx_trades_ai_decision ON trades(ai_decision_id);
                
                -- AI decisions indexes
                CREATE INDEX IF NOT EXISTS idx_ai_decisions_timestamp ON ai_decisions(timestamp_utc);
                CREATE INDEX IF NOT EXISTS idx_ai_decisions_type ON ai_decisions(decision_type);
                CREATE INDEX IF NOT EXISTS idx_ai_decisions_status ON ai_decisions(execution_status);
                CREATE INDEX IF NOT EXISTS idx_ai_decisions_pair ON ai_decisions(token_pair);
                CREATE INDEX IF NOT EXISTS idx_ai_decisions_created ON ai_decisions(created_at);
                
                -- System logs indexes
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp_utc);
                CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level);
                CREATE INDEX IF NOT EXISTS idx_logs_module ON system_logs(module);
                CREATE INDEX IF NOT EXISTS idx_logs_created ON system_logs(created_at);
                
                -- Market snapshots indexes
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON market_snapshots(timestamp_utc);
                CREATE INDEX IF NOT EXISTS idx_snapshots_pair ON market_snapshots(token_pair);
                CREATE INDEX IF NOT EXISTS idx_snapshots_source ON market_snapshots(source);
                
                -- Portfolio snapshots indexes
                CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp ON portfolio_snapshots(timestamp_utc);
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
                confidence_score = float(trade_data.get('confidence_score', 0.0)) if trade_data.get('confidence_score') else None
                execution_time_ms = int(trade_data.get('execution_time_ms', 0)) if trade_data.get('execution_time_ms') else None
                gas_used = int(trade_data.get('gas_used', 0)) if trade_data.get('gas_used') else None
            except ValueError:
                self.logger.error("Invalid numerical values in trade_data.")
                return

            # Handle JSON fields carefully
            jupiter_quote_response_json = json.dumps(trade_data.get('jupiter_quote_response')) if trade_data.get('jupiter_quote_response') else None
            jupiter_transaction_data_json = json.dumps(trade_data.get('jupiter_transaction_data')) if trade_data.get('jupiter_transaction_data') else None

            with self.conn:
                cursor = self.conn.execute('''
                    INSERT INTO trades 
                    (pair_address, amount, entry_price, protocol, token_symbol, trade_id_external, side, 
                     jupiter_quote_response, jupiter_transaction_data, slippage_bps, transaction_signature, 
                     last_valid_block_height, ai_decision_id, execution_time_ms, gas_used, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    last_valid_block_height,
                    trade_data.get('ai_decision_id'),
                    execution_time_ms,
                    gas_used,
                    confidence_score
                ))
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Erreur enregistrement trade: {str(e)}")
            return None

    def record_ai_decision(self, decision_data: dict) -> Optional[str]:
        """Record an AI trading decision."""
        try:
            # Generate decision ID if not provided
            decision_id = decision_data.get('decision_id', str(uuid.uuid4()))
            
            # Validate required fields
            required_fields = ['decision_type', 'token_pair', 'confidence', 'reasoning', 'aggregated_inputs']
            for field in required_fields:
                if field not in decision_data:
                    self.logger.error(f"Missing required field '{field}' in AI decision data")
                    return None
            
            # Validate decision type
            if decision_data['decision_type'] not in ['BUY', 'SELL', 'HOLD']:
                self.logger.error(f"Invalid decision_type: {decision_data['decision_type']}")
                return None
            
            # Validate confidence
            confidence = float(decision_data['confidence'])
            if not 0 <= confidence <= 1:
                self.logger.error(f"Invalid confidence value: {confidence}")
                return None
            
            # Prepare data
            timestamp_utc = decision_data.get('timestamp_utc', datetime.utcnow().isoformat())
            aggregated_inputs_json = json.dumps(decision_data['aggregated_inputs'])
            
            with self.conn:
                self.conn.execute('''
                    INSERT INTO ai_decisions 
                    (decision_id, timestamp_utc, decision_type, token_pair, amount_usd, confidence,
                     stop_loss_price, take_profit_price, reasoning, full_prompt, raw_response,
                     aggregated_inputs, execution_status, gemini_tokens_input, gemini_tokens_output, gemini_cost_usd)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    decision_id,
                    timestamp_utc,
                    decision_data['decision_type'],
                    decision_data['token_pair'],
                    decision_data.get('amount_usd'),
                    confidence,
                    decision_data.get('stop_loss_price'),
                    decision_data.get('take_profit_price'),
                    decision_data['reasoning'],
                    decision_data.get('full_prompt'),
                    decision_data.get('raw_response'),
                    aggregated_inputs_json,
                    decision_data.get('execution_status', 'PENDING'),
                    decision_data.get('gemini_tokens_input'),
                    decision_data.get('gemini_tokens_output'),
                    decision_data.get('gemini_cost_usd')
                ))
                
            self.logger.info(f"Recorded AI decision: {decision_id}")
            return decision_id
            
        except Exception as e:
            self.logger.error(f"Error recording AI decision: {e}")
            return None

    def get_ai_decision_history(self, limit: int = 50, offset: int = 0, 
                              decision_type: Optional[str] = None) -> List[Dict]:
        """Get AI decision history with optional filtering."""
        try:
            query = '''
                SELECT decision_id, timestamp_utc, decision_type, token_pair, amount_usd, confidence,
                       reasoning, execution_status, created_at
                FROM ai_decisions
            '''
            params = []
            
            if decision_type:
                query += ' WHERE decision_type = ?'
                params.append(decision_type)
            
            query += ' ORDER BY timestamp_utc DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            self.logger.error(f"Error getting AI decision history: {e}")
            return []

    def update_ai_decision_status(self, decision_id: str, status: str, trade_id: Optional[int] = None) -> bool:
        """Update the execution status of an AI decision."""
        try:
            with self.conn:
                self.conn.execute('''
                    UPDATE ai_decisions 
                    SET execution_status = ?, execution_trade_id = ?
                    WHERE decision_id = ?
                ''', (status, trade_id, decision_id))
            return True
        except Exception as e:
            self.logger.error(f"Error updating AI decision status: {e}")
            return False

    def record_system_log(self, level: str, module: str, message: str, 
                         extra_data: Optional[Dict] = None, trade_id: Optional[int] = None,
                         ai_decision_id: Optional[str] = None) -> bool:
        """Record a system log entry."""
        try:
            extra_data_json = json.dumps(extra_data) if extra_data else None
            timestamp_utc = datetime.utcnow().isoformat()
            
            with self.conn:
                self.conn.execute('''
                    INSERT INTO system_logs 
                    (timestamp_utc, level, module, message, extra_data, trade_id, ai_decision_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp_utc, level, module, message, extra_data_json, trade_id, ai_decision_id))
            return True
        except Exception as e:
            self.logger.error(f"Error recording system log: {e}")
            return False

    def record_market_snapshot(self, snapshot_data: Dict) -> bool:
        """Record a market data snapshot."""
        try:
            timestamp_utc = snapshot_data.get('timestamp_utc', datetime.utcnow().isoformat())
            raw_data_json = json.dumps(snapshot_data.get('raw_data', {}))
            
            with self.conn:
                self.conn.execute('''
                    INSERT INTO market_snapshots 
                    (timestamp_utc, token_pair, price, volume_24h_usd, liquidity_usd, 
                     bid_ask_spread_bps, volatility_1h, source, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp_utc,
                    snapshot_data['token_pair'],
                    snapshot_data['price'],
                    snapshot_data.get('volume_24h_usd'),
                    snapshot_data.get('liquidity_usd'),
                    snapshot_data.get('bid_ask_spread_bps'),
                    snapshot_data.get('volatility_1h'),
                    snapshot_data['source'],
                    raw_data_json
                ))
            return True
        except Exception as e:
            self.logger.error(f"Error recording market snapshot: {e}")
            return False

    def record_portfolio_snapshot(self, snapshot_data: Dict) -> bool:
        """Record a portfolio snapshot."""
        try:
            timestamp_utc = snapshot_data.get('timestamp_utc', datetime.utcnow().isoformat())
            positions_json = json.dumps(snapshot_data['positions'])
            
            with self.conn:
                self.conn.execute('''
                    INSERT INTO portfolio_snapshots 
                    (timestamp_utc, total_value_usd, cash_usdc, positions, pnl_24h_usd, 
                     pnl_7d_usd, pnl_30d_usd, risk_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp_utc,
                    snapshot_data['total_value_usd'],
                    snapshot_data['cash_usdc'],
                    positions_json,
                    snapshot_data.get('pnl_24h_usd'),
                    snapshot_data.get('pnl_7d_usd'),
                    snapshot_data.get('pnl_30d_usd'),
                    snapshot_data.get('risk_score')
                ))
            return True
        except Exception as e:
            self.logger.error(f"Error recording portfolio snapshot: {e}")
            return False

    def get_active_trades(self) -> List[Dict]:
        cursor = self.conn.execute('''
            SELECT id, pair_address, amount, entry_price, protocol, timestamp, token_symbol, trade_id_external, side, 
                   jupiter_quote_response, jupiter_transaction_data, slippage_bps, transaction_signature, 
                   last_valid_block_height, ai_decision_id, execution_time_ms, gas_used, confidence_score
            FROM trades WHERE status = 'open'
        ''')
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades with AI decision info."""
        cursor = self.conn.execute('''
            SELECT t.*, ad.reasoning as ai_reasoning, ad.confidence as ai_confidence
            FROM trades t
            LEFT JOIN ai_decisions ad ON t.ai_decision_id = ad.decision_id
            ORDER BY t.timestamp DESC
            LIMIT ?
        ''', (limit,))
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
            self.logger.warning(f"IntegrityError while adding to blacklist: {address}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error while adding to blacklist {address}: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()