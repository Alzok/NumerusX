# NumerusX - IA TODO List 🤖

**Prompt pour l'IA**: Exécute les tâches une par une. Quand tu as terminé une tâche, vérifie la cohérence du code par rapport à l'ensemble du projet et au contexte fourni. Une fois la vérification terminée et la cohérence assurée, passe en autonomie à la tâche suivante.

## Phase 1: Initialisation et Configuration de Base (Jupiter API v6) - FONDATIONS

**Objectif**: Configurer l'environnement, intégrer le SDK Jupiter, et établir les bases pour l'interaction avec l'API Jupiter v6.

-   [x] **1.1. `app/config.py` (Jupiter API v6)**
    -   [x] Ajouter les nouveaux hostnames de l'API Jupiter v6 (`JUPITER_LITE_API_HOSTNAME`, `JUPITER_PRO_API_HOSTNAME`).
    -   [x] Ajouter les nouveaux chemins d'API pour `swap`, `price`, `tokens`, `trigger`, `recurring` (`JUPITER_SWAP_API_PATH`, etc.).
    -   [x] Ajouter les paramètres de transaction Jupiter (slippage, compute units, priority fees, etc. : `JUPITER_DEFAULT_SLIPPAGE_BPS`, `JUPITER_DYNAMIC_COMPUTE_UNIT_LIMIT`, `JUPITER_COMPUTE_UNIT_PRICE_MICRO_LAMPORTS`, `JUPITER_PRIORITY_FEE_LEVEL`, `JUPITER_WRAP_AND_UNWRAP_SOL`, `JUPITER_ONLY_DIRECT_ROUTES`, `JUPITER_RESTRICT_INTERMEDIATE_TOKENS`, `JUPITER_SWAP_MODE`).
    -   [x] Marquer les anciennes constantes Jupiter V4/V6 (ex: `JUPITER_API_BASE_URL_LEGACY`, `JUPITER_QUOTE_URL_SUFFIX_LEGACY`) comme "DEPRECATED" ou les commenter.
    -   [x] Revoir et potentiellement marquer comme obsolètes les getters de `Config` pour les URLs Jupiter (ex: `get_jupiter_quote_url`) si `JupiterApiClient` gère la construction des URLs.
    -   [x] `JUPITER_MAX_RETRIES` pour `JupiterApiClient`.
-   [x] **1.1.bis. `requirements.txt`**
    -   [x] Ajouter `jupiter-python-sdk>=0.24.0`.
