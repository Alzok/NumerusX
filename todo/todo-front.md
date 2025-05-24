# NumerusX - Guide de Développement de l'Interface Utilisateur (UI) pour IA 🎨

**Prompt pour l'IA**: En tant qu'IA spécialisée dans le développement d'interfaces, ta mission est de créer une interface utilisateur (UI) claire, moderne, et minimaliste pour NumerusX. L'UI doit suivre les principes du Material Design et permettre une gestion intuitive de l'application. Implémente les fonctionnalités étape par étape en te basant sur le fichier `app/gui.py` et `app/dashboard.py` comme point de départ, et en respectant les besoins définis ci-dessous. Assure-toi de la cohérence avec les fonctionnalités existantes et prévues du bot.

## Objectifs Généraux de l'UI:

-   **Contrôle Centralisé**: Démarrer, arrêter, et configurer le bot.
-   **Feedback en Temps Réel**: Afficher l'état du bot, les logs, et les actions en cours.
-   **Visualisation de Données**: Présenter les performances, les trades, et l'analyse de marché via des graphiques et tableaux clairs.
-   **Esthétique Moderne**: Interface épurée, intuitive, avec une bonne expérience utilisateur (UX).
-   **Réactivité**: L'interface doit être fluide et se mettre à jour dynamiquement.

## Structure de l'Interface (Basée sur `app/dashboard.py` et `todo.md`)

Utiliser `nicegui` comme framework. Le fichier `app/dashboard.py` servira de base pour l'implémentation.

### Étape 1: Initialisation et Structure Globale de l'UI

-   [ ] **Créer/Modifier `app/dashboard.py` pour héberger la logique de l'UI.**
    -   [ ] Définir la classe `NumerusXDashboard`.
    -   [ ] Initialiser les composants principaux du bot nécessaires à l'UI (`bot`, `db`, `dex_api`, `analytics`, `performance_monitor`).
-   [ ] **Implémenter un Header Global.**
    -   [ ] Titre de l'application "NumerusX Trading Dashboard".
    -   [ ] Icône de l'application.
    -   [ ] Indicateur de statut du bot (rond vert/rouge).
    -   [ ] Bouton de rafraîchissement manuel.
    -   [ ] Bouton "Settings" (roue crantée) avec un menu déroulant.
-   [ ] **Implémenter un Footer Global.**
    -   [ ] Version de l'application et date.
-   [ ] **Système de Navigation Principal par Onglets.**
    -   [ ] Onglet "Portfolio".
    -   [ ] Onglet "Trading Activity".
    -   [ ] Onglet "Market Analysis".
    -   [ ] Onglet "Control Center".
    -   [ ] Onglet "System Monitor".
-   [ ] **Mettre en place le mécanisme de mise à jour automatique de l'UI (`ui.timer`).**

### Étape 2: Panneau "Portfolio Overview"

-   [ ] **Afficher la Valeur Totale du Portefeuille.**
    -   [ ] Label principal affichant la valeur (ex: "$10,523.45").
    -   [ ] Label secondaire pour la variation sur 24h (ex: "+2.34%", couleur verte/rouge).
-   [ ] **Graphique d'Allocation d'Actifs.**
    -   [ ] Utiliser un graphique Plotly de type Pie/Donut.
    -   [ ] Afficher les principaux actifs et leur pourcentage dans le portefeuille.
-   [ ] **Graphique de Performance du Portefeuille.**
    -   [ ] Utiliser un graphique Plotly de type ligne.
    -   [ ] Permettre de sélectionner différentes périodes (1D, 1W, 1M).
    -   [ ] Afficher l'évolution de la valeur du portefeuille dans le temps.
-   [ ] **Tableau des Principales Positions ("Top Holdings").**
    -   [ ] Colonnes: Actif (symbole), Quantité, Prix Actuel, Valeur Totale, P&L (non réalisé), Variation 24h.
    -   [ ] Récupérer les données depuis `PortfolioManager` et `DexAPI`.

### Étape 3: Panneau "Trading Activity Center"

-   [ ] **Tableau des Trades Récents.**
    -   [ ] Colonnes: Timestamp, Paire, Type (Achat/Vente), Montant, Prix d'Exécution, P&L réalisé (si trade fermé), Statut.
    -   [ ] Récupérer les données depuis `EnhancedDatabase`.
-   [ ] **Visualisation du Taux de Réussite des Trades.**
    -   [ ] Graphique Plotly de type Jauge ou Bar simple (Trades Gagnants vs Perdants).
-   [ ] **Graphiques de Volume de Trading.**
    -   [ ] Volume par jour/semaine (Graphique en barres Plotly).
-   [ ] **Graphique de Distribution des Trades par Type de Token.**
    -   [ ] (Ex: % de trades sur SOL, USDC, autres altcoins) - Graphique Pie/Bar Plotly.

### Étape 4: Panneau "Market Analysis Section"

