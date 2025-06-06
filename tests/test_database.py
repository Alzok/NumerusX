import unittest
import sqlite3
import json
import os
from app.database import EnhancedDatabase
from app.config import get_config # For DB_PATH, though we'll override

# Sample data for new fields
SAMPLE_JUPITER_QUOTE_RESPONSE = {"inputMint": "SOL", "outAmount": "150000000"}
SAMPLE_JUPITER_TRANSACTION_DATA = {"swap_transaction": "base64encodedtx"}

class TestEnhancedDatabase(unittest.TestCase):

    def setUp(self):
        # Override Config.DB_PATH to use an in-memory database for tests
        self.original_db_path = Config.DB_PATH
        Config.DB_PATH = ":memory:"
        
        self.db = EnhancedDatabase() # This will create an in-memory DB
        # self.conn = self.db.conn # Direct access to connection for verification
        self.conn = sqlite3.connect(":memory:") # Use a separate conn for setup to avoid EnhancedDB's logic if needed
        self.db.conn = self.conn # Override the connection in EnhancedDatabase instance for this test
        self.db._init_db() # Manually call _init_db on the new connection

    def tearDown(self):
        self.conn.close()
        Config.DB_PATH = self.original_db_path # Restore original DB_PATH

    def test_record_trade_and_get_active_trades_with_new_fields(self):
        trade_details = {
            "pair": "SOL/USDC",
            "amount": 10.5,
            "entry_price": 150.25,
            "protocol": "JupiterV6",
            "token_symbol": "SOL",
            "trade_id": "external_trade_123",
            "side": "buy",
            "jupiter_quote_response": SAMPLE_JUPITER_QUOTE_RESPONSE,
            "jupiter_transaction_data": SAMPLE_JUPITER_TRANSACTION_DATA,
            "slippage_bps": 50,
            "transaction_signature": "sig_abc123xyz",
            "last_valid_block_height": 123456789
            # status defaults to 'open' in record_trade if not provided, or schema default
        }

        self.db.record_trade(trade_details)

        # Verify directly in DB (optional, get_active_trades is better test of read path)
        cursor = self.conn.execute("SELECT * FROM trades WHERE pair_address = ?", (trade_details["pair"],))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        
        # Fetch column names to map row values to dict
        db_column_names = [description[0] for description in cursor.description]
        db_row_dict = dict(zip(db_column_names, row))

        self.assertEqual(db_row_dict['pair_address'], trade_details['pair'])
        self.assertEqual(db_row_dict['amount'], trade_details['amount'])
        self.assertEqual(db_row_dict['entry_price'], trade_details['entry_price'])
        self.assertEqual(db_row_dict['protocol'], trade_details['protocol'])
        self.assertEqual(db_row_dict['token_symbol'], trade_details['token_symbol'])
        self.assertEqual(db_row_dict['trade_id_external'], trade_details['trade_id'])
        self.assertEqual(db_row_dict['side'], trade_details['side'])
        self.assertEqual(json.loads(db_row_dict['jupiter_quote_response']), trade_details['jupiter_quote_response'])
        self.assertEqual(json.loads(db_row_dict['jupiter_transaction_data']), trade_details['jupiter_transaction_data'])
        self.assertEqual(db_row_dict['slippage_bps'], trade_details['slippage_bps'])
        self.assertEqual(db_row_dict['transaction_signature'], trade_details['transaction_signature'])
        self.assertEqual(db_row_dict['last_valid_block_height'], trade_details['last_valid_block_height'])
        self.assertEqual(db_row_dict['status'], 'open') # Default status

        # Test get_active_trades
        active_trades = self.db.get_active_trades()
        self.assertEqual(len(active_trades), 1)
        retrieved_trade = active_trades[0]

        self.assertEqual(retrieved_trade['pair_address'], trade_details['pair'])
        self.assertEqual(retrieved_trade['amount'], trade_details['amount'])
        # ... (assert all other fields, especially new ones)
        self.assertEqual(json.loads(retrieved_trade['jupiter_quote_response']), trade_details['jupiter_quote_response'])
        self.assertEqual(json.loads(retrieved_trade['jupiter_transaction_data']), trade_details['jupiter_transaction_data'])
        self.assertEqual(retrieved_trade['slippage_bps'], trade_details['slippage_bps'])
        self.assertEqual(retrieved_trade['transaction_signature'], trade_details['transaction_signature'])
        self.assertEqual(retrieved_trade['last_valid_block_height'], trade_details['last_valid_block_height'])

    def test_record_trade_handles_missing_optional_new_fields(self):
        trade_details = {
            "pair": "SOL/USDC",
            "amount": 5.0,
            "entry_price": 140.0,
            # Omitting new optional fields like jupiter_quote_response, transaction_signature etc.
        }
        self.db.record_trade(trade_details)
        active_trades = self.db.get_active_trades()
        self.assertEqual(len(active_trades), 1)
        retrieved_trade = active_trades[0]

        self.assertEqual(retrieved_trade['pair_address'], trade_details['pair'])
        self.assertIsNone(retrieved_trade['jupiter_quote_response'])
        self.assertIsNone(retrieved_trade['jupiter_transaction_data'])
        self.assertIsNone(retrieved_trade['transaction_signature'])
        self.assertIsNone(retrieved_trade['last_valid_block_height'])
        # slippage_bps should have a default from Config or hardcoded in record_trade
        # The record_trade method has: trade_data.get('slippage_bps', Config.JUPITER_DEFAULT_SLIPPAGE_BPS if hasattr(Config, 'JUPITER_DEFAULT_SLIPPAGE_BPS') else 50)
        # We need to ensure Config.JUPITER_DEFAULT_SLIPPAGE_BPS exists or mock it for predictable test
        if hasattr(Config, 'JUPITER_DEFAULT_SLIPPAGE_BPS'):
             self.assertEqual(retrieved_trade['slippage_bps'], Config.JUPITER_DEFAULT_SLIPPAGE_BPS)
        else:
            self.assertEqual(retrieved_trade['slippage_bps'], 50) # Default if not in config

if __name__ == '__main__':
    unittest.main() 