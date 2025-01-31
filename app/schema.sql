PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS tokens (
    address TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    price REAL,
    liquidity REAL,
    volume_24h REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timestamp ON tokens(timestamp);