-   [x] **1.2. `app/logger.py` (Optionnel - si des configurations spécifiques sont nécessaires pour Jupiter)**
    -   [x] (Considéré comme non nécessaire pour l'instant, la journalisation standard suffit.)
-   [x] **1.3. `app/utils/jupiter_api_client.py` (Nouveau Client API Jupiter SDK)**
    -   [x] Créer le fichier.
    -   [x] Implémenter `JupiterApiClient` en utilisant `jupiter-python-sdk`.
        -   [x] `__init__`:
            -   [x] Initialiser `Keypair` à partir de `SOLANA_PRIVATE_KEY_BS58` (ou une clé dédiée si configurée).
            -   [x] Initialiser `AsyncClient` de `solana.rpc.async_api`.
            -   [x] Initialiser l'instance `Jupiter` du SDK (`jupiter_python_sdk.jupiter.Jupiter`) avec les URLs de base construites à partir des nouvelles constantes de `Config` (`JUPITER_LITE_API_HOSTNAME`, `JUPITER_PRO_API_HOSTNAME` si clé API Pro).
            -   [x] Gérer la logique pour `JUPITER_PRO_API_HOSTNAME` et la clé API Jupiter si elle est fournie dans `Config`.
        -   [x] `_call_sdk_method(sdk_method_callable, *args, **kwargs)`: Wrapper interne pour les appels SDK avec `tenacity.retry` (utilisant `JUPITER_MAX_RETRIES`). Doit lever `JupiterAPIError` en cas d'échec après les reintentions.
        -   [x] `get_quote(...)`: Implémenter la méthode pour obtenir une quote via le SDK.
            -   [x] Paramètres : `input_mint_str`, `output_mint_str`, `amount_lamports`, `slippage_bps` (optionnel, défaut `Config.JUPITER_DEFAULT_SLIPPAGE_BPS`), `swap_mode` (optionnel, défaut `Config.JUPITER_SWAP_MODE`).
            -   [x] Utiliser les constantes de `Config` pour les paramètres de la requête (`only_direct_routes`, `dynamic_compute_unit_limit`, `compute_unit_price_micro_lamports` / `priority_fee_level`).
            -   [x] Retourner la réponse brute du SDK ou un `Dict` standardisé. Lever `JupiterAPIError` en cas d'échec.
        -   [x] `get_swap_transaction_data(quote_response)`: Implémenter la méthode pour obtenir les données de transaction de swap via le SDK.
            -   [x] Paramètres : `quote_response` (la réponse de `get_quote`), `payer_public_key` (automatiquement `self.keypair.public_key`).
            -   [x] Utiliser les constantes de `Config` pour les paramètres (`wrap_and_unwrap_sol`, etc.).
            -   [x] Retourner un `Dict` standardisé avec `serialized_transaction_b64` et `last_valid_block_height`. Lever `JupiterAPIError` en cas d'échec.
        -   [x] `sign_and_send_transaction(serialized_transaction_b64, last_valid_block_height)`: Implémenter la signature et l'envoi de la transaction.
            -   [x] Décoder `serialized_transaction_b64`.
            -   [x] Désérialiser en `VersionedTransaction`.
            -   [x] Signer la transaction avec `self.keypair`.
            -   [x] Envoyer la transaction via `AsyncClient.send_transaction` avec `TxOpts(skip_preflight=True, last_valid_block_height=...)`.
            -   [x] Confirmer la transaction avec `AsyncClient.confirm_transaction`.
            -   [x] Gérer `TransactionExpiredBlockheightExceededError` (lever `TransactionExpiredError` pour que l'appelant (ex: `TradingEngine`) puisse rafraîchir la quote et la tx).
            -   [x] Gérer les autres erreurs (`SendTransactionPreflightFailureError` -> `TransactionSimulationError`, `TimeoutError` -> `TransactionConfirmationError`).
            -   [x] Lever des sous-types de `SolanaTransactionError` appropriés.
            -   [x] Retourner la signature de la transaction (string) en cas de succès.
        -   [x] `get_prices(token_ids_list, vs_token_str)`: Implémenter la récupération des prix. Lever `JupiterAPIError`.
        -   [x] `get_token_info_list(mint_address_list, tag_list)`: Implémenter la récupération des infos de tokens. Lever `JupiterAPIError`.
        -   [x] Méthodes pour les ordres Trigger (Limit Orders) : `create_trigger_order`, `execute_trigger_order` (si applicable), `cancel_trigger_order`, `get_trigger_orders`. Lever `JupiterAPIError`.
        -   [x] Méthodes pour les ordres DCA : `create_dca_plan`, `get_dca_orders`, `close_dca_order`. Lever `JupiterAPIError`.
        -   [x] `close_async_client()`: Pour fermer la session `AsyncClient`.
-   [x] **1.4. `app/market/market_data.py` (Refactor pour Jupiter SDK)**
    -   [x] `MarketDataProvider.__init__`:
        -   [x] Initialiser `JupiterApiClient` (passer la clé privée de `Config`, l'URL RPC, et l'instance `Config`).
    -   [x] Refactoriser `_get_jupiter_price`:
        -   [x] Utiliser `self.jupiter_client.get_prices()`.
        -   [x] Adapter la réponse du SDK au format attendu par `get_token_price`.
        -   [x] Gérer `JupiterAPIError` et retourner le dict `{'success': False, ...}`.
    -   [x] Refactoriser `_get_jupiter_token_info`:
        -   [x] Utiliser `self.jupiter_client.get_token_info_list()`.
        -   [x] Adapter la réponse du SDK, s'assurer que les `decimals` sont prioritaires.
        -   [x] Gérer `JupiterAPIError` et retourner le dict `{'success': False, ...}`.
    -   [x] Refactoriser `get_jupiter_swap_quote`:
        -   [x] Doit accepter `amount_in_tokens` (float, ex: 0.1 SOL) au lieu de `amount_lamports`.
        -   [x] Appeler `self.get_token_info()` pour obtenir les décimales du token d'entrée.
        -   [x] Calculer `amount_lamports` à partir de `amount_in_tokens` et des décimales.
        -   [x] Appeler `self.jupiter_client.get_quote()` avec les paramètres corrects.
        -   [x] Retourner la réponse brute du SDK dans le champ `data` du dictionnaire standard.
        -   [x] Gérer `JupiterAPIError` et retourner le dict `{'success': False, ...}`.
    -   [x] Supprimer les anciennes méthodes `_fetch_jupiter_quote_v6`, `_fetch_jupiter_price_v4`, `_convert_jupiter_format` (basées sur `aiohttp`).
-   [x] **1.5. Gestion des Erreurs (Améliorations Initiales)**
    -   [x] `app/utils/exceptions.py`:
        -   [x] Définir une hiérarchie d'exceptions custom: `NumerusXBaseError`, `APIError` (avec `api_name`, `status_code`), `JupiterAPIError`, `DexScreenerAPIError`, `GeminiAPIError`.
        -   [x] Définir `TradingError`, `SwapExecutionError`, `OrderPlacementError`.
        -   [x] Définir `SolanaTransactionError` (avec `signature`), et ses sous-types : `TransactionSimulationError`, `TransactionBroadcastError`, `TransactionConfirmationError`, `TransactionExpiredError`.
    -   [x] `app/utils/jupiter_api_client.py`:
        -   [x] `_call_sdk_method`: Doit attraper les exceptions du SDK (ex: `JupiterPythonSdkException`, et autres exceptions spécifiques si documentées par le SDK) et les encapsuler dans `JupiterAPIError` (avec `original_exception`).
        -   [x] `sign_and_send_transaction`: Doit lever `TransactionExpiredError`, `TransactionSimulationError`, `TransactionBroadcastError`, `TransactionConfirmationError` (qui sont des sous-types de `SolanaTransactionError`) comme spécifié.
        -   [x] Les autres méthodes (`get_quote`, `get_swap_transaction_data`, `get_prices`, etc.) doivent propager `JupiterAPIError` levée par `_call_sdk_method` ou lever directement `JupiterAPIError` pour des erreurs de logique interne/validation de paramètres avant l'appel SDK.
        -   [x] **Confirmation du Contrat d'Interface**: Les méthodes de `JupiterApiClient` lèvent des exceptions en cas d'erreur et retournent les données directes du SDK (ou un `Dict` standardisé si une transformation minimale est nécessaire) en cas de succès. Elles ne retournent PAS de dictionnaires `{'success': True/False, ...}`.
    -   [x] `app/market/market_data.py`:
        -   [x] Les méthodes appelant `JupiterApiClient` (ex: `_get_jupiter_price`, `_get_jupiter_token_info`, `get_jupiter_swap_quote`) **doivent attraper** `JupiterAPIError` (et potentiellement `SolanaTransactionError` si `MarketDataProvider` devait un jour initier des transactions, bien que ce ne soit pas son rôle actuel pour les quotes/prix).
        -   [x] En cas d'exception attrapée depuis `JupiterApiClient`, ces méthodes de `MarketDataProvider` **transformeront l'exception en le dictionnaire standard** `{'success': False, 'error': str(e), 'data': None, 'details': e}`. Ceci maintient un contrat d'interface cohérent pour les utilisateurs de `MarketDataProvider` (comme `DexBot`), qui s'attendent à ce format de dictionnaire pour la gestion des erreurs de sources de données.
        -   [x] Les appels `aiohttp` directs (ex: pour DexScreener) doivent lever `DexScreenerAPIError` en cas d'échec, qui sera ensuite attrapée par la méthode publique de `MarketDataProvider` l'utilisant et transformée de la même manière en `{'success': False, ...}`.
        -   [x] `get_token_price` et `get_token_info`: Mettre à jour pour attraper `JupiterAPIError` et `DexScreenerAPIError` de leurs appels internes respectifs (`_get_jupiter_price`, appels à DexScreener) et retourner le format de dictionnaire standardisé, en agrégeant les messages d'erreur si plusieurs sources sont interrogées et échouent.
-   [x] **1.6. `app/trading/trading_engine.py` (Robustification et Intégration Jupiter SDK)**
    -   [x] `TradingEngine.__init__`:
        -   [x] Initialiser `Config`.
        -   [x] Initialiser `JupiterApiClient` (passer la clé privée `config.SOLANA_PRIVATE_KEY_BS58`, l'URL RPC, et `config`).
        -   [x] `MarketDataProvider` peut être initialisé à `None` ici et instancié dans `__aenter__`.
    -   [x] `TradingEngine.__aenter__` / `__aexit__`:
        -   [x] Gérer l'instanciation et le cycle de vie de `MarketDataProvider` (via `await self.market_data_provider.__aenter__()` et `__aexit__`) si `TradingEngine` en est responsable.
    -   [x] Nouvelle méthode privée `_execute_swap_attempt(input_token_mint, output_token_mint, amount_in_tokens_float, slippage_bps)`:
        -   [x] Contient la logique de base du swap : `self.market_data_provider.get_jupiter_swap_quote`, `self.jupiter_client.get_swap_transaction_data`, `self.jupiter_client.sign_and_send_transaction`.
        -   [x] Doit retourner la signature de la transaction (string) ou lever des exceptions (`JupiterAPIError`, `SolanaTransactionError` sous-types).
        -   [x] Décorer avec `tenacity.retry` pour réessayer spécifiquement en cas de `TransactionExpiredError` (en utilisant `Config.JUPITER_MAX_RETRIES`).
    -   [x] `TradingEngine.execute_swap` (méthode publique):
        -   [x] Gérer la conversion USD -> montant en tokens si `amount_in_usd` est fourni (utiliser `self.market_data_provider.get_token_price`).
        -   [x] Appeler `_execute_swap_attempt` dans un bloc `try...except`.
        -   [x] Attraper `TransactionExpiredError` (après les reintentions de `_execute_swap_attempt`). Si cette erreur persiste, cela indique que la quote et le blockhash ne sont plus valides. `DexBot` devrait idéalement être informé pour potentiellement rafraîchir toutes les données et redemander une décision à l'AIAgent. Attraper également `JupiterAPIError`, `SolanaTransactionError` (et ses sous-types), et d'autres `NumerusXBaseError` ou exceptions génériques. Ces erreurs doivent être journalisées de manière critique. `DexBot` peut décider de suspendre temporairement le trading sur la paire concernée ou d'alerter l'utilisateur.
        -   [x] Formater le dictionnaire final `{'success': ..., 'error': ..., 'signature': ..., 'details': ...}`.
        -   [x] Appeler `_record_transaction` avec le résultat.
    -   [x] Revoir et marquer comme obsolètes les anciennes méthodes `_get_swap_routes`, `_select_best_quote`, `_build_swap_transaction`, `_execute_transaction`, `_execute_fallback_swap`, `_make_jupiter_api_request` qui effectuaient des appels `aiohttp` directs à l'API Jupiter. (Vérifié, ces méthodes ne sont plus présentes, elles ont été supprimées/refactorisées lors des étapes précédentes.)
    -   [ ] **Méthodes Futures pour Ordres Avancés (Limite, DCA)**: S'assurer que les futures implémentations de méthodes publiques dans `TradingEngine` pour gérer les ordres Limite, DCA, etc. (ex: `place_limit_order`, `create_dca_plan`) utilisent les fonctionnalités correspondantes du `self.jupiter_client` (`JupiterApiClient`) et n'interagissent pas directement avec l'API HTTP de Jupiter.
-   [x] **1.7. `app/dex_bot.py` (Ajustements Initiaux)**
    -   [x] (À déterminer si des ajustements sont nécessaires à ce stade, probablement minimes. La logique principale de trading sera revue en Phase 4). *(Note: Initial review suggests minimal changes currently needed due to existing abstractions. Deeper integration testing may reveal further needs.)*
-   [x] **1.8. Fiabilisation de la Base de Données (`app/database.py`)**
    -   [x] Ajouter les champs suivants à la table `trades` (avec migration pour tables existantes) :
        -   [x] `jupiter_quote_response` (TEXT, stockera la réponse JSON de la quote)
        -   [x] `jupiter_transaction_data` (TEXT, stockera la réponse JSON de la transaction de swap avant envoi)
        -   [x] `slippage_bps` (INTEGER)
        -   [x] `transaction_signature` (TEXT, explicite pour la signature on-chain)
        -   [x] `last_valid_block_height` (INTEGER)
    -   [x] Mettre à jour `EnhancedDatabase.record_trade` pour accepter et stocker ces nouveaux champs.
    -   [x] Mettre à jour `EnhancedDatabase.get_active_trades` (et autres méthodes de lecture si nécessaire) pour inclure ces champs.
-   [ ] **1.9. Tests Unitaires et d'Intégration (Initiaux)**
    -   [ ] `tests/test_config.py`: Vérifier le chargement des nouvelles constantes Jupiter.
    -   [ ] `tests/test_jupiter_api_client.py`: (Nouveau) Tests pour `JupiterApiClient` (mock des appels SDK et RPC).
        -   [x] __init__
        -   [x] get_quote
        -   [x] get_swap_transaction_data
        -   [x] sign_and_send_transaction (vérifier gestion erreurs spécifiques Solana)
        -   [x] close_async_client
        -   [ ] `get_prices`
        -   [ ] `get_token_info_list`
        -   [ ] `create_trigger_order` (et vérifier si le SDK `jupiter.trigger_create_order` existe et fonctionne)
        -   [ ] `cancel_trigger_order` (et vérifier si le SDK `jupiter.trigger_cancel_order` existe et fonctionne)
        -   [ ] `get_trigger_orders` (et vérifier si le SDK `jupiter.trigger_get_orders` existe et fonctionne)
        -   [ ] `create_dca_plan` (et vérifier si le SDK `jupiter.dca_create` existe et fonctionne)
        -   [ ] `get_dca_orders` (et vérifier si le SDK `jupiter.dca_get_orders` existe et fonctionne)
        -   [ ] `close_dca_order` (et vérifier si le SDK `jupiter.dca_close` existe et fonctionne)
        -   [ ] (Note: `execute_trigger_order` est retiré de la liste des tests directs car il n'est pas implémenté comme un appel SDK distinct dans `JupiterApiClient` pour le moment, l'action de création est supposée soumettre l'ordre. À valider lors de l'écriture des tests pour `create_trigger_order`.)
    -   [ ] `tests/test_market_data.py`: Mettre à jour pour mocker `JupiterApiClient` et tester les méthodes refactorisées.
    -   [ ] `tests/test_trading_engine.py`: Mettre à jour pour mocker `JupiterApiClient` et `MarketDataProvider`, tester `execute_swap` (succès, erreurs API, erreurs de transaction).
    -   [ ] `tests/test_database.py`: Vérifier l'enregistrement et la lecture des nouveaux champs de trade.

## Phase 1.bis: Configuration pour Nouvelle UI React et Backend

- [ ] **1.10. `app/main.py` (Backend FastAPI - Modifications pour UI)**
    - [ ] **1.10.1. Intégration Socket.io (FastAPI)**:
        - [ ] Ajouter `python-socketio` et `uvicorn[standard]` (si pas déjà là pour WebSockets) à `requirements.txt`.
        - [ ] Configurer `SocketManager` dans FastAPI.
        - [ ] Implémenter des namespaces et événements Socket.io de base pour envoyer des données en temps réel à l'UI React (ex: mises à jour de l'état du bot, P&L, logs, décisions IA, santé des systèmes).
        - [ ] Définir des événements pour recevoir des commandes de l'UI (ex: Start/Stop Bot, ajustement des paramètres de stratégie).
    - [ ] **1.10.2. Endpoints API pour Authentification (Clerk/Auth0)**:
        - [ ] Si Clerk/Auth0 nécessite des endpoints backend pour la validation de token ou la synchronisation des utilisateurs, les implémenter.
        - [ ] Sécuriser les endpoints FastAPI et les connexions Socket.io en utilisant les tokens JWT de Clerk/Auth0.
    - [ ] **1.10.3. Endpoints API pour Configuration UI**:
        - [ ] Créer des endpoints pour que l'UI React puisse lire/écrire les configurations du bot stockées dans `app/config.py` (via des méthodes de `Config` qui lisent/écrivent dans un fichier de config utilisateur ou `.env`).
    - [ ] **1.10.4. Servir l'Application React (Optionnel, si pas géré par Nginx dans Docker)**:
        - [ ] Configurer FastAPI pour servir les fichiers statiques de l'application React buildée si une solution Nginx dédiée n'est pas utilisée en production.
    - [ ] **1.10.5. Endpoints API REST Clés pour Actions Utilisateur et Sécurité (Nouveau)**:
        - [ ] **Objectif**: Définir les endpoints API REST que le frontend React utilisera pour les actions utilisateur et clarifier la sécurisation.
        - [ ] **Endpoints (Exemples à implémenter dans `app/api_routes.py` ou équivalent)**:
            - [ ] `POST /api/v1/bot/start`: Démarre le bot.
            - [ ] `POST /api/v1/bot/stop`: Arrête le bot.
            - [ ] `POST /api/v1/bot/pause`: Met le bot en pause.
            - [ ] `GET /api/v1/config`: Récupère la configuration actuelle du bot (parties non sensibles).
            - [ ] `POST /api/v1/config`: Met à jour la configuration du bot (avec validation rigoureuse).
            - [ ] `POST /api/v1/trades/manual`: Permet à l'utilisateur de soumettre un ordre manuel.
            - [ ] `GET /api/v1/trades/history?limit=50&offset=0`: Récupère l'historique des trades.
            - [ ] `GET /api/v1/ai/decisions/history?limit=50&offset=0`: Récupère l'historique des décisions de l'IA.
            - [ ] `GET /api/v1/portfolio/snapshot`: Récupère un snapshot complet du portefeuille.
            - [ ] `GET /api/v1/logs?service_name=<service>&limit=100`: Récupère les logs pour un service spécifique.
            - [ ] `GET /api/v1/system/health`: Récupère l'état de santé agrégé des services.
        - [ ] **Sécurité**:
            - [ ] Tous les endpoints API REST seront sécurisés en utilisant des tokens JWT fournis par Clerk/Auth0 (ou le fournisseur d'identité choisi).
            - [ ] FastAPI utilisera un middleware ou des dépendances pour valider le token JWT présent dans l'en-tête `Authorization` de chaque requête.
            - [ ] La connexion Socket.io sera également authentifiée lors du handshake initial, potentiellement en passant le token JWT et en le validant côté serveur avant d'autoriser la connexion persistante.
            - [ ] Des rôles et permissions (si définis dans Clerk/Auth0) pourraient être utilisés pour contrôler l'accès à certains endpoints sensibles.
- [ ] **1.11. `requirements.txt` (Ajouts pour Backend UI)**
    - [ ] Ajouter `python-socketio`.
    - [ ] Ajouter `python-jose[cryptography]` et `passlib[bcrypt]` pour la gestion JWT si Clerk/Auth0 en a besoin côté backend ou si une authentification locale est envisagée en complément.
    - [ ] Ajouter `fastapi-limiter` pour la limitation de taux sur les API.
- [ ] **1.12. `Docker/` (Mises à Jour pour UI React)**
    - [ ] **1.12.1. `Docker/frontend/Dockerfile` (Nouveau)**:
        - [ ] Créer un `Dockerfile` pour l'application React (`numerusx-ui/`).
        - [ ] Utiliser une multi-stage build:
            -   Stage 1: Node.js pour installer les dépendances (`npm install`) et builder l'application React (`npm run build`).
            -   Stage 2: Nginx (ou un autre serveur web léger) pour servir les fichiers statiques générés par le build React.
        - [ ] S'assurer que les variables d'environnement nécessaires à l'UI React (ex: URL du backend API/Socket.io) peuvent être configurées au moment du build ou du run.
    - [ ] **1.12.2. `docker-compose.yml` (Mise à Jour)**:
        - [ ] Ajouter un nouveau service `frontend` basé sur `Docker/frontend/Dockerfile`.
        - [ ] Configurer le port mapping pour le service frontend (ex: `80:80` ou `3000:80`).
        - [ ] S'assurer que le service backend (`app`) est accessible depuis le service frontend (gestion des réseaux Docker, ex: en utilisant les noms de service comme hostnames).
        - [ ] Mettre en place des volumes pour le développement local si nécessaire (ex: monter le code source de React pour le hot-reloading avec Vite pendant le dev, différent du build de prod).
        - [ ] **Gestion des Variables d'Environnement**: Utiliser un fichier `.env` à la racine du projet NumerusX, qui sera implicitement chargé par `docker-compose up` ou explicitement défini via `env_file` dans `docker-compose.yml`. Chaque service pourra alors accéder aux variables nécessaires (ex: `REACT_APP_BACKEND_URL` pour le frontend, `GOOGLE_API_KEY` pour le backend) via la section `environment` de sa définition de service ou directement injectées lors du build du conteneur si ce sont des arguments de build.
    - [ ] **1.12.3. `Docker/backend/Dockerfile` ou `Dockerfile` racine (Ajustements)**:
        - [ ] Vérifier que le backend FastAPI expose correctement le port pour l'API et Socket.io.
        - [ ] S'assurer que les variables d'environnement pour la communication avec le frontend sont gérées.
    - [ ] **1.12.4. Configuration Nginx indicative pour le Frontend (Nouveau)**:
        - [ ] **Objectif**: Fournir un exemple de configuration Nginx pour servir l'application React et gérer le proxy vers le backend.
        - [ ] **Exemple de `nginx.conf` (ou partie pertinente dans `Docker/frontend/Dockerfile` ou un fichier de conf séparé copié dans l'image Nginx)**:
            ```nginx
            server {
                listen 80;
                server_name localhost; # Ou le domaine approprié

                root /usr/share/nginx/html; # Où les fichiers buildés de React sont copiés
                index index.html index.htm;

                # Servir les fichiers statiques React
                location / {
                    try_files $uri $uri/ /index.html;
                }

                # Proxy pour les appels API vers le backend FastAPI
                location /api {
                    proxy_pass http://backend:8000; # 'backend' est le nom du service Docker backend, 8000 son port
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header X-Forwarded-Proto $scheme;
                }

                # Proxy pour les connexions WebSocket vers le backend FastAPI
                location /socket.io {
                    proxy_pass http://backend:8000/socket.io; # Assumant que le backend expose Socket.io sur le même port
                    proxy_http_version 1.1;
                    proxy_set_header Upgrade $http_upgrade;
                    proxy_set_header Connection "upgrade";
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                }
            }
            ```
        - [ ] Cette configuration Nginx doit être adaptée en fonction du port exposé par le backend FastAPI et du nom du service backend dans `docker-compose.yml`.
- [x] **1.13. Suppression de `app/dashboard.py` et `app/gui.py`**
    - [x] Supprimer ces fichiers car l'UI est maintenant gérée par l'application React externe.

## Phase 2: Développement du Cœur Agentique IA et Intégrations 🧠🤖

L'objectif principal de cette phase est de construire l'Agent IA central et de réorienter les modules existants pour l'alimenter.

### 2.1. Conception et Implémentation de l'Agent IA (`app/ai_agent.py`)
- [ ] **Tâche**: Créer la classe `AIAgent` dans `app/ai_agent.py`.
- [ ] **Détails**:
    - [ ] Définir la structure de base de `AIAgent`.
    - [ ] Implémenter la méthode principale de prise de décision (ex: `decide_trade(self, aggregated_inputs: Dict) -> Dict`).
        - [ ] `aggregated_inputs` contiendra toutes les données de `MarketDataProvider`, `PredictionEngine`, signaux des stratégies, `RiskManager`, `SecurityChecker`, `PortfolioManager`.
        - [ ] L'output sera un dictionnaire structuré représentant l'ordre final (action, paire, montant, SL/TP, type d'ordre) ou une décision de non-action, incluant un "raisonnement".
    - [ ] Initialiser avec `Config`.
    - [ ] Mettre en place une journalisation détaillée des inputs reçus et des décisions prises par l'agent.
- [ ] **Fichiers concernés**: `app/ai_agent.py` (nouveau), `app/config.py`.

### 2.2. Refactorisation de `app/dex_bot.py` en Orchestrateur de Flux pour l'Agent IA
- [🚧] **Tâche**: Modifier `DexBot` pour qu'il collecte les données et les transmette à l'`AIAgent`, puis exécute la décision de l'Agent.
- [x] **Détails**:
    - [x] `DexBot` initialise `AIAgent`.
    - [x] La méthode `_run_cycle` (ou équivalent) doit :
        - [x] Collecter les données de `MarketDataProvider`.
        - [x] Obtenir les analyses/signaux de `StrategySelector` (qui fournit les outputs des stratégies de `app/strategies/` et `app/analytics_engine.py`).
        - [x] Obtenir les prédictions de `PredictionEngine`.
        - [x] Obtenir les contraintes de `RiskManager`, `SecurityChecker`, et l'état de `PortfolioManager`.
        - [x] Agréger tous ces inputs dans un format structuré.
        - [x] Appeler `self.ai_agent.decide_trade(aggregated_inputs)`.
        - [x] Si l'agent retourne un ordre, le transmettre à `TradeExecutor` (qui utilisera `TradingEngine` avec le nouveau `JupiterApiClient`).
        - [x] Journaliser la décision et le raisonnement de l'agent.
    - [x] Supprimer l'ancienne logique de `_analyze_and_generate_signals` et `_execute_signals` qui prenait des décisions directes.
- [ ] **Détails (Jupiter Ordres Avancés)**:
    - [ ] Si l'Agent IA décide de placer des ordres limités ou DCA, `DexBot` (ou `AIAgent` lui-même) doit pouvoir construire les `params_dict` nécessaires et initier ces actions via les nouvelles méthodes de `TradingEngine` (ex: `place_limit_order`, `create_dca_plan`).
- [x] **Fichiers concernés**: `app/dex_bot.py`, `app/ai_agent.py`.

### 2.3. Adaptation des Modules Fournisseurs d'Inputs pour l'Agent IA
- [🚧] **Tâche**: S'assurer que `StrategyFramework`, `PredictionEngine`, `RiskManager`, `SecurityChecker` et `PortfolioManager` fournissent leurs informations dans un format consommable par `DexBot` pour l'`AIAgent`.
- [x] **Détails**:
    - [x] **`StrategyFramework` et `app/strategies/*`, `app/analytics_engine.py`**: Leurs méthodes `analyze` et `generate_signal` retournent des données structurées (features, scores, indicateurs) plutôt que des décisions de trade directes. Ces données deviennent des inputs pour l'`AIAgent`.
    - [x] **`PredictionEngine`**: Les prédictions (prix, régime, sentiment) sont formatées pour être facilement intégrées dans les `aggregated_inputs` de l'`AIAgent`.
    - [x] **`RiskManager`**: Fournit des limites de risque, des calculs de taille de position potentielle maximale comme contraintes/informations.
    - [x] **`SecurityChecker`**: Fournit des scores/alertes de sécurité.
    - [x] **`PortfolioManager`**: Fournit l'état actuel du portefeuille.
- [ ] **Détails (Compatibilité Jupiter)**:
    - [ ] Vérifier la compatibilité des formats de données retournés par `MarketDataProvider` (maintenant enrichi par `JupiterApiClient` pour les prix, infos tokens, quotes) avec les modules d'analyse (`analytics_engine.py`, stratégies) et l'Agent IA. Les décimales des tokens, par exemple, sont cruciales.
- [x] **Fichiers concernés**: `app/strategy_framework.py`, `app/strategies/*`, `app/analytics_engine.py`, `app/prediction_engine.py`, `app/risk_manager.py`, `app/security/security.py`, `app/portfolio_manager.py`.

### 2.4. Intégration du Raisonnement de l'Agent dans la Base de Données et l'UI
- [ ] **Tâche**: Stocker le "raisonnement" de l'Agent IA et l'afficher dans le dashboard (`numerusx-ui/`).
- [ ] **Détails**:
    - [ ] Modifier `EnhancedDatabase` pour avoir une table ou une colonne pour stocker les logs de décision de l'Agent IA (inputs clés considérés, logique appliquée, score de confiance, décision finale).
    - [ ] `DexBot` enregistre ce raisonnement après chaque décision de l'`AIAgent`.
    - [ ] **`numerusx-ui/` (Application React)**: (Les fonctionnalités UI sont détaillées dans `todo/01-todo-ui.md`)
        - [ ] Implémenter les sections/composants nécessaires dans l'UI React pour afficher le raisonnement derrière chaque trade (ou décision de ne pas trader) et l'état actuel de l'Agent IA, en se basant sur les spécifications de `todo/01-todo-ui.md`.
- [ ] **Fichiers concernés**: `app/database.py`, `app/dex_bot.py`, `numerusx-ui/` (et ses composants), `todo/01-todo-ui.md`.

## Phase 3: Logique de Trading Raffinée et Améliorations du Bot (Post-Agent IA) ⚙️

### 3.1. Amélioration des Inputs pour l'Agent IA (Anciennement Intégration Moteur Prédiction)
- [🚧] **Tâche**: Assurer que `prediction_engine.py` fournit des inputs de haute qualité à l'Agent IA. (Déjà marqué comme fait, mais vérifier pertinence/format pour l'Agent)
- [ ] **Détails**:
    - [ ] L'Agent IA consomme directement les outputs de `prediction_engine`.
- [ ] **Fichiers concernés**: `app/dex_bot.py` (orchestration), `app/prediction_engine.py` (fournisseur), `app/ai_agent.py` (consommateur).

### 3.2. Utilisation des Outputs du `RiskManager` par l'Agent IA (Anciennement Intégration Gestionnaire Risques)
- [🚧] **Tâche**: S'assurer que l'Agent IA utilise les informations de `risk_manager.py`. (Déjà marqué comme fait, mais vérifier l'intégration avec l'Agent)
- [ ] **Détails**:
    - [ ] `RiskManager.calculate_position_size()` peut être appelé par l'Agent IA comme une heuristique ou une contrainte.
    - [ ] L'Agent IA reçoit les limites d'exposition, etc., comme inputs.
- [ ] **Fichiers concernés**: `app/dex_bot.py` (orchestration), `app/risk_manager.py` (fournisseur), `app/ai_agent.py` (consommateur).

### 3.3. Logique d'Exécution et Suivi Post-Décision de l'Agent IA (`app/trade_executor.py`)
- [🚧] **Tâche**: Assurer une exécution et un suivi robustes des ordres de l'Agent IA via `TradingEngine` (utilisant `JupiterApiClient`).
- [x] **Détails**:
    - [x] `TradeExecutor` gère l'exécution des ordres de l'Agent IA, en appelant les méthodes appropriées de `TradingEngine` (ex: `execute_swap`, et les nouvelles `place_limit_order`, `create_dca_plan`).
    - [x] S'assurer que `TradeExecutor.execute_agent_order` est compatible avec les signatures de méthodes mises à jour de `TradingEngine` et peut passer les `params_dict` pour les ordres limités/DCA.
    - [x] `PortfolioManager` suit les positions résultantes.
    - [ ] La gestion des erreurs et reintentions spécifiques aux trades doit informer l'Agent IA pour d'éventuels ajustements futurs.
- [x] **Fichiers concernés**: `app/trade_executor.py`, `app/portfolio_manager.py`, `app/ai_agent.py`, `app/trading/trading_engine.py`.

## Phase 4: Interface Utilisateur et Fonctionnalités Avancées (Post-Agent IA) ✨

Cette phase vise à enrichir l'expérience utilisateur et à introduire des capacités de trading plus sophistiquées.

### 4.1. Amélioration de l'Interface Utilisateur (`numerusx-ui/`)
- [ ] **Tâche**: Développer les fonctionnalités du tableau de bord React comme défini dans `todo/01-todo-ui.md`.
- [ ] **Détails**: Se référer à `todo/01-todo-ui.md` pour la liste complète des fonctionnalités et des étapes de développement de l'interface React.
- [ ] **Fichiers concernés**: `numerusx-ui/` (ensemble du projet frontend), `todo/01-todo-ui.md`.

### 4.2. Implémentation de Stratégies de Trading Novatrices
- [x] **Tâche**: Développer et intégrer plusieurs archétypes de stratégies.
- [x] **Détails**:
    - [x] **Framework de Stratégie (`BaseStrategy`)**: Définir une classe `BaseStrategy` dans `app/strategy_framework.py` avec des méthodes communes (`analyze`, `generate_signal`, `get_parameters`, `get_name`).
    - [x] **Stratégie de Momentum (`MomentumStrategy`)**: Créer `app/strategies/momentum_strategy.py`. Implémenter une stratégie basée sur RSI et MACD.
    - [x] **Stratégie de Mean Reversion (`MeanReversionStrategy`)**: Créer `app/strategies/mean_reversion_strategy.py`. Implémenter une stratégie basée sur les Bandes de Bollinger.
    - [x] **Système de sélection de stratégie (`StrategySelector`)**: Développer une classe `StrategySelector` dans `app/strategy_selector.py`. Permettre à `DexBot` d'utiliser différentes stratégies (via `StrategySelector`) en fonction des conditions de marché ou d'une configuration. Initialement, implémenter une sélection simple (ex: par défaut ou via `Config`). (DONE: Selector created, DexBot uses it for default strategy from Config. *Note: L'implémentation actuelle du `StrategySelector` charge une stratégie par défaut. L'objectif à terme, comme décrit dans `0-architecte.md`, est que `StrategySelector` puisse pré-sélectionner/filtrer un ensemble de signaux ou de stratégies pour l'AIAgent, et non pas seulement en sélectionner une unique.*)
    - [x] **Stratégie de Suivi de Tendance (`TrendFollowingStrategy`)**: Créer `app/strategies/trend_following_strategy.py`. Utiliser des moyennes mobiles (EMA, SMA) et potentiellement ADX.
    - [x] **Intégration et tests initiaux**: S'assurer que `DexBot` peut charger et exécuter ces stratégies. Mettre à jour `AdvancedTradingStrategy` pour qu'elle hérite de `BaseStrategy` et s'intègre dans ce framework. (DONE for Advanced, Momentum, MeanReversion, TrendFollowing; DexBot loads default via Selector)
- [x] **Fichiers concernés**: `app/strategy_framework.py`, `app/strategies/`, `app/dex_bot.py`, `app/config.py`, `app/strategy_selector.py`.

### 4.3. Boucle de Confirmation par IA pour les Trades (OBSOLETE/REMPLACÉ PAR AGENT IA CENTRAL)
- [ ] **Tâche**: ~~Intégrer une étape finale de validation par une IA rapide avant l'exécution d'un trade.~~
- [ ] **Détails**: L'Agent IA est maintenant le décideur central. Ce concept est fusionné dans la logique de l'`