-   [ ] **Indicateur des Conditions de Marché.**
    -   [ ] Icône et label (Bull/Bear/Neutral) basés sur une analyse (ex: `prediction_engine` ou `analytics_engine`).
-   [ ] **Watchlist des Trades Potentiels.**
    -   [ ] Tableau affichant les tokens avec des signaux d'achat/vente forts générés par les stratégies, avec leur score de confiance.
-   [ ] **Graphiques de Prix pour les Paires Actives/Sélectionnées.**
    -   [ ] Sélecteur de token pour choisir l'actif à afficher.
    -   [ ] Graphique Plotly de type Candlestick.
    -   [ ] Options de timeframe (1H, 4H, 1D).
-   [ ] **Visualisation des Indicateurs Techniques (RSI, MACD, etc.).**
    -   [ ] Graphiques Plotly séparés (ou superposés sur le graphique de prix) pour l'actif sélectionné.

### Étape 5: Panneau "Control Center"

-   [ ] **Boutons de Contrôle du Bot.**
    -   [ ] Bouton Démarrer/Arrêter le bot (avec changement d'icône et de couleur).
    -   [ ] Bouton d'Arrêt d'Urgence avec confirmation.
-   [ ] **Ajustement du Niveau de Risque.**
    -   [ ] Slider pour modifier `Config.TRADE_THRESHOLD` ou un paramètre équivalent dans `RiskManager`.
-   [ ] **Sélecteur de Stratégie.**
    -   [ ] Menu déroulant pour choisir parmi les stratégies implémentées (si plusieurs sont disponibles).
-   [ ] **Formulaire d'Entrée Manuelle de Trade.**
    -   [ ] Champs pour: Token d'entrée, Token de sortie, Montant.
    -   [ ] Affichage des frais estimés avant exécution.
    -   [ ] Boutons "Preview" et "Execute".

### Étape 6: Panneau "System Monitoring"

-   [ ] **Indicateurs d'État du Bot et d'Uptime.**
    -   [ ] Afficher l'uptime du bot (ex: "2j 5h 32m").
    -   [ ] Indicateurs de santé pour les connexions API (Market Data, Trading Engine) et la base de données.
-   [ ] **Métriques d'Utilisation des Ressources.**
    -   [ ] Graphiques Plotly en temps réel (ou mis à jour fréquemment) pour l'utilisation CPU et Mémoire (utiliser `psutil`).
-   [ ] **Visualisation du Taux d'Erreur.**
    -   [ ] Compteur d'erreurs sur les dernières 24h.
    -   [ ] Affichage des derniers messages d'erreur importants dans une zone de log dédiée.

### Étape 7: Panneau "Settings" (accessible via le menu du Header)

-   [ ] **Éditeur des Paramètres de Configuration.**
    -   [ ] Permettre de modifier certains paramètres de `Config` (ex: `SLIPPAGE`, `MAX_ORDER_SIZE`, `MIN_LIQUIDITY`) et de les sauvegarder (potentiellement dans un fichier de configuration utilisateur ou directement dans `Config` si la structure le permet dynamiquement).
-   [ ] **Paramètres de Notification.**
    -   [ ] Options pour activer/désactiver les notifications pour certains événements (trades, erreurs critiques).
-   [ ] **Sélecteur de Thème (Light/Dark).**
    -   [ ] Interrupteur pour basculer entre le thème clair et sombre de `nicegui`.
-   [ ] **Contrôle du Taux de Rafraîchissement des Données.**
    -   [ ] Input numérique pour ajuster la fréquence de `ui.timer`.

### Étape 8: Améliorations Générales et Finitions

-   [ ] **Réactivité Mobile**: S'assurer que le layout s'adapte correctement aux différentes tailles d'écran.
-   [ ] **Utilisation de Composants Material Design**: Utiliser des cartes (`ui.card`), des tabs (`ui.tabs`), des sections extensibles pour organiser l'information de manière claire.
-   [ ] **Optimisation des Performances de l'UI**: S'assurer que les mises à jour de l'UI sont efficientes et ne bloquent pas le thread principal.
-   [ ] **Gestion des Erreurs dans l'UI**: Afficher des messages d'erreur clairs à l'utilisateur si des données ne peuvent pas être chargées ou si une action échoue.
-   [ ] **Internationalisation (Optionnel)**: Prévoir la possibilité de traduire l'interface si nécessaire.

**Sources de Données pour l'UI (Rappel de `todo.md`):**
-   `EnhancedDatabase` pour les données historiques de trades.
-   `DexAPI` (ou `MarketDataProvider`) pour les informations de marché.
-   `PortfolioManager` pour les données de portefeuille.
-   `PerformanceMonitor` de `monitoring.py` pour les métriques système.

Ce guide devrait fournir une structure claire pour le développement de l'interface. L'IA devra consulter les fichiers existants (`app/gui.py`, `app/dashboard.py`) pour voir ce qui est déjà en place et l'étendre ou le modifier en conséquence.