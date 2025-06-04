# NumerusX - Database Schema et Migration 📊

## Schema Complet de la Base de Données

### Table: trades (EXISTANTE - À ENRICHIR)
- [x] Champs existants :
  - `id` INTEGER PRIMARY KEY
  - `timestamp` DATETIME
  - `token_in` TEXT
  - `token_out` TEXT
  - `amount_in` REAL
  - `amount_out` REAL
  - `price` REAL
  - `transaction_hash` TEXT
  - `status` TEXT
  - `error_message` TEXT
  - `strategy_used` TEXT
  - `profit_loss` REAL
  
- [x] Nouveaux champs ajoutés :
  - `jupiter_quote_response` TEXT (JSON de la quote Jupiter)
  - `jupiter_transaction_data` TEXT (JSON de la transaction)
  - `slippage_bps` INTEGER
  - `transaction_signature` TEXT
  - `last_valid_block_height` INTEGER
  
- [ ] Champs à ajouter :
  - `ai_decision_id` INTEGER FOREIGN KEY (lien vers ai_decisions)
  - `execution_time_ms` INTEGER (temps d'exécution)
  - `gas_used` INTEGER (frais en lamports)
  - `confidence_score` REAL (confiance de l'IA)
  
- [ ] Index à créer :
  - INDEX idx_trades_timestamp ON trades(timestamp)
  - INDEX idx_trades_status ON trades(status)
  - INDEX idx_trades_ai_decision ON trades(ai_decision_id)
  - INDEX idx_trades_token_pair ON trades(token_in, token_out)

### Table: ai_decisions (IMPLÉMENTÉE) ✅
- [x] Structure complète :
  ```sql
  CREATE TABLE ai_decisions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      decision_id TEXT UNIQUE NOT NULL,
      timestamp_utc DATETIME NOT NULL,
      decision_type TEXT NOT NULL, -- 'BUY', 'SELL', 'HOLD'
      token_pair TEXT NOT NULL,
      amount_usd REAL,
      confidence REAL NOT NULL,
      stop_loss_price REAL,
      take_profit_price REAL,
      reasoning TEXT NOT NULL, -- Raisonnement court de l'IA
      full_prompt TEXT, -- Prompt complet envoyé à Gemini
      raw_response TEXT, -- Réponse brute de Gemini
      aggregated_inputs TEXT NOT NULL, -- JSON des inputs complets
      execution_status TEXT DEFAULT 'PENDING', -- 'PENDING', 'EXECUTED', 'FAILED', 'CANCELLED'
      execution_trade_id INTEGER REFERENCES trades(id),
      gemini_tokens_input INTEGER,
      gemini_tokens_output INTEGER,
      gemini_cost_usd REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```
  
- [x] Index :
  - INDEX idx_ai_decisions_timestamp ON ai_decisions(timestamp_utc)
  - INDEX idx_ai_decisions_type ON ai_decisions(decision_type)
  - INDEX idx_ai_decisions_status ON ai_decisions(execution_status)
  - INDEX idx_ai_decisions_pair ON ai_decisions(token_pair)

### Table: system_logs (IMPLÉMENTÉE) ✅
- [x] Structure :
  ```sql
  CREATE TABLE system_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp_utc DATETIME NOT NULL,
      level TEXT NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
      module TEXT NOT NULL, -- Module source du log
      message TEXT NOT NULL,
      extra_data TEXT, -- JSON pour données additionnelles
      trade_id INTEGER REFERENCES trades(id),
      ai_decision_id INTEGER REFERENCES ai_decisions(id),
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```
  
- [ ] Index :
  - INDEX idx_logs_timestamp ON system_logs(timestamp_utc)
  - INDEX idx_logs_level ON system_logs(level)
  - INDEX idx_logs_module ON system_logs(module)
  - INDEX idx_logs_created ON system_logs(created_at)

### Table: market_snapshots (NOUVELLE)
- [ ] Structure pour historique des données de marché :
  ```sql
  CREATE TABLE market_snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp_utc DATETIME NOT NULL,
      token_pair TEXT NOT NULL,
      price REAL NOT NULL,
      volume_24h_usd REAL,
      liquidity_usd REAL,
      bid_ask_spread_bps INTEGER,
      volatility_1h REAL,
      source TEXT NOT NULL, -- 'jupiter', 'dexscreener', etc.
      raw_data TEXT, -- JSON complet
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```
  
- [ ] Index :
  - INDEX idx_snapshots_timestamp ON market_snapshots(timestamp_utc)
  - INDEX idx_snapshots_pair ON market_snapshots(token_pair)
  - INDEX idx_snapshots_source ON market_snapshots(source)

### Table: strategy_performance (NOUVELLE)
- [ ] Structure pour tracking performance des stratégies :
  ```sql
  CREATE TABLE strategy_performance (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      strategy_name TEXT NOT NULL,
      period_start DATETIME NOT NULL,
      period_end DATETIME NOT NULL,
      total_trades INTEGER NOT NULL,
      winning_trades INTEGER NOT NULL,
      losing_trades INTEGER NOT NULL,
      total_pnl_usd REAL NOT NULL,
      sharpe_ratio REAL,
      max_drawdown_pct REAL,
      win_rate REAL,
      profit_factor REAL,
      avg_trade_duration_minutes INTEGER,
      metadata TEXT, -- JSON pour données additionnelles
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```
  
- [ ] Index :
  - INDEX idx_perf_strategy ON strategy_performance(strategy_name)
  - INDEX idx_perf_period ON strategy_performance(period_start, period_end)

### Table: portfolio_snapshots (NOUVELLE)
- [ ] Structure pour historique du portfolio :
  ```sql
  CREATE TABLE portfolio_snapshots (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp_utc DATETIME NOT NULL,
      total_value_usd REAL NOT NULL,
      cash_usdc REAL NOT NULL,
      positions TEXT NOT NULL, -- JSON array des positions
      pnl_24h_usd REAL,
      pnl_7d_usd REAL,
      pnl_30d_usd REAL,
      risk_score REAL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```
  
- [ ] Index :
  - INDEX idx_portfolio_timestamp ON portfolio_snapshots(timestamp_utc)

## Migrations

### Migration v1 -> v2 (Ajout tables AI et logs)
- [ ] Script de migration `migrations/v1_to_v2.sql` :
  ```sql
  -- Backup existant
  CREATE TABLE trades_backup AS SELECT * FROM trades;
  
  -- Ajouter colonnes manquantes à trades
  ALTER TABLE trades ADD COLUMN ai_decision_id INTEGER;
  ALTER TABLE trades ADD COLUMN execution_time_ms INTEGER;
  ALTER TABLE trades ADD COLUMN gas_used INTEGER;
  ALTER TABLE trades ADD COLUMN confidence_score REAL;
  
  -- Créer nouvelles tables
  -- (Copier les CREATE TABLE ci-dessus)
  
  -- Créer les index
  -- (Copier les CREATE INDEX ci-dessus)
  ```

### Système de Migration Automatique
- [ ] Créer `app/database_migrations.py` :
  - [ ] Classe `MigrationManager`
  - [ ] Méthode `check_schema_version()`
  - [ ] Méthode `apply_migrations()`
  - [ ] Table `schema_versions` pour tracking
  
- [ ] Structure table schema_versions :
  ```sql
  CREATE TABLE schema_versions (
      version INTEGER PRIMARY KEY,
      applied_at DATETIME NOT NULL,
      description TEXT
  );
  ```

### Validation et Intégrité
- [ ] Contraintes à ajouter :
  - [ ] CHECK constraints sur les enums (status, decision_type, etc.)
  - [ ] Foreign keys avec ON DELETE CASCADE où approprié
  - [ ] NOT NULL sur champs critiques
  
- [ ] Triggers :
  - [ ] Trigger pour auto-update `updated_at` timestamps
  - [ ] Trigger pour valider cohérence trades/ai_decisions

### Optimisations Performance
- [ ] Configuration SQLite :
  - [ ] PRAGMA journal_mode = WAL
  - [ ] PRAGMA synchronous = NORMAL
  - [ ] PRAGMA cache_size = -64000 (64MB cache)
  - [ ] PRAGMA temp_store = MEMORY
  
- [ ] Maintenance régulière :
  - [ ] VACUUM hebdomadaire
  - [ ] ANALYZE après migrations
  - [ ] Rotation des logs anciens (>30 jours)

### Backup et Récupération
- [ ] Stratégie de backup :
  - [ ] Backup automatique quotidien
  - [ ] Rotation sur 7 jours
  - [ ] Export CSV des trades pour analyse externe
  
- [ ] Script `backup_database.py` :
  - [ ] Copie de la DB avec timestamp
  - [ ] Compression des backups anciens
  - [ ] Vérification intégrité post-backup

## Intégration avec l'Application

### EnhancedDatabase Updates
- [x] Nouvelles méthodes implémentées :
  - [x] `record_ai_decision()` - Enregistrer décision IA
  - [x] `get_ai_decision_history()` - Historique décisions
  - [x] `update_ai_decision_status()` - Mettre à jour statut décision
  - [x] `record_system_log()` - Logger dans DB
  - [x] `record_portfolio_snapshot()` - Snapshot portfolio
  - [x] `record_market_snapshot()` - Snapshot marché
  - [ ] `get_strategy_performance()` - Performance stratégies
  
- [ ] Validation Pydantic :
  - [ ] Modèle `TradeRecord` pour validation
  - [ ] Modèle `AIDecisionRecord` pour validation
  - [ ] Modèle `SystemLogRecord` pour validation

### API Endpoints pour Données
- [ ] Routes dans `app/api/v1/database_routes.py` :
  - [ ] GET `/api/v1/db/trades` - Historique trades paginé
  - [ ] GET `/api/v1/db/ai-decisions` - Décisions IA
  - [ ] GET `/api/v1/db/performance` - Métriques performance
  - [ ] GET `/api/v1/db/logs` - Logs système filtrés
  - [ ] GET `/api/v1/db/export` - Export données CSV/JSON

## Tests Database
- [ ] Créer `tests/test_database_schema.py` :
  - [ ] Test création tables
  - [ ] Test migrations
  - [ ] Test contraintes et triggers
  - [ ] Test performance queries
  
- [ ] Créer `tests/test_database_operations.py` :
  - [ ] Test CRUD operations
  - [ ] Test transactions
  - [ ] Test concurrent access
  - [ ] Test backup/restore

## Monitoring et Alertes
- [ ] Métriques à surveiller :
  - [ ] Taille de la base de données
  - [ ] Temps de réponse des queries
  - [ ] Nombre de trades/décisions par jour
  - [ ] Taux d'erreur des transactions
  
- [ ] Alertes :
  - [ ] DB size > 1GB
  - [ ] Query time > 1s
  - [ ] Backup failure
  - [ ] Schema corruption