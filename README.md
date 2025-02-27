![Logo](logo.jpg)

# NumerusX - Plateforme avancée de trading algorithmique pour les cryptomonnaies

NumerusX est une plateforme complète de trading algorithmique pour le marché des cryptomonnaies, conçue pour développer, tester et déployer des stratégies de trading automatisées avec une attention particulière à la gestion du risque, la prédiction de prix et l'analyse de sécurité.

## Caractéristiques principales

- **Framework de stratégies flexibles** : Développez des stratégies personnalisées en utilisant un cadre extensible.
- **Backtest et optimisation** : Testez et optimisez vos stratégies avec des données historiques précises.
- **Gestion avancée des risques** : Contrôlez votre exposition et protégez votre capital avec des outils de gestion du risque sophistiqués.
- **Analyse de sentiment** : Intégrez l'analyse de sentiment des réseaux sociaux dans vos stratégies.
- **Prédiction de prix par ML** : Utilisez des modèles d'apprentissage automatique pour anticiper les mouvements de prix.
- **Vérifications de sécurité** : Protégez-vous contre les escroqueries et les tokens à risque.
- **Évaluation et débogage** : Analysez et améliorez la performance de vos stratégies.

## Structure du projet

```
NumerusX/
├── strategy_framework.py    # Cadre pour développer des stratégies de trading
├── strategy_evaluator.py    # Outils d'évaluation des stratégies
├── strategy_debug.py        # Utilitaires de débogage avancé pour stratégies
├── market_data.py           # Fournisseur de données de marché
├── prediction_engine.py     # Moteur de prédiction basé sur l'apprentissage automatique
├── security.py              # Vérifications de sécurité pour les tokens
├── risk_manager.py          # Gestion des risques et du portefeuille
└── trading_engine.py        # Moteur d'exécution des ordres
```

## Composants du système

### Strategy Framework

Le cœur du système qui permet de développer des stratégies de trading. Il comprend:

- Classes de base pour les stratégies
- Types de signaux prédéfinis (BUY, SELL, STRONG_BUY, etc.)
- Calcul de métriques pour évaluer les performances
- Mécanismes d'optimisation des paramètres

Exemples de stratégies incluses:
- Moving Average Crossover
- RSI (Relative Strength Index)
- Volatility Breakout
- Pattern Recognition
- Sentiment-Based

### Evaluation et Débogage

Outils permettant d'analyser en profondeur les performances des stratégies:

- Métriques de performance complètes (ROI, ratio de Sharpe, drawdown, etc.)
- Visualisations détaillées (courbes d'équité, distributions des rendements)
- Rapport de débogage avec timeline de signaux et analyse d'erreurs
- Recommandations d'amélioration automatiques

### Gestion des risques

Système avancé de gestion des risques pour protéger votre capital:

- Calcul de taille de position optimale avec critère de Kelly
- Contrôle des corrélations entre actifs
- Limites d'exposition dynamiques
- Mécanisme de "circuit breaker" en cas de drawdown important

### Prédiction de prix

Moteur de prédiction basé sur l'apprentissage automatique:

- Classification automatique du régime de marché
- Sélection dynamique du modèle selon le régime
- Analyse de sentiment intégrée depuis Twitter, Discord, Reddit
- Optimisation par apprentissage par renforcement

### Sécurité

Module de vérification des tokens pour prévenir les risques:

- Validation des adresses et contrats
- Détection de modèles de fraude et d'arnaque
- Vérification de la liquidité et de sa profondeur
- Analyse des détenteurs et de la distribution des tokens

## Comment utiliser le système

### Installation des dépendances

```bash
pip install numpy pandas matplotlib seaborn scikit-learn torch aiohttp
```

### Création d'une stratégie simple

```python
from strategy_framework import Strategy, Signal, SignalType

class SimpleMAStrategy(Strategy):
    """Stratégie simple de croisement de moyennes mobiles."""
    
    def __init__(self, name: str, timeframes: List[str], params: Dict[str, Any] = None):
        default_params = {
            "fast_ma": 10,
            "slow_ma": 30
        }
        actual_params = default_params.copy()
        if params:
            actual_params.update(params)
            
        super().__init__(name, timeframes, actual_params)
        
    async def generate_signal(self, token_address: str, price_data: pd.DataFrame, timeframe: str) -> Signal:
        # Calculer les moyennes mobiles
        fast_ma = price_data['close'].rolling(window=self.params["fast_ma"]).mean()
        slow_ma = price_data['close'].rolling(window=self.params["slow_ma"]).mean()
        
        # Obtenir les valeurs les plus récentes
        latest_fast = fast_ma.iloc[-1]
        latest_slow = slow_ma.iloc[-1]
        prev_fast = fast_ma.iloc[-2]
        prev_slow = slow_ma.iloc[-2]
        
        # Déterminer le type de signal
        if prev_fast < prev_slow and latest_fast > latest_slow:
            signal_type = SignalType.BUY
            confidence = 0.8
        elif prev_fast > prev_slow and latest_fast < latest_slow:
            signal_type = SignalType.SELL
            confidence = 0.8
        else:
            signal_type = SignalType.NEUTRAL
            confidence = 0.5
            
        # Créer et retourner le signal
        signal = Signal(
            type=signal_type,
            confidence=confidence,
            timestamp=time.time(),
            token_address=token_address,
            timeframe=timeframe,
            strategy_name=self.name,
            metadata={
                "fast_ma": latest_fast,
                "slow_ma": latest_slow
            }
        )
        
        return signal
```

### Exécution d'un backtest

```python
import asyncio
from strategy_framework import BacktestEngine
from strategy_evaluator import StrategyEvaluator

async def run_backtest():
    # Créer une stratégie
    strategy = SimpleMAStrategy(
        name="SimpleMA_10_30", 
        timeframes=["1h", "4h"]
    )
    
    # Charger les données historiques
    price_data = {
        "1h": pd.read_csv("historical_data_1h.csv"),
        "4h": pd.read_csv("historical_data_4h.csv")
    }
    
    # Exécuter le backtest
    backtest_engine = BacktestEngine()
    result = await backtest_engine.run_backtest(
        strategy, 
        price_data, 
        "TokenXYZ123"
    )
    
    # Évaluer les performances
    evaluator = StrategyEvaluator()
    evaluation = await evaluator.evaluate_strategy(
        strategy,
        price_data, 
        "TokenXYZ123"
    )
    
    # Générer un rapport
    report = evaluator.generate_report(evaluation)
    print(f"Rapport généré: {report}")

# Exécuter le backtest
asyncio.run(run_backtest())
```

### Débogage d'une stratégie

```python
from strategy_debug import StrategyDebugger

async def debug_strategy():
    # Créer une stratégie
    strategy = SimpleMAStrategy(
        name="SimpleMA_Debug", 
        timeframes=["1h"]
    )
    
    # Charger les données
    price_data = {"1h": pd.read_csv("historical_data_1h.csv")}
    
    # Déboguer la stratégie
    debugger = StrategyDebugger()
    debug_result = await debugger.debug_strategy(
        strategy,
        price_data,
        "TokenXYZ123"
    )
    
    # Analyser les problèmes
    analysis = debugger.analyze_strategy_problems(debug_result)
    
    # Afficher les recommandations
    for recommendation in analysis["recommendations"]:
        print(f"- {recommendation}")

# Exécuter le débogage
asyncio.run(debug_strategy())
```

## Contributions

Les contributions sont les bienvenues! Voici comment vous pouvez contribuer:

1. Fork du projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Commit de vos changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## License

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## Avertissement

Ce logiciel est fourni à des fins éducatives et de recherche uniquement. Le trading de cryptomonnaies comporte des risques significatifs et peut entraîner des pertes financières importantes. Utilisez ce système à vos propres risques.

