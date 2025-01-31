CREATE TABLE IF NOT EXISTS tokens (
    pair_address TEXT PRIMARY KEY,
    base_token_symbol TEXT,
    price REAL,
    liquidity REAL
);

CREATE TABLE IF NOT EXISTS blacklisted_coins (
    address TEXT PRIMARY KEY,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);