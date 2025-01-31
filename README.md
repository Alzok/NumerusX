# 📄 Documentation du DEX Trading Bot 

## 🌟 Fonctionnalités
- Analyse temps réel via DexScreener
- Détection de scams (rug pulls, volume fake)
- Notifications Telegram instantanées
- Intégration avec BonkBot pour le trading
- Base de données SQLite sécurisée

---

## 🛠 Installation

### Prérequis
- Python 3.10+
- Git
- Terminal Linux/macOS

### Étapes
```bash
git clone https://github.com/yourusername/dex-trading-bot.git
cd dex-trading-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔑 Configuration des API

### 1. Clé Infura
- Allez sur [Infura](https://infura.io/)
- Créez un projet "Ethereum"
- Copiez la clé API dans `.env` :
```ini
INFURA_KEY="votre_clé_infura"
```

### 2. Clé Etherscan
- Inscrivez-vous sur [Etherscan](https://etherscan.io/apis)
- Génerez une clé dans "API Keys"
```ini
ETHERSCAN_KEY="votre_clé_etherscan"
```

### 3. RugCheck.xyz
- Obtenez une clé via [Documentation RugCheck](https://rugcheck.xyz/api-docs)
```ini
RUGCHECK_API_KEY="rc_votre_clé"
```

### 4. Pocket Universe
- Suivez le guide [Pocket Universe API](https://pocketuniverse.app/api-access)
```ini
POCKET_UNIVERSE_KEY="pu_votre_clé"
```

### 5. BonkBot (Trading)
1. Achetez un abonnement sur [BonkBot.io](https://bonkbot.io/pricing)
2. Génerez une clé API dans le dashboard
```ini
BONKBOT_API_KEY="bk_votre_clé"
```

---

## 💾 Configuration de la Base de Données

### Fichier Schema
`schema.sql` contient :
```sql
-- Tokens blacklistés
CREATE TABLE IF NOT EXISTS blacklisted_coins (
  address TEXT PRIMARY KEY,
  reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historique des trades
CREATE TABLE trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pair_address TEXT,
  amount REAL,
  price REAL,
  side TEXT CHECK(side IN ('BUY', 'SELL')),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Initialisation
```bash
sqlite3 dex_analytics.db < schema.sql
```

### Gestion manuelle
```bash
sqlite3 dex_analytics.db
SQLite> INSERT INTO blacklisted_coins VALUES ('0x123...', 'rug_pull', datetime());
```

---

## 🤖 Configuration Telegram

### 1. Création du Bot
1. Ouvrez [@BotFather](https://t.me/BotFather) sur Telegram
2. Envoyez `/newbot`
3. Suivez les instructions pour obtenir :
```ini
TELEGRAM_TOKEN="123456:ABC-DEF..."
```

### 2. Obtenir le Chat ID
1. Ajoutez le bot à un groupe
2. Envoyez un message
3. Visitez :
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```
4. Cherchez `"chat":{"id":-10012345...}` dans la réponse

---

## 🚀 Lancement du Bot

### Mode Démo (Pas de vrai trading)
```bash
python dex_bot.py --demo
```

### Mode Production
```bash
nohup python dex_bot.py >> trades.log 2>&1 &
```

### Vérification
```bash
tail -f trades.log
```

---

## ⌨ Commandes Telegram
| Commande | Description |
|----------|-------------|
| `/start` | Démarrer le bot |
| `/status` | Afficher les stats |
| `/blacklist 0x...` | Blacklister un token |
| `/whitelist 0x...` | Retirer de la blacklist |
| `/panic` | Annuler tous les trades |

---

## 🔍 Exemples d'Alertes
```text
🟢 BUY Signal Detected!
Token: PEPE/USDC
Volume: $1.2M (+325%)
Confidence: 89.5%
```

```text
🔴 SELL Signal Detected!
Reason: Price drop >15% in 1H
Target: Take profit @ $0.00045
```

---

## 🚨 Dépannage

### Erreurs Courantes
1. **Clés API invalides** : Vérifiez les permissions
2. **Problèmes de DB** : Exécutez `sqlite3 dex_analytics.db "PRAGMA integrity_check"`
3. **Latence réseau** : Augmentez `API_TIMEOUT` dans `config.py`

### Logs
```bash
grep "ERROR" trades.log # Voir les erreurs
grep "EXECUTE" trades.log # Voir les trades
```

---

## 📞 Support
- Documentation DexScreener : [dexscreen.com/docs](https://dexscreen.com/docs)
- Support BonkBot : [support@bonkbot.io](mailto:support@bonkbot.io)
- Issues GitHub : [github.com/yourusername/issues](https://github.com/yourusername/issues)

---

✅ **Le bot est maintenant opérationnel !** Surveillez les alertes Telegram pour les opportunités de trading.
