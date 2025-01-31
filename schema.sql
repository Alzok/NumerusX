CREATE TABLE IF NOT EXISTS token_metrics (
    address TEXT PRIMARY KEY,
    liquidity REAL,
    volume_24h REAL,
    safety_score INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blacklisted_coins (
    address TEXT PRIMARY KEY,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);