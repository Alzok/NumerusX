#!/usr/bin/env python3

import sqlite3
import os

# Connect to database
db_path = "data/numerusx.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== ALL TABLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
if tables:
    for table in tables:
        print(f"Table: {table[0]}")
else:
    print("No tables found")

print("\n=== APP CONFIGURATION ===")
try:
    cursor.execute("SELECT key, value, value_type, category FROM app_configuration LIMIT 10")
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"Config: {row}")
    else:
        print("No data in app_configuration table")
except sqlite3.OperationalError as e:
    print(f"Error accessing app_configuration: {e}")

print("\n=== TABLE SCHEMAS ===")
cursor.execute("PRAGMA table_info(system_status)")
print("system_status schema:")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close() 