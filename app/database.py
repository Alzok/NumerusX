import sqlite3
import json
import os
from typing import Optional, Dict, List
from app.config import get_config
import logging
from datetime import datetime
import uuid

class EnhancedDatabase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_config().database.db_path
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

                -- App configuration table
                CREATE TABLE IF NOT EXISTS app_configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    value_type TEXT NOT NULL CHECK (value_type IN ('string', 'integer', 'float', 'boolean', 'json', 'encrypted')),
                    description TEXT,
                    category TEXT NOT NULL,
                    is_required BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- User preferences table
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    value_type TEXT NOT NULL CHECK (value_type IN ('string', 'integer', 'float', 'boolean', 'json')),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, preference_key)
                );

                -- System status table for application state
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY,
                    is_configured BOOLEAN DEFAULT FALSE,
                    operating_mode TEXT DEFAULT 'test' CHECK (operating_mode IN ('test', 'production')),
                    theme_name TEXT DEFAULT 'default',
                    theme_palette TEXT DEFAULT 'slate',
                    last_configuration_update DATETIME,
                    configuration_version INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
                
                -- App configuration indexes
                CREATE INDEX IF NOT EXISTS idx_config_key ON app_configuration(key);
                CREATE INDEX IF NOT EXISTS idx_config_category ON app_configuration(category);
                
                -- User preferences indexes
                CREATE INDEX IF NOT EXISTS idx_prefs_user ON user_preferences(user_id);
                CREATE INDEX IF NOT EXISTS idx_prefs_key ON user_preferences(preference_key);
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
                slippage_bps = int(trade_data.get('slippage_bps', get_config().jupiter.default_slippage_bps if hasattr(Config, 'JUPITER_DEFAULT_SLIPPAGE_BPS') else 50))
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

    # Configuration Management Methods
    def initialize_system_status(self):
        """Initialize system status if not exists."""
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT COUNT(*) FROM system_status WHERE id = 1")
                if cursor.fetchone()[0] == 0:
                    self.conn.execute("""
                        INSERT INTO system_status (id, is_configured, operating_mode, theme_name, theme_palette)
                        VALUES (1, FALSE, 'test', 'default', 'slate')
                    """)
            return True
        except Exception as e:
            self.logger.error(f"Error initializing system status: {e}")
            return False

    def is_app_configured(self) -> bool:
        """Check if the application has been configured."""
        try:
            cursor = self.conn.execute("SELECT is_configured FROM system_status WHERE id = 1")
            result = cursor.fetchone()
            return bool(result[0]) if result else False
        except Exception as e:
            self.logger.error(f"Error checking app configuration status: {e}")
            return False

    def set_app_configured(self, configured: bool = True):
        """Mark the application as configured."""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO system_status 
                    (id, is_configured, last_configuration_update, updated_at)
                    VALUES (1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (configured,))
            return True
        except Exception as e:
            self.logger.error(f"Error setting app configured status: {e}")
            return False

    def save_configuration(self, config_data: Dict[str, any]) -> bool:
        """Save configuration data to database."""
        try:
            with self.conn:
                for category, settings in config_data.items():
                    if isinstance(settings, dict):
                        for key, value in settings.items():
                            self._save_config_item(key, value, category)
                    else:
                        self._save_config_item(category, settings, "general")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def _save_config_item(self, key: str, value: any, category: str):
        """Save individual configuration item."""
        from app.utils.encryption import EncryptionService
        
        # Determine value type and whether to encrypt
        is_sensitive = self._is_sensitive_key(key)
        
        if is_sensitive:
            encrypted_value = EncryptionService.encrypt_data(str(value))
            value_to_store = encrypted_value
            type_to_store = "encrypted"
        else:
            if isinstance(value, (dict, list)):
                value_to_store = json.dumps(value)
                type_to_store = "json"
            elif isinstance(value, bool):
                value_to_store = str(value).lower()
                type_to_store = "boolean"
            elif isinstance(value, int):
                value_to_store = str(value)
                type_to_store = "integer"
            elif isinstance(value, float):
                value_to_store = str(value)
                type_to_store = "float"
            else:
                value_to_store = str(value)
                type_to_store = "string"

        self.conn.execute("""
            INSERT OR REPLACE INTO app_configuration 
            (key, value, value_type, category, is_required, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (key, value_to_store, type_to_store, category, is_sensitive))

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a configuration key contains sensitive data."""
        sensitive_keywords = [
            'api_key', 'secret', 'password', 'private_key', 'token', 
            'jwt', 'encryption', 'wallet', 'credentials'
        ]
        return any(keyword in key.lower() for keyword in sensitive_keywords)

    def load_configuration(self) -> Dict[str, any]:
        """Load configuration from database."""
        try:
            from app.utils.encryption import EncryptionService
            
            cursor = self.conn.execute("""
                SELECT key, value, value_type, category 
                FROM app_configuration 
                ORDER BY category, key
            """)
            
            config = {}
            for row in cursor.fetchall():
                key, value, value_type, category = row
                
                # Decrypt if encrypted
                if value_type == "encrypted":
                    try:
                        decrypted_value = EncryptionService.decrypt_data(value)
                        parsed_value = decrypted_value
                    except Exception as e:
                        self.logger.warning(f"Failed to decrypt config key {key}: {e}")
                        continue
                elif value_type == "json":
                    parsed_value = json.loads(value)
                elif value_type == "boolean":
                    parsed_value = value.lower() in ('true', '1', 'yes')
                elif value_type == "integer":
                    parsed_value = int(value)
                elif value_type == "float":
                    parsed_value = float(value)
                else:
                    parsed_value = value

                # Organize by category
                if category not in config:
                    config[category] = {}
                config[category][key] = parsed_value

            return config
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return {}

    def get_system_status(self) -> Dict[str, any]:
        """Get current system status."""
        try:
            cursor = self.conn.execute("""
                SELECT is_configured, operating_mode, theme_name, theme_palette,
                       last_configuration_update, configuration_version
                FROM system_status WHERE id = 1
            """)
            result = cursor.fetchone()
            
            if result:
                return {
                    'is_configured': bool(result[0]),
                    'operating_mode': result[1],
                    'theme_name': result[2], 
                    'theme_palette': result[3],
                    'last_configuration_update': result[4],
                    'configuration_version': result[5]
                }
            else:
                # Initialize if not exists
                self.initialize_system_status()
                return {
                    'is_configured': False,
                    'operating_mode': 'test',
                    'theme_name': 'default',
                    'theme_palette': 'slate',
                    'last_configuration_update': None,
                    'configuration_version': 1
                }
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {}

    def update_system_status(self, **kwargs) -> bool:
        """Update system status with provided parameters."""
        try:
            # Build dynamic UPDATE SQL based on provided kwargs
            valid_fields = ['is_configured', 'operating_mode', 'theme_name', 'theme_palette']
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in valid_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            # First, ensure record exists
            self.conn.execute("""
                INSERT OR IGNORE INTO system_status 
                (id, is_configured, operating_mode, theme_name, theme_palette, created_at, updated_at)
                VALUES (1, 0, 'test', 'default', 'slate', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            
            # Then update
            sql = f"""
                UPDATE system_status 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """
            
            with self.conn:
                self.conn.execute(sql, values)
            return True
        except Exception as e:
            self.logger.error(f"Error updating system status: {e}")
            return False

    def save_user_preference(self, user_id: str, key: str, value: any) -> bool:
        """Save user preference."""
        try:
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
                value_type = "json"
            elif isinstance(value, bool):
                value_str = str(value).lower()
                value_type = "boolean"
            elif isinstance(value, int):
                value_str = str(value)
                value_type = "integer"
            elif isinstance(value, float):
                value_str = str(value)
                value_type = "float"
            else:
                value_str = str(value)
                value_type = "string"
            
            with self.conn:
                self.conn.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, preference_key, preference_value, value_type, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, key, value_str, value_type))
            return True
        except Exception as e:
            self.logger.error(f"Error saving user preference: {e}")
            return False

    def get_user_preferences(self, user_id: str) -> Dict[str, any]:
        """Get all user preferences."""
        try:
            cursor = self.conn.execute("""
                SELECT preference_key, preference_value, value_type 
                FROM user_preferences 
                WHERE user_id = ?
                ORDER BY preference_key
            """, (user_id,))
            
            preferences = {}
            for row in cursor.fetchall():
                key, value, value_type = row
                
                if value_type == "json":
                    parsed_value = json.loads(value)
                elif value_type == "boolean":
                    parsed_value = value.lower() in ('true', '1', 'yes')
                elif value_type == "int":
                    parsed_value = int(value)
                elif value_type == "float":
                    parsed_value = float(value)
                else:
                    parsed_value = value
                    
                preferences[key] = parsed_value
                
            return preferences
        except Exception as e:
            self.logger.error(f"Error getting user preferences: {e}")
            return {}