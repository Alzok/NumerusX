#!/usr/bin/env python3

import sqlite3
import os

# Connect to database
db_path = "data/numerusx.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)

print("Creating missing tables...")

# Create the missing tables
conn.executescript('''
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

conn.commit()
print("Tables created successfully!")

# Verify
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [table[0] for table in cursor.fetchall()]
print(f"All tables: {tables}")

# Initialize system status
conn.execute("""
    INSERT OR IGNORE INTO system_status 
    (id, is_configured, operating_mode, theme_name, theme_palette, created_at, updated_at)
    VALUES (1, 0, 'test', 'default', 'slate', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
""")
conn.commit()
print("System status initialized!")

conn.close() 