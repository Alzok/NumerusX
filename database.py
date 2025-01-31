import sqlite3
import logging
from config import Config, BLACKLIST_REASON

class DexDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_NAME)
        self._init_db()
    
    def _init_db(self):
        with self.conn:
            self.conn.executescript(open('schema.sql').read())
    
    def blacklist_token(self, address, reason):
        self.conn.execute("""
            INSERT OR REPLACE INTO blacklisted_coins 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (address.lower(), reason.value))
    
    def get_safety_data(self, pair_address):
        return self.conn.execute("""
            SELECT * FROM token_metrics 
            WHERE pair_address = ?
            ORDER BY time DESC LIMIT 100
        """, (pair_address,)).fetchall()

class BlacklistManager:
    def check_bundled(self, token_data):
        if token_data['top_holder'] > Config.BUNDLED_THRESHOLD:
            self.blacklist_token(
                token_data['address'], 
                BLACKLIST_REASON.BUNDLED
            )