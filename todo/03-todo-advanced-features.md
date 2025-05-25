# NumerusX - Évolutions Stratégiques & IA Avancée 🧠💡

**Prompt pour l\'IA**: Analyse les propositions d\'évolution suivantes. Pour chaque feature, évalue sa faisabilité technique dans le contexte du projet NumerusX, son potentiel d\'amélioration des performances de trading, et propose une ébauche des étapes d\'implémentation. L\'objectif est de maximiser la rentabilité en explorant des approches innovantes.

## I. Compréhension Profonde du Marché & Modélisation Causale

### 1.1. Moteur d\'Analyse Causale des Mouvements de Marché (MAC-MM)
- [ ] **Feature**: Développer un système capable d\'identifier les relations de cause à effet entre divers événements (macro-économiques, actualités spécifiques à un projet, mouvements de gros portefeuilles, mises à jour de protocoles, changements réglementaires) et les fluctuations de prix des tokens.
- [ ] **Objectif**: Aller au-delà de la corrélation pour comprendre les *pourquoi* des mouvements, permettant des prédictions plus robustes et des stratégies proactives.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Collecte de Données Hétérogènes**: Agréger des flux de news (API spécialisées crypto, Google News), données on-chain (Glassnode, Nansen si API disponibles, sinon via explorateurs), calendriers économiques, annonces de projets (blogs, Discord, Twitter).
    - [ ] **NLP Avancé pour l\'Extraction d\'Événements**: Utiliser des LLMs pour extraire des entités, des sentiments et des relations causales implicites à partir de textes non structurés.
        - [ ] **Modélisation Thématique (Topic Modeling, ex: LDA, NMF)** des actualités et rapports financiers pour identifier des thèmes sous-jacents (ex: \'risques réglementaires\', \'innovation produit\', \'problèmes de chaîne d\'approvisionnement\') et suivre leur évolution comme signaux prédictifs. (Outils: `gensim`, `scikit-learn`)
    - [ ] **Modélisation par Graphes de Connaissance (Knowledge Graphs)**: Construire un graphe où les nœuds sont des événements, des tokens, des acteurs du marché, et les arêtes représentent leurs relations (causalité, influence, temporalité).
    - [ ] **Inférence Causale**: Appliquer des techniques d\'inférence causale (ex: réseaux bayésiens dynamiques, modèles de DoWhy/CausalML) pour quantifier l\'impact probable d\'un nouvel événement sur les prix.
    - [ ] **Intégration au `prediction_engine`**: Les signaux causaux viendraient enrichir les features ou moduler la confiance des prédictions ML.
    - [ ] **Intégration Prévue avec AIAgent**:
        -   Le MAC-MM produira un output structuré qui sera inclus dans `aggregated_inputs`.
        -   Cet output pourrait être une liste d'événements causaux pertinents ou un score d'impact causal global.
        -   **Structure dans `aggregated_inputs`**:
            ```json
            "causal_analysis_insights": {
                "active_causal_events": [
                    {
                        "event_id": "uuid_event_1",
                        "event_type": "MACRO_ECONOMIC_RELEASE", // e.g., INTEREST_RATE_DECISION, CPI_REPORT
                        "source": "EconomicCalendarX",
                        "description": "US Federal Reserve increases interest rates by 0.25%",
                        "detected_at_utc": "2023-11-15T18:05:00Z",
                        "expected_impact_on_target_pair": { // e.g., SOL/USDC
                            "direction": "NEGATIVE", // NEGATIVE, POSITIVE, NEUTRAL, UNCERTAIN
                            "magnitude": "MEDIUM", // LOW, MEDIUM, HIGH
                            "confidence": 0.70, // Confidence in this impact assessment
                            "time_horizon_hours": 24,
                            "reasoning_snippet": "Higher interest rates typically strengthen USD, potentially pressuring SOL."
                        },
                        "related_assets_potentially_affected": ["BTC", "ETH"]
                    },
                    {
                        "event_id": "uuid_event_2",
                        "event_type": "PROJECT_SPECIFIC_NEWS", // e.g., MAINNET_LAUNCH, PARTNERSHIP_ANNOUNCEMENT, SECURITY_BREACH
                        "source": "SolanaProjectBlog",
                        "description": "Project Y on Solana announces major partnership with Company Z.",
                        "detected_at_utc": "2023-11-15T10:00:00Z",
                        "expected_impact_on_target_pair": {
                            "direction": "POSITIVE",
                            "magnitude": "LOW",
                            "confidence": 0.85,
                            "time_horizon_hours": 48,
                            "reasoning_snippet": "Positive news for Project Y may indirectly benefit SOL ecosystem sentiment."
                        }
                    }
                ],
                "overall_causal_pressure_on_target_pair": "SLIGHTLY_NEGATIVE", // AGGREGATED_VIEW: STRONG_POSITIVE, POSITIVE, SLIGHTLY_POSITIVE, NEUTRAL, SLIGHTLY_NEGATIVE, NEGATIVE, STRONG_NEGATIVE
                "last_updated_utc": "2023-11-15T18:10:00Z"
            }
            ```
    - [ ] **Adaptation du Prompt Gemini**:
        -   Le prompt de l'AIAgent inclura une section "CAUSAL ANALYSIS INSIGHTS" si des données sont disponibles.
        -   Exemple d'instruction pour Gemini: "Consider the following causal analysis insights. These represent identified external events and their potential market impact. Factor these into your overall decision, noting their specified confidence and time horizon. Prioritize events with higher confidence and relevance to the target pair."
        -   Gemini devra évaluer comment ces événements externes (souvent qualitatifs) modifient les signaux plus quantitatifs issus des indicateurs techniques ou des prédictions de prix.

### 1.2. Modélisation de la Liquidité Dynamique et Prédiction d\'Impact
- [ ] **Feature**: Créer un modèle prédictif pour l\'évolution de la liquidité des pools (sur Jupiter/Raydium) et l\'impact sur les prix des transactions de différentes tailles *avant* leur exécution.
- [ ] **Objectif**: Optimiser l\'exécution des trades en anticipant les glissements (slippage) importants et en identifiant les moments optimaux pour trader en fonction de la profondeur du marché. Éviter les "thin liquidity traps".
- [ ] **Méthodologie Potentielle**:
    - [ ] **Analyse en Temps Réel des Carnets d\'Ordres (LOB - Level 2/3 si API le permettent)**:
        - [ ] Analyser la profondeur complète du LOB, la taille et le timing des ordres.
        - [ ] Étudier l\'interaction entre les ordres limites et au marché.
        - [ ] Utiliser l\'apprentissage automatique (ex: SVM, LSTMs simplifiés avec `scikit-learn`, `TensorFlow/Keras`) pour découvrir des modèles de déséquilibre complexes indicatifs des mouvements de prix futurs.
        - [ ] **Ingénierie de caractéristiques spécifique au LOB**: Déséquilibres pondérés en fonction de la profondeur, taux de changement du déséquilibre, taux d\'absorption des gros ordres.
    - [ ] **Apprentissage sur Données Historiques de Liquidité**: Entraîner un modèle (séries temporelles, ex: LSTM) sur l\'historique des snapshots de liquidité des pools pour prédire leur état à court terme.
    - [ ] **Simulation d\'Impact de Prix**: Développer un simulateur plus fin que la simple API `get_quote` de Jupiter, en considérant la structure actuelle du pool et les transactions récentes.
    - [ ] **Intégration au `trading_engine`**: Le moteur pourrait ajuster la taille de l\'ordre ou le fractionner en plusieurs petits ordres (TWAP/VWAP adaptatif) en fonction de la liquidité prédite et du déséquilibre détecté.
    - [ ] **Intégration Prévue avec AIAgent**:
        -   Les prédictions de liquidité et d'impact de prix seront fournies à l'AIAgent.
        -   Ces informations aideront l'AIAgent à décider non seulement *si* trader, mais aussi *comment* (taille, urgence).
        -   **Structure dans `aggregated_inputs`**:
            ```json
            "liquidity_and_impact_analysis": {
                "target_pair": "SOL/USDC",
                "current_liquidity_state": { // For various potential trade sizes
                    "size_5000_usd": { "estimated_slippage_bps": 5, "expected_fill_price": 165.22, "liquidity_rating": "GOOD" },
                    "size_50000_usd": { "estimated_slippage_bps": 25, "expected_fill_price": 164.90, "liquidity_rating": "MODERATE" },
                    "size_200000_usd": { "estimated_slippage_bps": 150, "expected_fill_price": 162.00, "liquidity_rating": "POOR_WARNING" }
                },
                "predicted_liquidity_trend_1h": "STABLE", // IMPROVING, STABLE, DETERIORATING
                "optimal_execution_time_window_minutes": 15, // Suggested window for better execution based on predicted liquidity flows
                "last_updated_utc": "2023-11-15T18:00:00Z"
            }
            ```
    - [ ] **Adaptation du Prompt Gemini**:
        -   Section: "LIQUIDITY AND EXECUTION CONTEXT".
        -   Instruction: "The following data describes the current and predicted liquidity for the target pair. If you decide to trade, consider this information to recommend an execution strategy (e.g., if liquidity is poor for desired size, suggest HOLD or reducing trade size). Your `amount_usd` decision should be informed by the estimated slippage."
        -   Gemini peut utiliser ces données pour affiner `amount_usd`, ou même changer sa décision `BUY/SELL/HOLD` si l'impact de prix est trop important.

## II. Stratégies de Trading Agentiques et Adaptatives

### 2.1. Swarm Intelligence pour la Découverte de Stratégies Émergentes
- [ ] **Feature**: Mettre en place un système multi-agents où chaque "mini-bot" explore une micro-stratégie ou un ensemble de paramètres spécifique.
- [ ] **Objectif**: Découvrir de manière autonome des stratégies rentables ou des combinaisons de paramètres optimales qui ne seraient pas évidentes pour un humain.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Architecture Multi-Agent**: Utiliser une librairie comme `MASA` (Multi-Agent Serving Architecture) ou développer un système simple.
    - [ ] **Espace d\'Exploration**: Chaque agent se voit attribuer un sous-ensemble de l\'espace des stratégies (ex: variations de périodes d\'indicateurs, combinaisons de signaux, seuils de risque différents).
    - [ ] **Fonction de Fitness**: Définir une fonction de récompense basée sur la performance simulée (ex: Sharpe ratio, Profit Factor sur des données de backtest glissantes).
    - [ ] **Communication et Collaboration (Optionnel)**: Les agents pourraient partager des informations sur les features ou les conditions de marché qui semblent prometteuses.
    - [ ] **Sélection et Évolution**: Périodiquement, les stratégies (ou paramètres) les moins performantes sont éliminées, et les plus performantes sont "reproduites" avec de légères mutations, s\'inspirant des algorithmes génétiques.
    - [ ] **Meta-Stratégie**: Un agent "maître" pourrait agréger les signaux des meilleurs agents ou allouer dynamiquement du capital aux stratégies les plus performantes en temps réel.
    - [ ] **Intégration Prévue avec AIAgent**:
        -   **Option A (Signaux Directs)**: Les N meilleures stratégies du swarm fournissent leurs signaux individuels comme n'importe quelle autre stratégie dans `aggregated_inputs.signal_sources`.
            ```json
            // Dans aggregated_inputs.signal_sources
            {
                "source_name": "SwarmStrategy_Alpha_1337",
                "signal": "BUY",
                "confidence": 0.78,
                "indicators": {"custom_feature_1": 0.9, "custom_feature_2": "POSITIVE"},
                "reasoning_snippet": "Learned pattern X detected in current market.",
                "strategy_metadata": {"type": "swarm_learned", "backtest_sharpe_recent": 2.1}
            }
            ```
        -   **Option B (Signal Agrégé du Maître Swarm)**: L'agent maître du swarm fournit une recommandation de plus haut niveau.
            ```json
            // Nouvelle clé dans aggregated_inputs
            "swarm_intelligence_directive": {
                "overall_market_bias_from_swarm": "BULLISH_CONSOLIDATION",
                "top_performing_swarm_strategies_types": ["momentum_breakout", "volatility_contraction"],
                "recommended_action_based_on_swarm_consensus": "HOLD_WITH_CAUTION", // ou BUY, SELL
                "swarm_consensus_confidence": 0.65,
                "reasoning_snippet": "Majority of high-performing swarm agents suggest current conditions are not optimal for new entries despite some bullish undertones."
            }
            ```
    - [ ] **Adaptation du Prompt Gemini**:
        -   **Pour Option A**: "You will receive signals from `SwarmStrategy_` sources. These are dynamically evolved strategies. Evaluate them alongside other signals."
        -   **Pour Option B**: Section "SWARM INTELLIGENCE DIRECTIVE". Instruction: "A meta-agent analyzing a swarm of trading strategies provides the following directive. Use this as a high-level input to contextualize other signals. If the swarm consensus is strong, it may warrant greater attention."

### 2.2. "Shadow Trading" Dynamique Basé sur l\'Analyse Comportementale des Wallets Performants
- [ ] **Feature**: Identifier et suivre (sans copier directement les trades pour éviter le front-running) les comportements et stratégies implicites de portefeuilles historiquement très performants sur Solana.
- [ ] **Objectif**: S\'inspirer des "smart money" en modélisant leurs patterns de décision plutôt qu\'en copiant leurs trades.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Identification de Wallets Cibles**: Utiliser des outils d\'analyse on-chain (Nansen, Arkham si API, sinon via parsing d\'explorateurs) pour identifier des wallets avec un historique de ROI élevé et une gestion de risque apparente.
    - [ ] **Ingénierie Inverse des Stratégies**:
        - [ ] Analyser leurs transactions passées (types de tokens, timing des achats/ventes, interaction avec les protocoles DeFi, réaction aux événements de marché).
        - [ ] Tenter de déduire les indicateurs ou les logiques qu\'ils pourraient suivre (ex: accumulation pendant les phases de faible volatilité, vente sur pics de sentiment).
    - [ ] **Modélisation Comportementale**: Créer un modèle ML (ex: Hidden Markov Model, LSTMs avec attention) qui apprend à prédire la *prochaine action probable* d\'un wallet performant en fonction du contexte de marché.
    - [ ] **Génération de Signaux Inspirés**: Si le modèle prédit qu\'un wallet cible est susceptible d\'acheter un token X, et que les propres analyses de NumerusX corroborent un potentiel, un signal d\'achat pourrait être généré/renforcé.
    - [ ] **Filtre Éthique et de Risque**: Toujours appliquer les filtres de sécurité et de risque de NumerusX. Ne pas suivre aveuglément.
    - [ ] **Intégration Prévue avec AIAgent**:
        -   Les "signaux inspirés" du Shadow Trading alimenteront l'AIAgent.
        -   **Structure dans `aggregated_inputs`**:
            ```json
            // Potentiellement dans aggregated_inputs.signal_sources ou une section dédiée
            "shadow_trading_insights": {
                "watched_wallets_activity_summary": [ // Top N wallets ou ceux avec activité récente pertinente
                    {
                        "wallet_profile_id": "SmartMoney_Profile_A", // Anonymized profile
                        "recent_action_type_target_pair": "ACCUMULATION_SUSPECTED", // e.g. ACCUMULATION_SUSPECTED, DISTRIBUTION_STARTING, HOLDING_STRONG, PROFIT_TAKING
                        "confidence_in_action_type": 0.70,
                        "relevant_token": "SOL", // ou la paire spécifique
                        "action_timestamp_utc": "2023-11-15T14:00:00Z",
                        "reasoning_snippet": "Wallet Profile A has historically shown strong accumulation before upward trends for this asset class."
                    }
                ],
                "overall_shadow_signal_for_target_pair": "POTENTIAL_BUY_WINDOW", // POTENTIAL_BUY_WINDOW, CAUTION_SELL_PRESSURE_BUILDING, NEUTRAL_OBSERVE
                "confidence_in_shadow_signal": 0.60,
                "last_updated_utc": "2023-11-15T18:00:00Z"
            }
            ```
    - [ ] **Adaptation du Prompt Gemini**:
        -   Section: "SHADOW TRADING INSIGHTS".
        -   Instruction: "The following insights are derived from observing historically performant wallets. This is NOT a directive to copy trades but an additional contextual signal about potential market interest or sentiment from sophisticated actors. Correlate this with other data before making a decision."
        -   Gemini doit utiliser cette information comme une source de confirmation ou d'alerte, mais pas comme un signal de trading primaire.

## III. Optimisation Avancée de l\'Exécution et de la Gestion des Risques

### 3.1. Exécution Prédictive Anti-MEV (Miner Extractable Value)
- [ ] **Feature**: Développer des stratégies pour minimiser l\'impact négatif du MEV (sandwich attacks, front-running) sur les transactions de NumerusX.
- [ ] **Objectif**: Améliorer le prix d\'exécution effectif des trades.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Analyse du Mempool (si possible sur Solana)**: Surveiller les transactions en attente pour détecter les bots MEV potentiels ciblant des transactions similaires.
    - [ ] **Fractionnement Intelligent des Ordres**: Diviser les gros ordres en plus petits morceaux exécutés à des moments et via des routes légèrement différents pour réduire la signature MEV.
    - [ ] **Timing d\'Exécution Aléatoire/Optimisé**: Introduire une petite variabilité aléatoire dans le timing d\'envoi des transactions ou les envoyer pendant des périodes de congestion de blocs moins prévisibles.
    - [ ] **Utilisation de RPC Privés/Services Anti-MEV**: Intégrer des services comme Jito ou des RPC privés qui offrent une protection contre le MEV.
    - [ ] **Modèle de Prédiction MEV**: Entraîner un modèle pour prédire la probabilité qu\'une transaction soit ciblée par du MEV en fonction de sa taille, du token, du pool de liquidité et de l\'état actuel du réseau. Le `trading_engine` pourrait alors décider de retarder ou modifier la transaction.

### 3.2. Gestion de Portefeuille Basée sur l\'Apprentissage par Renforcement Profond (Deep RL)
- [ ] **Feature**: Utiliser un agent Deep RL pour optimiser dynamiquement l\'allocation du portefeuille entre différents tokens et stratégies, ainsi que pour ajuster les paramètres de risque globaux.
- [ ] **Objectif**: Maximiser le rendement ajusté au risque du portefeuille global de manière adaptative.
- [ ] **Méthodologie Potentielle**:
    - [ ] **État de l\'Agent**: Inclure la composition actuelle du portefeuille, les P&L, les métriques de risque (VaR, drawdown), les prédictions de marché du `prediction_engine`, le régime de marché.
    - [ ] **Espace d\'Actions**: Actions d\'allocation (augmenter/diminuer l\'exposition à certains tokens/stratégies), ajustement des seuils de stop-loss/take-profit globaux, modification du risque maximum par trade.
    - [ ] **Fonction de Récompense**: Combinaison du Sharpe ratio du portefeuille, du ROI, et pénalités pour les drawdowns excessifs ou la volatilité trop élevée.
    - [ ] **Algorithmes Deep RL**: Explorer des algorithmes comme A2C (Advantage Actor-Critic), PPO (Proximal Policy Optimization) ou DDPG (Deep Deterministic Policy Gradient) en utilisant des librairies comme `Stable Baselines3` ou `Ray RLlib`.
    - [ ] **Simulation et Entraînement Off-Policy**: Entraîner l\'agent dans un environnement de backtest simulé avant de le laisser prendre des décisions (même limitées) en live.

## IV. Personnalisation et Explicabilité de l\'IA

### 4.1. Générateur de "Rapports de Décision" par LLM
- [ ] **Feature**: Pour chaque décision de trade (ou non-trade significatif), générer un rapport concis en langage naturel expliquant les principaux facteurs qui ont conduit à cette décision.
- [ ] **Objectif**: Augmenter la transparence, permettre l\'audit des décisions de l\'IA, et faciliter l\'amélioration continue des stratégies.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Collecte des Données de Décision**: Agréger les signaux des indicateurs, les scores de confiance du `prediction_engine`, les outputs du `risk_manager`, et les éventuelles confirmations de l\'IA (de la todo précédente).
    - [ ] **Prompt Engineering pour LLM**: Concevoir un prompt structuré qui demande au LLM (ex: un modèle local léger ou une API externe rapide) de synthétiser ces informations en un paragraphe explicatif.
    - [ ] **Exemple de Rapport**: "Trade d\'achat initié sur SOL/USDC car : 1. RSI (1h) est sorti de la zone de survente (32.5). 2. Prédiction ML indique une probabilité de hausse de 75% dans les 4 prochaines heures. 3. Sentiment Twitter légèrement positif. 4. Risque de la position calculé à 0.8% du portefeuille, respectant le seuil max."
    - [ ] **Intégration à l\'UI**: Afficher ces rapports dans le dashboard à côté de chaque trade.

### 4.2. "Jumeau Numérique" du Marché pour Simulation Contre-Factuelle
- [ ] **Feature**: Créer un environnement de simulation haute-fidélité ("jumeau numérique") qui reproduit les dynamiques du marché Solana, incluant les mécanismes des DEX, les flux de transactions, et potentiellement le comportement d\'autres acteurs (simulés).
- [ ] **Objectif**: Tester des stratégies dans des conditions ultra-réalistes et effectuer des analyses contre-factuelles ("Que se serait-il passé si j\'avais agi différemment ?") pour l\'apprentissage par renforcement et l\'évaluation de stratégies.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Modélisation des Composants du Marché**:
        - [ ] Agent-Based Modeling (ABM) pour simuler différents types de traders (arbitragistes, market makers, investisseurs long terme, bots MEV).
        - [ ] Modèles de files d\'attente pour simuler la congestion du réseau et l\'impact sur les confirmations de transactions.
        - [ ] Reproduction des AMM (Automated Market Makers) de Jupiter/Raydium.
    - [ ] **Alimentation avec Données Réelles**: Calibrer le jumeau numérique en utilisant des données historiques et en temps réel de prix, volume, et liquidité.
    - [ ] **Interface de Simulation**: Permettre à NumerusX d\'interagir avec ce jumeau comme s\'il s\'agissait du marché réel.
    - [ ] **Cas d\'Usage**:
        - [ ] Entraînement plus sûr et plus rapide des agents RL.
        - [ ] Évaluation de la robustesse des stratégies face à des "cygnes noirs" simulés.
        - [ ] Optimisation fine des paramètres d\'exécution.

### 4.3. XAI (LIME, SHAP) pour Rendre les Modèles de Trading Transparents
- [ ] **Feature**: Utiliser des techniques d\'IA Explicable (XAI) comme LIME (Local Interpretable Model-agnostic Explanations) et SHAP (SHapley Additive exPlanations) pour comprendre et interpréter les prédictions des modèles de trading algorithmique complexes (boîtes noires).
- [ ] **Objectif**: Valider si le modèle apprend des relations financières logiques ou du bruit. Affiner les stratégies en identifiant les conditions où le modèle performe mal. Augmenter la confiance dans les modèles et aider à la conformité réglementaire.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Données**: Sorties (prédictions, probabilités) de n\'importe quel modèle de trading ML.
    - [ ] **Librairies (Python)**: `shap`, `lime`.
    - [ ] **Intégration**: Module d\'analyse post-prédiction pour les modèles du `PredictionEngine`. Les résultats peuvent être journalisés ou affichés dans l\'UI pour des trades spécifiques.
- [ ] **Complexité**: Conceptuel: Moyen / Implémentation: Moyen.

## V. Idées Innovantes (Source: DeepSeek)

### 5.1. Modélisation des Dynamiques de Liquidité par Réseaux de Neurones Graphiques (GNN)
- [ ] **Feature**: Modéliser les relations multi-échelles entre pools de liquidité sur Solana via des GNN, en considérant les pools comme des nœuds et les arbitrages comme des arêtes.
- [ ] **Objectif**: Détection d\'opportunités d\'arbitrage cross-pool invisibles aux méthodes linéaires, avec estimation des seuils de rentabilité après frais. Anticipation des "domino effects" lors de gros swaps. Capturer les inefficacités transitoires liées aux dépendances topologiques entre AMM.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Données**: Graphes dynamiques de liquidité (historique des APIs Jupiter/DEX).
    - [ ] **Librairies/Outils**: PyTorch Geometric, DGL pour GNN temps-réel.
    - [ ] **Entraînement**: Entraînement contrastif sur triplets de pools corrélés.
    - [ ] **Intégration**: Module d\'analyse de liquidité avancé, alimentant le `prediction_engine` ou le `trading_engine` pour des décisions d\'arbitrage ou d\'exécution.
- [ ] **Complexité**: Conceptuel 🔴 | Implémentation 🔴

### 5.2. Embeddings Sémantiques des Smart Contracts
- [ ] **Feature**: Générer des embeddings vectoriels des bytecodes des contrats intelligents via des modèles NLP (ex: CodeBERT) pour détecter des patterns de rug pulls ou de mécaniques tokenomiques innovantes.
- [ ] **Objectif**: Classification proactive des tokens à risque via l\'analyse sémantique de leur logique interne, avant même le déploiement sur chaîne ou les premières transactions suspectes. Identification de tokens avec des tokenomics potentiellement avantageuses.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Données**: Bytecodes des contrats (via API Solana ou explorateurs), historique de rug pulls et de tokens avec tokenomics spécifiques.
    - [ ] **Librairies/Outils**: Transformers (Hugging Face), HDBSCAN pour le clustering.
    - [ ] **Entraînement**: Fine-tuning de modèles comme CodeBERT sur des bytecodes Solana, entraînement d\'un classificateur sur les embeddings pour identifier les risques/opportunités.
    - [ ] **Intégration**: Au module `Security` pour enrichir l\'analyse de risque des tokens.
- [ ] **Complexité**: Conceptuel 🔴 | Implémentation 🟠

### 5.3. Stratégie Quantique-Inspirée par Optimisation à Champ Moyen (MFQ)
- [ ] **Feature**: Adapter les algorithmes d\'optimisation par champ moyen de la physique quantique pour gérer l\'allocation de portefeuille dans des marchés fortement corrélés et non ergodiques.
- [ ] **Objectif**: Gestion robuste des "black swan events" et des régimes de marché extrêmes via des superpositions probabilistes de positions, améliorant la résilience du portefeuille.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Framework**: Modèles à particules interactives, algorithmes d\'optimisation inspirés du recuit simulé quantique.
    - [ ] **Librairies/Outils**: JAX pour la différentiation automatique et les simulations haute performance.
    - [ ] **Entraînement**: Calibration des paramètres du modèle de champ moyen sur des données de crise historiques.
    - [ ] **Intégration**: Au `RiskManager` pour une allocation de portefeuille dynamique et pour informer des stop-loss "quantiques" (basés sur des probabilités de transition d\'état extrêmes).
- [ ] **Complexité**: Conceptuel 🔴 | Implémentation 🔴

### 5.4. Détection de Manipulation de Marché par Topologie Algébrique et/ou IA
- [ ] **Feature**: Utiliser la théorie des graphes persistants et l\'homologie computationnelle OU des modèles d\'Apprentissage Automatique (SVM, K-NN, Random Forests) pour identifier des patterns de manipulation de marché (wash trading, spoofing, layering) dans les carnets d\'ordres ou les flux de transactions.
- [ ] **Objectif**: Détection précoce de manipulations. Générer des signaux de trading contrariants en identifiant les manipulations en temps réel. Mesurer la "toxicité" du flux d\'ordres pour évaluer la pression manipulatrice.
- [ ] **Méthodologie Potentielle (Approche Topologique)**:
    - [ ] **Données**: Flux L2/L3 des carnets d\'ordres, historique des transactions.
    - [ ] **Librairies/Outils**: GUDHI, giotto-tda, Ripser pour l\'analyse topologique.
    - [ ] **Features**: Calculer les diagrammes de persistance, nombres de Betti, paysages de persistance.
- [ ] **Méthodologie Potentielle (Approche IA)**:
    - [ ] **Données**: Données d\'ordres et de transactions tick-by-tick.
    - [ ] **Ingénierie de caractéristiques HFT**: Taille de l\'ordre, distance par rapport au meilleur prix, taux d\'annulation, durée de vie de l\'ordre.
    - [ ] **Bibliothèques (Python)**: `scikit-learn` pour les modèles ML.
- [ ] **Intégration**: Module de surveillance du marché, alertant le `Security` module ou le `RiskManager`.
- [ ] **Complexité**: Conceptuel: Moyen-Élevé / Implémentation: Élevé (dû à la gestion des données HFT pour l\'IA).

### 5.5. Réseaux Neuro-Symboliques pour l\'Interprétation des Oracles
- [ ] **Feature**: Combiner des règles symboliques (ex: logique temporelle, contraintes de marché connues) avec des réseaux neuronaux pour évaluer la fiabilité des oracles de prix décentralisés (ex: Pyth, Switchboard) et leur impact sur les prix des DEX.
- [ ] **Objectif**: Anticiper les divergences oracle/DEX, exploiter les arbitrages résultants, et se prémunir contre les manipulations d\'oracles ou les défaillances.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Architecture**: Logic Tensor Networks (LTN) ou frameworks similaires permettant d\'injecter des connaissances logiques dans des modèles neuronaux.
    - [ ] **Données**: Historique des prix des oracles, historique des prix des DEX, données de transaction, état du réseau de l\'oracle (ex: nombre de validateurs, staking).
    - [ ] **Entraînement**: Entraîner le réseau à prédire la probabilité de déviation oracle/DEX ou la "qualité" du prix de l\'oracle.
    - [ ] **Intégration**: Au `PredictionEngine` pour affiner les prédictions de prix, et au `RiskManager` pour évaluer le risque lié à la fiabilité de l\'oracle pour un actif donné.
- [ ] **Complexité**: Conceptuel 🟠 | Implémentation 🔴

### 5.6. Métrique d\'Entropie Causale pour l\'Allocation Dynamique
- [ ] **Feature**: Mesurer le flux d\'information causale entre actifs via l\'entropie de transfert pour construire des portefeuilles résilients aux chocs systémiques et optimiser la diversification.
- [ ] **Objectif**: Minimiser les expositions latentes aux cascades de liquidité et aux contagions de marché lors de crises, en allant au-delà des matrices de corrélation classiques.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Méthode**: Calcul de l\'entropie de transfert (Transfer Entropy) entre les séries de rendements des actifs.
    - [ ] **Optimisation**: Construire un portefeuille qui minimise l\'entropie causale totale entrante ou maximise la diversification causale.
    - [ ] **Librairies/Outils**: PyIF, JIDT (via bindings Python si disponibles).
    - [ ] **Intégration**: Au `RiskManager` pour l\'allocation de portefeuille et la gestion de l\'exposition.
- [ ] **Complexité**: Conceptuel 🟠 | Implémentation 🟠

### 5.7. Modèle de Deep Hedging avec Contraintes Physiques
- [ ] **Feature**: Entraîner un réseau neuronal à couches différentiables qui intègre directement les équations fondamentales de la finance (ex: Black-Scholes pour les options, ou des modèles de parité pour les futures) comme contraintes physiques dans sa fonction de perte pour des stratégies de couverture.
- [ ] **Objectif**: Développer des stratégies de couverture (hedging) dynamiques et robustes pour les positions au comptant ou les positions LP, même dans des marchés incomplets où les hypothèses classiques ne tiennent pas.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Framework**: TensorFlow Probability, PyTorch avec des couches personnalisées pour la programmation différentiable.
    - [ ] **Données**: Flux de prix des actifs au comptant et des produits dérivés (options, futures sur Solana via des plateformes comme Zeta Markets, Mango Markets, etc.).
    - [ ] **Entraînement**: Entraîner le réseau à minimiser le risque de réplication d\'un payoff tout en respectant les contraintes financières.
    - [ ] **Intégration**: Au `RiskManager` pour le hedging automatique des positions du portefeuille ou des positions de LP si le bot s\'engage dans la fourniture de liquidité.
- [ ] **Complexité**: Conceptuel 🔴 | Implémentation 🔴

### 5.8. Cartographie des Mémoires des LLMs pour le Sentiment Multi-Échelle
- [ ] **Feature**: Analyser les patterns d\'activation des couches internes de grands modèles de langage (LLMs) lors du traitement de news crypto et de discussions communautaires pour extraire des signaux de sentiment et des thématiques émergentes à différentes échelles de temps (haute fréquence, moyen terme).
- [ ] **Objectif**: Détection de nuances sémantiques, d\'ironie, de narratifs en formation, et de signaux de sentiment plus profonds, qui sont souvent invisibles aux méthodes NLP classiques basées sur des lexiques ou des modèles de classification simples.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Modèles**: LLMs open-source quantifiés (ex: versions allégées de Llama, Mistral) pour un compromis vitesse/performance.
    - [ ] **Technique**: Extraction de features via "probing" des activations des couches cachées des LLMs, analyse de l\'attention.
    - [ ] **Librairies/Outils**: TransformerLens, PyTorch, bibliothèques d\'interprétabilité des LLMs.
    - [ ] **Entraînement**: Pas nécessairement un fine-tuning du LLM lui-même, mais plutôt l\'entraînement de modèles plus petits (sondes) sur les activations extraites.
    - [ ] **Intégration**: Au `PredictionEngine` (module `SentimentAnalyzer`) pour fournir des features de sentiment enrichies.
- [ ] **Complexité**: Conceptuel 🟠 | Implémentation 🟠

### 5.9. Algorithmes de Consensus Stochastiques pour l\'Agrégation de Stratégies
- [ ] **Feature**: Utiliser des mécanismes inspirés des algorithmes de consensus (ex: Proof-of-Stake probabiliste, sélection par tournois stochastiques) pour pondérer dynamiquement les signaux de stratégies hétérogènes (issues du `StrategyFramework` ou du Swarm Intelligence 2.1) en fonction de leur performance récente, de leur adéquation au régime de marché actuel, et de leur "vote" de confiance.
- [ ] **Objectif**: Créer un système de méta-stratégie auto-adaptatif, robuste à la sur-optimisation (overfitting) d\'une stratégie unique, et capable de s\'ajuster rapidement aux conditions de marché changeantes.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Mécanisme**: Chaque stratégie "vote" pour un trade avec une confiance. Les "votes" sont pondérés par la performance passée de la stratégie et un "stake" virtuel.
    - [ ] **Métriques**: Utiliser l\'entropie de Shannon des "votes" des stratégies pour mesurer la conviction du consensus.
    - [ ] **Implémentation**: Créer une classe `MetaStrategyAggregator`.
    - [ ] **Intégration**: Au `StrategyFramework` ou comme une surcouche au `DexBot` pour la décision finale de trading.
- [ ] **Complexité**: Conceptuel 🟠 | Implémentation 🟠

### 5.10. Réseaux Antagonistes Différentiables pour la Simulation de Marché
- [ ] **Feature**: Développer un Réseau Antagoniste Génératif (GAN) où le générateur apprend à produire des séquences de données de marché (prix, volume, liquidité) réalistes et complexes, et où le discriminateur, au lieu d\'être un simple classificateur, intègre des contraintes d\'absence d\'arbitrage via un solveur de Programmation Linéaire (LP) différentiable.
- [ ] **Objectif**: Générer des scénarios de marché synthétiques de haute fidélité, incluant des comportements adverses et rationnels, pour un backtesting plus robuste et pour l\'entraînement d\'agents RL (complétant le "Jumeau Numérique" 4.2).
- [ ] **Méthodologie Potentielle**:
    - [ ] **Architecture**: Utiliser des frameworks comme DiffCVX (pour les solveurs différentiables) avec PyTorch ou TensorFlow pour le GAN.
    - [ ] **Données**: Historique de marché enrichi d\'événements rares et de conditions de stress.
    - [ ] **Entraînement**: Le générateur essaie de tromper le discriminateur en produisant des données qui semblent réelles ET sans opportunités d\'arbitrage évidentes (selon le solveur LP).
    - [ ] **Utilisation**: Augmentation de données pour le `BacktestEngine` et pour l\'environnement de simulation du "Jumeau Numérique".
- [ ] **Complexité**: Conceptuel 🔴 | Implémentation 🔴

## VI. Idées Innovantes (Source: Manus)

### 6.1. Analyse Topologique des Données (TDA) pour la Détection de Régimes de Marché
- [ ] **Feature**: Appliquer la TDA pour étudier la "forme" des données financières multidimensionnelles, en se concentrant sur les propriétés topologiques (connectivité, trous) pour identifier des structures de marché complexes.
- [ ] **Objectif**: Détecter des changements subtils dans la structure topologique du marché avant qu\'ils ne se manifestent classiquement, anticipant ainsi les transitions de régimes de marché (tendance, range, volatilité) avec une précision accrue.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `giotto-tda`, `ripser`, `persim` pour le calcul d\'homologie persistante.
    - [ ] **Module dédié**: `topology_analyzer.py`.
        - [ ] Construire des complexes simpliciaux à partir des données de prix multi-actifs.
        - [ ] Calculer les diagrammes de persistance et les paysages de persistance.
        - [ ] Extraire des features topologiques.
    - [ ] **Intégration**: Alimenter le `prediction_engine.MarketRegimeClassifier` avec les features topologiques. Utiliser des fenêtres glissantes pour l\'analyse en temps réel.
- [ ] **Complexité**: Conceptuel: Élevé | Implémentation: Moyen

### 6.2. Inférence Causale Dynamique pour l\'Analyse des Flux d\'Ordres
- [ ] **Feature**: Utiliser des techniques d\'inférence causale pour découvrir et quantifier les relations de cause à effet entre les flux d\'ordres de différents types d\'acteurs du marché et les mouvements de prix.
- [ ] **Objectif**: Comprendre les véritables moteurs de prix plutôt que les simples corrélations. Détecter des "alpha" cachés en identifiant des chaînes causales spécifiques (ex: flux institutionnels -> réaction des market makers -> prix).
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `DoWhy`, `CausalNex`, `causal-learn`.
    - [ ] **Module dédié**: `causal_flow_analyzer.py`.
        - [ ] Construire et mettre à jour continuellement un graphe causal à partir des données de marché (carnet d\'ordres, flux de transactions).
        - [ ] Utiliser des méthodes comme les interventions contrefactuelles pour tester des hypothèses.
        - [ ] Quantifier la force des relations causales.
        - [ ] Utiliser des algorithmes comme FCI (Fast Causal Inference) ou NOTEARS.
- [ ] **Complexité**: Conceptuel: Élevé | Implémentation: Moyen-Élevé

### 6.3. Computing Neuromorphique pour le Trading Ultra-Basse Latence
- [ ] **Feature**: Explorer l\'utilisation de systèmes de calcul neuromorphique (inspirés du cerveau, utilisant des Spiking Neural Networks - SNNs) pour un traitement ultra-rapide et énergétiquement efficace des données de marché temporelles.
- [ ] **Objectif**: Réduire drastiquement la latence de prise de décision, essentiel dans les marchés crypto. Identifier des opportunités de trading éphémères.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `Norse`, `BindsNET`, `Nengo` pour la simulation de SNNs.
    - [ ] **Hardware (Optionnel/Exploratoire)**: Utilisation potentielle de hardware spécialisé comme Intel Loihi ou IBM TrueNorth (via cloud).
    - [ ] **Module dédié**: `neuromorphic_engine.py`.
        - [ ] Implémenter des SNNs pour l\'analyse en temps réel.
        - [ ] Utiliser l\'apprentissage par renforcement adapté aux SNNs.
    - [ ] **Déploiement**: Initialement comme système consultatif/parallèle.
- [ ] **Complexité**: Conceptuel: Moyen-Élevé | Implémentation: Élevé

### 6.4. Modélisation Multi-Agents Hétérogènes avec Apprentissage par Auto-Jeu
- [ ] **Feature**: Modéliser le marché comme un système complexe d\'agents hétérogènes (retail, institutionnels, market makers, etc.) et utiliser l\'apprentissage par auto-jeu (self-play) pour améliorer continuellement les stratégies.
- [ ] **Objectif**: Développer des stratégies robustes qui s\'adaptent aux comportements changeants des participants. Anticiper la "méta-game" et découvrir des stratégies contre-intuitives.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `AI-Economist`, `RLlib`, `PettingZoo`.
    - [ ] **Module dédié**: `market_simulator.py`.
        - [ ] Modéliser différentes classes d\'agents avec des comportements paramétrables.
        - [ ] Simuler leurs interactions dans un environnement de marché réaliste.
        - [ ] Utiliser des techniques d\'apprentissage par renforcement multi-agents et inspirées d\'AlphaZero.
    - [ ] **Calibration**: Calibrer les agents sur des données historiques réelles.
- [ ] **Complexité**: Conceptuel: Moyen | Implémentation: Élevé

### 6.5. Quantum-Inspired Optimization pour la Gestion de Portefeuille Adaptative
- [ ] **Feature**: Utiliser des algorithmes d\'optimisation inspirés du quantum computing (ex: Quantum Annealing simulé, QAOA) pour résoudre efficacement des problèmes d\'allocation de portefeuille complexes sur des ordinateurs classiques.
- [ ] **Objectif**: Trouver des allocations de portefeuille quasi-optimales plus rapidement que les méthodes classiques, permettant des ajustements fréquents et précis, améliorant le ratio rendement/risque.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `qiskit`, `D-Wave Ocean`, `QuTiP`.
    - [ ] **Module dédié**: `quantum_optimizer.py`.
        - [ ] Formuler le problème d\'allocation comme un QUBO (Quadratic Unconstrained Binary Optimization).
        - [ ] Implémenter des solveurs quantum-inspired.
        - [ ] Intégrer des contraintes dynamiques basées sur les prédictions de marché.
    - [ ] **Intégration**: Avec le `risk_manager.py` pour une approche hybride.
- [ ] **Complexité**: Conceptuel: Élevé | Implémentation: Moyen

### 6.6. Analyse des Microstructures de Marché par Transformers Spatio-Temporels
- [ ] **Feature**: Utiliser des architectures Transformer adaptées pour capturer simultanément les dépendances spatiales (entre actifs) et temporelles dans les microstructures de marché.
- [ ] **Objectif**: Identifier des inefficiences subtiles et éphémères en modélisant la propagation de l\'information à travers le réseau d\'actifs. Utile pour l\'arbitrage statistique et les relations lead-lag.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `PyTorch`, `Transformers`, `torch_geometric`.
    - [ ] **Module dédié**: `market_microstructure_analyzer.py`.
        - [ ] Construire des graphes dynamiques des relations entre actifs.
        - [ ] Implémenter des Transformers spatio-temporels.
        - [ ] Extraire des signaux d\'alpha.
    - [ ] **Données**: Tick-by-tick et carnet d\'ordres pour une granularité maximale.
    - [ ] **Intégration**: Avec le `prediction_engine` pour une approche multi-modèle.
- [ ] **Complexité**: Conceptuel: Moyen-Élevé | Implémentation: Moyen-Élevé

### 6.7. Détection d\'Anomalies par Apprentissage Contrastif Auto-Supervisé
- [ ] **Feature**: Utiliser l\'apprentissage contrastif auto-supervisé pour apprendre à distinguer les patterns de marché normaux des anomalies sans étiquettes explicites.
- [ ] **Objectif**: Détecter des configurations de marché inhabituelles (anomalies) qui pourraient signaler des inefficiences temporaires ou des mouvements imminents, et les exploiter.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `PyTorch`, `TensorFlow`, `PyOD`.
    - [ ] **Module dédié**: `anomaly_detector.py`.
        - [ ] Implémenter des techniques comme SimCLR ou BYOL adaptées aux données financières.
        - [ ] Construire un espace de représentation des conditions de marché normales.
        - [ ] Calculer des scores d\'anomalie en temps réel.
    - [ ] **Intégration**: Avec le système d\'alerte et de génération de signaux.
    - [ ] **Data Augmentation**: Utiliser des techniques d\'augmentation spécifiques aux séries temporelles financières.
- [ ] **Complexité**: Conceptuel: Moyen | Implémentation: Moyen

### 6.8. Analyse Sentiment-Flux par Traitement du Langage Naturel Multimodal
- [ ] **Feature**: Combiner l\'analyse textuelle (NLP) avec d\'autres modalités (données de marché, métriques on-chain, signaux sociaux) et modéliser la dynamique temporelle entre les changements de sentiment et les flux de capitaux.
- [ ] **Objectif**: Anticiper les mouvements de prix résultant de la dynamique sentiment-flux, particulièrement puissant dans les marchés crypto où le sentiment est un catalyseur rapide.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `transformers`, `pytorch`, `networkx`.
    - [ ] **Module dédié**: `sentiment_flow_analyzer.py`.
        - [ ] Collecter et analyser des données textuelles (Twitter, Discord, Reddit).
        - [ ] Construire un modèle de propagation du sentiment.
        - [ ] Corréler les changements de sentiment avec les flux on-chain et les prix.
    - [ ] **Modèles**: Utiliser des LLMs fine-tunés pour l\'analyse contextuelle crypto.
    - [ ] **Intégration**: Avec des APIs de données sociales et on-chain.
- [ ] **Complexité**: Conceptuel: Moyen | Implémentation: Moyen-Élevé

### 6.9. Optimisation Bayésienne pour le Meta-Learning des Hyperparamètres
- [ ] **Feature**: Utiliser l\'optimisation bayésienne pour ajuster automatiquement et continuellement les hyperparamètres de toutes les stratégies et modèles du système en fonction des conditions de marché changeantes.
- [ ] **Objectif**: Maintenir des performances optimales dans des conditions de marché dynamiques, en apprenant quels paramètres fonctionnent le mieux dans quels contextes, et éviter le sur-ajustement.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `GPyOpt`, `Optuna`, `Ax`.
    - [ ] **Module dédié**: `meta_optimizer.py`.
        - [ ] Définir un espace de recherche pour les hyperparamètres critiques.
        - [ ] Implémenter un processus gaussien pour modéliser la relation paramètres-performance.
        - [ ] Utiliser l\'acquisition bayésienne pour explorer l\'espace des paramètres.
    - [ ] **Intégration**: Avec un système de backtest rapide pour évaluation continue et boucle de feedback.
- [ ] **Complexité**: Conceptuel: Moyen | Implémentation: Moyen

### 6.10. Analyse Fractale Adaptative pour la Prédiction Multi-Échelle
- [ ] **Feature**: Exploiter la nature fractale des marchés financiers en analysant simultanément les patterns à différentes échelles temporelles et en modélisant explicitement les relations fractales entre ces échelles.
- [ ] **Objectif**: Obtenir une compréhension plus profonde de la structure du marché pour des prédictions plus robustes, intégrant des informations de multiples horizons temporels. Particulièrement utile pour identifier les points de retournement majeurs.
- [ ] **Méthodologie Potentielle**:
    - [ ] **Librairies/Outils**: `pywavelets`, `hurst`, `fractalai`.
    - [ ] **Module dédié**: `fractal_analyzer.py`.
        - [ ] Calculer des métriques fractales (exposant de Hurst, dimension fractale).
        - [ ] Implémenter une décomposition en ondelettes multi-résolution.
        - [ ] Détecter les divergences fractales entre échelles.
    - [ ] **Intégration**: Avec le `prediction_engine` pour une approche multi-modèle.
    - [ ] **Techniques**: Utilisation d\'analyse de singularité pour identifier les points critiques.
- [ ] **Complexité**: Conceptuel: Élevé | Implémentation: Moyen

---

# NumerusX - Remaining Advanced Features & Specifics (from original todo.md)

**Prompt pour l\'IA**: Ce fichier contient des spécifications détaillées pour des fonctionnalités avancées issues d\'une version précédente de la todo list. Utilise ces détails pour enrichir l\'implémentation des modules correspondants (`analytics_engine.py`, `risk_manager.py`, `trading_engine.py`, `strategy_framework.py`, `backtest_engine.py`, `market_maker.py`) comme spécifié dans `todo-ia.md` et `todo-features.md`. Ces tâches doivent être exécutées après la stabilisation de base du bot.

## 1. Dépendances à Vérifier/Ajouter (`requirements.txt`)
Lors de l\'implémentation du moteur de prédiction, s\'assurer que les dépendances suivantes (ou versions compatibles) sont présentes :
- [ ] `scikit-learn==1.0.2`
- [ ] `torch==1.13.1`
- [ ] `joblib==1.1.0`
- [ ] `gensim` (pour Topic Modeling)
- [ ] `shap` (pour XAI)
- [ ] `lime` (pour XAI)
- [ ] `PyPortfolioOpt` (pour HRP et autres optimisations)
- [ ] `Riskfolio-Lib` (pour HRP et autres optimisations)

## 2. Advanced Market Analysis Framework (`analytics_engine.py`)

-   [ ] **Analyse des flux On-Chain (Complément à `todo-features.md` I.1 & II.2)**:
    -   [ ] Implémenter `analyze_whale_activity(self, token_address: str) -> dict`:
        -   Analyse les grosses transactions (ex: >$10k) sur les dernières 24h.
        -   Utilise l\'API Solana Explorer pour récupérer ces transactions.
        -   Calcule le ratio achat/vente et le flux net.
        -   Retourne `{\'net_flow\': float, \'whale_sentiment\': str, \'risk_level\': int}`.
-   [ ] **Analyse Multi-Timeframe**:
    -   [ ] Modifier la méthode `_momentum_score` (ou équivalent) pour considérer plusieurs timeframes (ex: 1m, 5m, 15m, 1h, 4h).
    -   [ ] Créer une matrice de corrélation entre les timeframes pour identifier les divergences.
    -   [ ] Pondérer les signaux des différents timeframes en fonction du régime de marché actuel (détecté par `prediction_engine.MarketRegimeClassifier`).
-   [ ] **Analyse Avancée de la Structure des Prix**:
    -   [ ] Implémenter `identify_support_resistance(self, price_data: pd.DataFrame) -> list`:
        -   Utiliser l\'analyse du profil de volume pour trouver les nœuds à volume élevé.
        -   Identifier les fractales pour les points hauts/bas de swing.
        -   Calculer les niveaux de retracement de Fibonacci.
-   [ ] **Indicateurs d\'Efficience du Marché**:
    -   [ ] Ajouter le calcul de l\'Exposant de Hurst pour déterminer le caractère aléatoire ou tendanciel.
    -   [ ] Implémenter un ratio d\'efficience du marché.
    -   [ ] Créer un classificateur momentum/retour à la moyenne.
-   [ ] **Système de Scoring Adaptatif**:
    -   [ ] Modifier la méthode `generate_signal` pour ajuster les poids des différents facteurs d\'analyse en fonction du régime de marché.
    -   [ ] Augmenter les facteurs de momentum dans les marchés tendanciels.
    -   [ ] Favoriser le retour à la moyenne dans les marchés en range.

## 3. Sophisticated Risk Management System (`risk_manager.py`)

-   [ ] **Dimensionnement de Position Basé sur le Critère de Kelly**:
    -   [ ] Implémenter `calculate_position_size(self, win_rate: float, win_loss_ratio: float, account_size: float) -> float`:
        -   Prend en entrée : `win_rate` (taux de succès historique), `win_loss_ratio` (gain moyen / perte moyenne), `account_size`.
        -   Utilise la formule de Kelly : `f* = p - (1-p)/r`.
        -   Appliquer une fraction de Kelly (ex: demi-Kelly) pour la sécurité.
        -   Retourne la fraction du portefeuille à risquer, plafonnée par `Config.MAX_RISK_PER_TRADE`.
-   [ ] **Stop-Loss Dynamique Basé sur la Volatilité**:
    -   [ ] Calculer l\'Average True Range (ATR) pour l\'actif.
    -   [ ] Définir le stop-loss à un multiple de l\'ATR par rapport au prix d\'entrée.
    -   [ ] Ajuster en fonction des patterns de volatilité historiques.
-   [ ] **Contrôles de Risque au Niveau du Portefeuille**:
    -   [ ] Implémenter `check_correlation_risk(self, proposed_asset: str) -> bool`:
        -   Évalue si l\'ajout d\'un nouvel actif augmente le risque de corrélation du portefeuille.
        -   Calcule la corrélation entre l\'actif proposé et les positions existantes.
        -   Retourne `False` si l\'ajout dépasse un seuil de corrélation défini.
    -   [ ] Envisager l\'optimisation de portefeuille via la Théorie Moderne du Portefeuille (MPT).
    -   [ ] **Optimisation de Portefeuille par Parité de Risque Hiérarchique (HRP)**: Utiliser la théorie des graphes et le clustering hiérarchique pour une diversification structurelle du risque (Outils: `PyPortfolioOpt`, `Riskfolio-Lib`).
-   [ ] **Protection contre le Drawdown**:
    -   [ ] Implémenter un mécanisme de disjoncteur (circuit breaker) qui met en pause le trading après un drawdown de X%.
    -   [ ] Définir des règles basées sur le temps pour la reprise du trading après des pertes.
-   [ ] **Dimensionnement de Position Ajusté à la Volatilité (généralisation du stop-loss dynamique)**.
-   [ ] **Intégration avec `EnhancedDatabase`**:
    -   [ ] Enregistrer tous les calculs de risque dans la base de données pour analyse.
    -   [ ] Suivre les métriques de risque dans le temps pour identifier les tendances.
    -   [ ] Stocker les données de validation pour le backtesting.

## 4. High-Performance Execution Engine (`trading_engine.py`)

-   [ ] **Récupération Parallèle de Cotations**:
    -   [ ] Implémenter `async def get_quotes(self, mint_in: str, mint_out: str, amount: int) -> dict`:
        -   Récupère les cotations de plusieurs sources en parallèle (ex: Jupiter API principale, Raydium pour comparaison, Openbook en fallback).
        -   Utiliser `asyncio.gather`.
        -   Retourne la meilleure cotation basée sur le montant de sortie et la fiabilité.
-   [ ] **Optimisation des Frais de Transaction (Spécifique Solana)**:
    -   [ ] Implémenter `def estimate_fees(self, tx_data: dict) -> int` (peut être intégré à `get_fee_for_message` de `todo-ia.md` 1.5):
        -   Utilise la congestion actuelle du réseau (via `getPrioritizationFees`).
        -   Estime la taille de la transaction.
        -   Considère les données de frais récents historiques.
        -   Retourne le niveau de frais optimal en lamports.
    -   [ ] Ajouter des instructions de "compute budget" aux transactions.
    -   [ ] Inclure le calcul des "priority fees".
    -   [ ] Ajouter la compensation du "clock skew".
-   [ ] **Sélection d\'Algorithmes d\'Exécution (TWAP, VWAP, etc.)** (si pertinent pour les swaps simples sur Jupiter).
-   [ ] **Mesure et Optimisation de la Latence**.
-   [ ] **Batching de Transactions** (si applicable et bénéfique sur Solana pour les types de transactions effectuées).
-   [ ] **Mécanisme de Réessai Intelligent (détail pour `todo-ia.md` 1.5)**:
    -   [ ] Utiliser `@retry` de `tenacity` avec `wait_exponential`, `stop_after_attempt`, et `retry_if_exception_type((TimeoutError, ConnectionError))` pour `execute_transaction`.
-   [ ] **Stratégies de Protection MEV (détail pour `todo-features.md` III.1)**:
    -   [ ] Soumission de transactions privées via RPC (si disponible/efficace).
    -   [ ] Monitoring du slippage en temps réel pendant l\'exécution.
    -   [ ] Timing d\'exécution randomisé (petite variance).

## 5. Strategy Framework (`strategy_framework.py`)
En complément de `todo-ia.md` (Tâche 3.2):
-   [ ] **Définir l\'Interface de Base de Stratégie (`BaseStrategy`)**:
    -   [ ] `analyze(self, market_data: pd.DataFrame) -> dict`: Analyse les données de marché et retourne les résultats.
    -   [ ] `generate_signal(self, analysis: dict) -> dict`: Génère un signal de trading à partir de l\'analyse.
    -   [ ] `get_parameters(self) -> dict`: Retourne les paramètres de la stratégie.
-   [ ] **Implémenter des Exemples de Stratégies Concrètes**:
    -   [ ] `MomentumStrategy(BaseStrategy)`:
        -   Paramètres: `rsi_period=14`, `rsi_threshold=70`.
        -   `analyze`: Implémente l\'analyse de momentum avec RSI, MACD, action des prix.
-   [ ] **Créer un Sélecteur de Stratégie (`StrategySelector`)**:
    -   [ ] `select_strategy(self, market_data: pd.DataFrame) -> BaseStrategy`:
        -   Détermine la meilleure stratégie pour les conditions actuelles.
        -   Utilise la détection de régime de marché (`prediction_engine`).
        -   Considère la performance historique des stratégies.
        -   Retourne une instance de la stratégie sélectionnée.
-   [ ] **Suivi de Performance par Stratégie**:
    -   [ ] Suivre le ratio gain/perte pour chaque stratégie.
    -   [ ] Calculer le facteur de profit et le ratio de Sharpe pour chaque stratégie.
    -   [ ] Implémenter une rotation automatique des stratégies basée sur la performance (si `StrategySelector` n\'est pas suffisant).
-   [ ] **Framework pour Indicateurs Personnalisés**.
-   [ ] **Capacités de Combinaison de Stratégies**.
-   [ ] **Intégration avec `dex_bot.py`**:
    -   [ ] Remplacer l\'analytique codée en dur par le framework de stratégie.
    -   [ ] Ajouter une étape de sélection de stratégie à la boucle principale.

## 6. Advanced Order Types (`trading_engine.py`)

-   [ ] **Ordres Limites via API Jupiter**:
    -   [ ] `async def place_limit_order(self, mint_in: str, mint_out: str, amount: int, price_limit: float) -> dict`:
        -   Place un ordre limite en utilisant l\'API d\'ordres limites de Jupiter.
        -   Définit le prix max pour achat ou min pour vente.
        -   Retourne l\'ID de l\'ordre et son statut.
        -   Stocke l\'ordre dans la DB pour suivi.
-   [ ] **Fonctionnalité d\'Ordres DCA (Dollar Cost Averaging)**:
    -   [ ] `async def setup_dca_orders(self, mint_in: str, mint_out: str, total_amount: int, num_orders: int, interval_seconds: int) -> dict`:
        -   Divise `total_amount` en `num_orders` parts égales.
        -   Planifie l\'exécution à des intervalles spécifiés.
-   [ ] **Système de Take-Profit en Échelle (Laddering)**:
    -   [ ] `def create_tp_ladder(self, entry_price: float, position_size: float, levels: list, percentages: list) -> list`:
        -   `levels`: liste de cibles de prix en pourcentages (ex: `[1.05, 1.10, 1.20]`).
        -   `percentages`: pourcentage de la position à vendre à chaque niveau (ex: `[0.3, 0.3, 0.4]`).
        -   Retourne une liste d\'ordres à exécuter.
-   [ ] **Fonctionnalité de Trailing Stops**:
    -   [ ] Créer une tâche de fond pour surveiller les mouvements de prix.
    -   [ ] Ajuster le stop-loss à mesure que le prix évolue favorablement.
    -   [ ] Implémenter avec une distance en pourcentage ou basée sur l\'ATR.
-   [ ] **Ordres Basés sur le Temps (GTD - Good Till Date)**.
-   [ ] **Ordres Conditionnels**.
-   [ ] **Gestionnaire d\'Ordres (`OrderManager` classe)**:
    -   [ ] Suivre tous les ordres ouverts.
    -   [ ] Implémenter l\'annulation/modification d\'ordres.
    -   [ ] Gérer les timeouts pour les ordres limites.

## 7. Robust Backtesting Engine (`backtest_engine.py`)
En complément de `todo-features.md` (IV.2 - Jumeau Numérique), un moteur de backtest plus classique :
-   [ ] **Chargement de Données Historiques**:
    -   [ ] `async def load_historical_data(self, token_address: str, timeframe: str, days: int) -> pd.DataFrame`:
        -   Charge les données OHLCV (depuis Coingecko, DexScreener, ou `market_data.py`).
        -   Nettoie et normalise le format des données.
-   [ ] **Simulation de Backtesting**:
    -   [ ] `def run_backtest(self, strategy: BaseStrategy, historical_data: pd.DataFrame, initial_capital: float) -> dict`:
        -   Traite les données chronologiquement pour éviter le biais de lookahead.
        -   Applique les signaux de la stratégie pour générer des trades.
        -   Suit la valeur du portefeuille, les drawdowns, et les statistiques de trades.
-   [ ] **Calcul de Métriques de Performance**:
    -   [ ] `def calculate_metrics(self, backtest_results: dict) -> dict`:
        -   Ratio de Sharpe, Ratio de Sortino, Ratio de Calmar.
        -   Max Drawdown, Taux de Réussite, Facteur de Profit.
-   [ ] **Optimisation des Paramètres de Stratégie**:
    -   [ ] Recherche par grille (grid search) et/ou aléatoire.
    -   [ ] Optimisation par validation progressive (walk-forward optimization).
-   [ ] **Simulation de Monte Carlo pour l\'Évaluation des Risques**.
-   [ ] **Modèles Réalistes de Frais et de Slippage pour le Backtesting**.
-   [ ] **Composants de Visualisation**:
    -   [ ] Courbe des capitaux (Equity curve).
    -   [ ] Visualisation du drawdown.
    -   [ ] Graphiques de comparaison de stratégies.
    -   [ ] Marqueurs d\'entrée/sortie de trade sur les graphiques.

-   [ ] **Stratégie de Backtesting Spécifique pour l\'AIAgent Basé sur LLM (Gemini)**:
    -   [ ] **Objectif Principal**: Évaluer l'efficacité des *décisions* de l'AIAgent et la performance du *système global d\'exécution* de ces décisions, tout en gérant les défis de coût et de reproductibilité des LLMs.
    -   [ ] **Phase 1: Collecte de Données de Décision (Mode Live/Paper Trading)**:
        -   [ ] Pendant les opérations en mode live ou paper trading, journaliser de manière exhaustive:
            -   L\'intégralité des `aggregated_inputs` envoyés à `AIAgent.decide_trade()`.
            -   Le prompt exact généré et envoyé à `GeminiClient`.
            -   La réponse JSON brute exacte reçue de `GeminiClient`.
            -   La décision structurée finale parsée par `AIAgent` (incluant action, montant, SL/TP, raisonnement).
            -   Toutes les étapes d\'exécution du trade par `TradeExecutor` et `TradingEngine`, y compris les signatures de transaction, les prix d\'exécution réels, les erreurs, etc.
        -   [ ] Stocker ces enregistrements dans une base de données dédiée au backtesting/analyse (peut-être une copie ou une section de `EnhancedDatabase`).
    -   [ ] **Phase 2: Backtesting par "Rejeu de Décisions" (Decision Replay)**:
        -   [ ] **Principe**: Utiliser les décisions *déjà prises et enregistrées* par Gemini lors du fonctionnement réel/papier.
        -   [ ] Le `BacktestEngine` chargera les données de marché historiques OHLCV pour la période correspondante.
        -   [ ] Pour chaque point temporel dans les données historiques où une décision a été enregistrée (basée sur le timestamp des `aggregated_inputs`):
            -   Le `BacktestEngine` ne réinterrogera PAS l\'API Gemini.
            -   Il récupérera la `décision structurée finale parsée` correspondante depuis la base de données de la Phase 1.
            -   Il simulera l\'exécution de cette décision fixe contre les données de marché historiques au moment `t` (en utilisant les prix `close` ou `open` de la bougie suivante, et en appliquant des modèles de slippage et de frais configurables dans `BacktestEngine`).
        -   [ ] **Avantages de cette approche**:
            -   **Coût Nul pour l\'API LLM**: Pas d\'appels à Gemini pendant le backtest.
            -   **Reproductibilité Parfaite des Décisions LLM**: Les décisions sont fixes.
            -   **Focalisation sur l\'Exécution et les Paramètres SL/TP**: Permet d\'évaluer si les SL/TP suggérés par l\'IA étaient pertinents, si le timing d\'exécution était bon, et comment les frais/slippage impactent la performance des décisions de l\'IA.
            -   **Permet de tester des ajustements de la logique d\'exécution ou des paramètres de risque *autour* des décisions de l\'IA**.
    -   [ ] **Phase 3: Analyse de Performance et Itération**:
        -   [ ] Analyser les résultats du backtest par rejeu pour identifier les points faibles (ex: SL trop serrés, impact du slippage mal estimé par l\'IA).
        -   Utiliser ces analyses pour affiner:
            -   Le prompt Gemini (ex: demander des SL/TP plus larges, ou de considérer le slippage de manière plus explicite).
            -   La logique de `TradeExecutor` ou `RiskManager`.
    -   [ ] **Limitations et Compléments**: 
        -   Cette méthode ne backteste pas la *capacité de généralisation* de Gemini à des situations de marché radicalement différentes de celles rencontrées lors de la collecte des décisions. Elle teste principalement la qualité des décisions passées dans leur contexte d'exécution.
        -   Pour évaluer la robustesse du *prompt* lui-même, des tests limités et ciblés avec des `aggregated_inputs` historiques spécifiques (représentant des conditions de marché variées ou critiques) peuvent être effectués manuellement ou via des scripts de test dédiés (avec appels réels à Gemini, en gardant un œil sur les coûts).
        -   **[NOUVEAU] Phase 2.bis: Évaluation de la Généralisation des Décisions sur Données Non Vues (Coût Contrôlé)**:
            -   [ ] Sélectionner un sous-ensemble représentatif mais limité (ex: 50-100 points de décision) de `aggregated_inputs` historiques qui n'ont **pas** été utilisés lors de la phase de collecte de décision initiale (Phase 1).
            -   [ ] Soumettre ces `aggregated_inputs` à l'`AIAgent` pour obtenir de nouvelles décisions de Gemini (ceci impliquera des appels API réels et donc un coût).
            -   [ ] Simuler l'exécution de ces nouvelles décisions contre les données historiques correspondantes (comme en Phase 2).
            -   [ ] Comparer la performance de ces décisions "à froid" avec celles obtenues par rejeu (Phase 2) et avec un benchmark simple (ex: buy & hold).
            -   [ ] **Objectif**: Obtenir une estimation de la capacité de l'AIAgent à généraliser son raisonnement à des situations non vues, sans encourir les coûts d'un backtest complet avec appels LLM.
        -   **Focus du backtesting des modules d'input**: Les modules qui génèrent les `aggregated_inputs` (stratégies, `PredictionEngine`, `AnalyticsEngine`) doivent être backtestés de manière plus traditionnelle, en évaluant la qualité de leurs signaux/prédictions par rapport aux données historiques, indépendamment de l'AIAgent. Un bon signal d'entrée est crucial pour une bonne décision de l'IA.
    -   [ ] **Pas de Simulation/Mocking de Gemini à ce stade**: Simuler la logique de Gemini est extrêmement complexe et peu fiable. Le rejeu de décisions existantes est la stratégie privilégiée.

## 8. Market-Making Capabilities (`market_maker.py`)

-   [ ] **Clarification du Rôle dans l'Architecture centrée sur l'AIAgent**:
    -   [ ] **Mode Opérationnel Principal**: Le `market_maker.py` ne fonctionnera pas de manière complètement autonome pour prendre des décisions de market making actives en production initiale. Son rôle principal sera d'agir comme un **fournisseur d'analyses avancées** et de **capacités d'exécution spécialisées** pour l'`AIAgent`.
    -   [ ] **Inputs Fournis à l'AIAgent**:
        -   Analyse des spreads optimaux potentiels.
        -   Évaluation des risques d'inventaire pour des paires spécifiques.
        -   Scores de "toxicité" du flux d'ordres.
        -   Prédictions de volatilité à court terme spécifiques au market making.
        -   Ces informations seraient structurées et incluses dans `aggregated_inputs` sous une clé comme `market_making_analysis`.
            ```json
            // Dans aggregated_inputs
            "market_making_analysis": {
                "target_pair": "SOL/USDC",
                "optimal_spread_bps_suggestion": 15, // Suggestion de spread si l'IA envisageait de fournir de la liquidité
                "inventory_risk_score": 0.3, // 0 (low) to 1 (high) for current target pair inventory
                "order_flow_toxicity_score": 0.1,
                "short_term_volatility_market_making": "LOW",
                "reasoning_snippet": "Current spread is tight, low toxicity, but inventory slightly skewed."
            }
            ```
    -   [ ] **Décision de l'AIAgent**: L'`AIAgent` (via Gemini) pourrait utiliser ces informations pour:
        -   Informer ses décisions de trading directionnel (ex: si le flux est toxique, éviter de trader).
        -   **Potentiellement, dans une phase ultérieure**, décider d'activer un mode de "fourniture de liquidité passive" si les conditions de marché (analysées par `market_maker.py`) sont jugées extrêmement favorables et à faible risque. Dans ce cas, l'`AIAgent` définirait les paramètres clés (paire, exposition max, spread cible) et `market_maker.py` exécuterait cette stratégie passive, toujours sous la supervision de `DexBot`.
    -   [ ] **Interaction avec `TradingEngine`**: Si l'`AIAgent` décide de placer des ordres qui s'apparentent à du market making (ex: des ordres limites des deux côtés du carnet pour une paire spécifique et pour une courte durée), `market_maker.py` pourrait fournir la logique pour calculer les prix et tailles optimaux de ces ordres, que `TradingEngine` exécuterait ensuite.
    -   [ ] **Pas d'Autonomie Initiale**: Le `market_maker.py` n'aura pas de capital propre alloué ni la capacité de démarrer/arrêter ses opérations de manière autonome. Toute activité sera initiée et paramétrée par une décision de l'`AIAgent`.

-   [ ] **Définition du Market Maker de Base**:
    -   [ ] `MarketMaker` classe:
        -   Paramètres: `trading_engine`, `pair_address`, `base_spread` (%), `inventory_target` (ratio).
-   [ ] **Logique de Génération de Cotations**:
    -   [ ] `generate_quotes(self, mid_price: float, volatility: float) -> dict`:
        -   Basé sur le prix médian du carnet d\'ordres, la volatilité (pour ajustement du spread), et la position d\'inventaire (pour skewing).
-   [ ] **Gestion de l\'Inventaire**:
    -   [ ] `adjust_for_inventory(self, bid_size: float, ask_size: float, current_inventory: float) -> tuple`:
        -   Ajuste la taille des ordres pour cibler `inventory_target`.
        -   Réduit la taille du bid si inventaire > cible, réduit la taille du ask si inventaire < cible.
-   [ ] **Gestion du Spread Basée sur la Volatilité**:
    -   [ ] Calculer la volatilité historique.
    -   [ ] Élargir le spread en période de haute volatilité, le resserrer en période de faible volatilité.
-   [ ] **Détection de Flux Toxique**:
    -   [ ] `detect_toxic_flow(self, recent_trades: list) -> bool`:
        -   Analyse les trades récents pour des patterns de sélection adverse.
        -   Identifie les flux de trades unilatéraux.
-   [ ] **Logique de Rafraîchissement des Cotations**:
    -   [ ] Tâche de fond pour rafraîchir périodiquement les cotations.
    -   [ ] Logique pour annuler et remplacer les cotations après un mouvement de prix.
    -   [ ] Disjoncteurs en cas de volatilité extrême.
-   [ ] **Laddering de Cotations Sophistiqué**.
-   [ ] **Monitoring des Positions de Fournisseur de Liquidité (LP)** (si le bot fournit activement de la liquidité à des pools).

---

## VII. Idées Innovantes (Source: Résumé Utilisateur)

Cette section détaille des idées d\'amélioration basées sur l\'analyse de réseaux et l\'apprentissage automatique avancé.

### 7.1. Optimisation de Portefeuille Basée sur les Réseaux de Corrélation
- [ ] **Concept**: Construire un réseau de corrélation des rendements de cryptomonnaies. Utiliser la Théorie des Matrices Aléatoires (RMT) pour filtrer le bruit et un Arbre de Recouvrement Minimal (MST) pour simplifier le réseau. Ajuster les poids du portefeuille en fonction de la centralité eigenvectorielle des actifs pour minimiser les risques systémiques.
- [ ] **Avantages**: Réduction des risques systémiques, diversification efficace, adaptabilité aux dynamiques de marché.
- [ ] **Implémentation**:
    - [ ] **Données**: Prix historiques (CoinMarketCap, etc.).
    - [ ] **Outils**: `NumPy`, `SciPy`, `NetworkX`, `scikit-learn`.
    - [ ] **Étapes**:
        - [ ] Calculer la matrice de corrélation (fenêtre glissante).
        - [ ] Appliquer RMT pour filtrage.
        - [ ] Construire MST.
        - [ ] Calculer centralités eigenvectorielles.
        - [ ] Optimiser les poids du portefeuille (ex: minimiser \(w^T \Sigma^* w + \gamma \sum x_i w_i\)).
- [ ] **Complexité**: Conceptuelle: Moyenne à Élevée / Implémentation: Élevée.
- [ ] **Intégration**: `app/risk_manager.py` (ajustement dynamique des tailles de position). Calculs en arrière-plan.

### 7.2. Analyse du Réseau des Développeurs pour Prédire les Corrélations de Prix
- [ ] **Concept**: Modéliser un réseau où les cryptomonnaies sont des nœuds et les arêtes représentent les développeurs partagés (via contributions GitHub). Les projets avec des développeurs communs peuvent avoir des rendements corrélés.
- [ ] **Avantages**: Facilite les stratégies de trading par paires/couverture, signaux précoces basés sur l'activité des développeurs, évaluation de la robustesse des projets.
- [ ] **Implémentation**:
    - [ ] **Données**: Contributeurs (API GitHub).
    - [ ] **Outils**: `NetworkX`, `Pandas`, `Matplotlib`.
    - [ ] **Étapes**:
        - [ ] Collecter données des contributeurs GitHub.
        - [ ] Construire réseau (projets partageant des développeurs).
        - [ ] Détection de communautés (Louvain), calcul de centralités (degré, PageRank).
        - [ ] Corréler structure du réseau avec prix historiques de `app/market/market_data.py`.
- [ ] **Complexité**: Conceptuelle: Moyenne / Implémentation: Moyenne à Élevée (limites API GitHub, traitement données).
- [ ] **Intégration**: `app/prediction_engine.py` ou nouveau module `developer_network_analyzer.py` pour fournir prédictions de corrélation au `StrategyFramework`.

  - [ ] **Intégration au `prediction_engine`**: Les signaux causaux viendraient enrichir les features ou moduler la confiance des prédictions ML.
  - [ ] **Intégration Prévue**: Le MAC-MM agirait comme une source d'enrichissement pour le `PredictionEngine` ou comme une source de signaux distincte dans les `aggregated_inputs` pour l'`AIAgent`. Il pourrait fournir des scores de probabilité d'impact pour des événements détectés ou des facteurs de confiance ajustés pour certaines prédictions.
  - [ ] **Impact Potentiel sur Prompt Gemini**: Un nouvel objet dans `aggregated_inputs.signal_sources` ou une nouvelle clé `aggregated_inputs.causal_analysis` pourrait contenir des informations structurées telles que : `{"event_type": "REGULATORY_NEWS_CRYPTO", "detected_event": "SEC announces new DeFi rules for protocol X", "predicted_impact_on_SOL_USDC": "NEGATIVE_MEDIUM_CONFIDENCE", "time_horizon_hours": 12, "causal_strength_score": 0.65}`.

### 1.2. Modélisation de la Liquidité Dynamique et Prédiction d'Impact 

- [ ] **Meta-Stratégie**: Un agent "maître" pourrait agréger les signaux des meilleurs agents ou allouer dynamiquement du capital aux stratégies les plus performantes en temps réel.
- [ ] **Intégration Prévue**: Les stratégies les plus performantes découvertes par le Swarm pourraient être enregistrées et rendues disponibles via le `StrategyFramework`, devenant ainsi des sources de signaux standard pour l'`AIAgent`. Alternativement, l'agent "maître" du Swarm pourrait lui-même fournir un signal agrégé ou une recommandation d'allocation de stratégie directement à l'`AIAgent`.
- [ ] **Impact Potentiel sur Prompt Gemini**: De nouveaux signaux pourraient apparaître dans `aggregated_inputs.signal_sources` (ex: `{"source_name": "SwarmAlpha_Strategy_Variant_7B", "signal": "BUY", "confidence": 0.75, ...}`). Si un agent maître fournit un signal d'allocation, cela pourrait être un input de plus haut niveau dans `aggregated_inputs`, par exemple: `"swarm_meta_signal": {"recommended_strategy_focus": ["MomentumStrategy_1h", "SwarmAlpha_7B"], "confidence_in_focus": 0.7, "reasoning": "Current market regime favors these approaches according to swarm learning."}`.

### 2.2. "Shadow Trading" Dynamique Basé sur l'Analyse Comportementale des Wallets Performants 