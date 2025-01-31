# Documentation Technique - NumerusX Bot

![Logo](logo.jpg)

## Fonctionnalités Clés
- **Analyse en Temps Réel**  
  Surveillance des paires DEX via Dexscreener (prix, volume, liquidité)
- **Détection de Risques**  
  Vérification Rugcheck + filtrage automatique des tokens à risque
- **Stratégie de Trading**  
  Combinaison RSI/MACD/Ichimoku avec seuils configurables
- **Exécution Cross-Plateforme**  
  Support CEX (Binance, KuCoin) et DEX (Uniswap, PancakeSwap)
- **Journalisation Avancée**  
  Stockage structuré des logs (fichier + console)

---

## Prérequis Techniques

### Services Externes
| Service | Lien | Obligatoire |
|---------|------|-------------|
| Dexscreener | [API Docs](https://docs.dexscreener.com/) | ✅ |
| Rugcheck | [API Access](https://rugcheck.xyz/api) | ✅ |
| CEX (Binance/KuCoin) | [API Management](https://www.binance.com/en/support/faq/360002502072) | ✅ |

---

## Installation

### 1. Cloner le Dépôt
```bash
git clone https://github.com/Alzok/NumerusX.git
cd numerusx
```

### 2. Configuration Docker
```bash
# Construire l'image
docker-compose build

# Démarrer le conteneur
docker-compose up -d
```

### 3. Fichier d'Environnement
```bash
cp .env.example .env
nano .env  # Remplir avec vos clés
```
Variables obligatoires :
```ini
RUGCHECK_API_KEY="votre_clé"
CEX_API_KEY="votre_clé_binance"
CEX_API_SECRET="votre_secret_binance"
```

---

## Configuration

### Fichiers Importants
| Fichier | Description |
|---------|------------|
| `config.py` | Paramètres généraux (intervalles, seuils) |
| `schema.sql` | Structure de la base de données |
| `data/trading.log` | Journal des opérations |

### Options Principales
```python
# Dans config.py
UPDATE_INTERVAL = 60  # Analyse toutes les 60s
RISK_PER_TRADE = 0.02  # 2% du capital par trade
BLACKLIST_THRESHOLD = 0.25  # 25%+ = supply suspecte
```

---

## Exécution

### Commandes Docker
```bash
# Démarrer/Arrêter
docker-compose start
docker-compose stop

# Voir les logs
docker-compose logs -f

# Mise à jour
docker-compose pull && docker-compose up -d
```

### Commandes CLI (Sans Docker)
```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le bot
python app/main.py

# Vérifier la base de données
sqlite3 data/dex_data.db "PRAGMA integrity_check"
```

---

## Services Externes

### Obtenir les Clés API

#### Dexscreener
Aucune clé nécessaire pour l'API publique

#### Rugcheck
Créer un compte sur [rugcheck.xyz](https://rugcheck.xyz) > Section Développeur

#### Exchanges CEX
- [Binance : API Management](https://www.binance.com/en/support/faq/360002502072)
- [KuCoin : API Creation](https://www.kucoin.com/account/api)

---

## Dépannage

### Problèmes Fréquents
| Symptôme | Solution |
|----------|---------|
| 403 Forbidden sur Rugcheck | Vérifier la clé API + quota |
| Erreurs CCXT | Redémarrer le bot + vérifier les permissions API |
| Base de données verrouillée | `docker-compose restart` |
| Latence élevée | Augmenter `UPDATE_INTERVAL` dans `config.py` |

### Vérifier l'État du Système
```bash
# Tester Dexscreener
curl https://api.dexscreener.com/latest/dex/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640

# Tester Rugcheck
curl -H "x-api-key: $RUGCHECK_API_KEY" https://api.rugcheck.xyz/v1/contracts/0x.../score
```

---

## Recommandations de Sécurité
- **VPN** : Toujours actif pendant l'exécution
- **Clés API** : Permissions minimales (read + trade only)
- **Backups** : Automatiser la copie de `data/dex_data.db`
- **Monitoring** : Surveiller `data/trading.log` quotidiennement

---

## Ressources Utiles
- [Code Source](https://github.com/votre-utilisateur/numerusx)
- [Documentation Dexscreener](https://docs.dexscreener.com/)
- [Documentation CCXT](https://docs.ccxt.com)
- [API Rugcheck](https://rugcheck.xyz/api)
