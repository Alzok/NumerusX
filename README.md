# 📘 Documentation d'Installation du DEX Trading Bot

![Logo](logo.webp)

## Prérequis

### 🖥️ Configuration Système
- **Système d'exploitation** : Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Python** : 3.10 ou supérieur ([Télécharger Python](https://www.python.org/downloads/))
- **Git** ([Guide d'installation](https://git-scm.com/book/fr/v2/D%C3%A9marrage-rapide-Installation-de-Git))

### 🔑 Clés API Requises

| Service      | Lien d'Obtention |
|-------------|------------------|
| Infura      | [https://infura.io/register](https://infura.io/register) |
| Etherscan   | [https://etherscan.io/apis](https://etherscan.io/apis) |
| Banana Gun  | [https://bananagun.io/api](https://bananagun.io/api) |
| Telegram Bot | [https://t.me/BotFather](https://t.me/BotFather) |

---

## 🛠 Installation Pas à Pas

### 1. Cloner le Dépôt

```bash
git clone https://github.com/votre-utilisateur/dex-trading-bot.git
cd dex-trading-bot
```

### 2. Configurer l'Environnement Virtuel

#### Linux/macOS :

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows :

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

## 🔧 Configuration

### 1. Fichier d'Environnement

```bash
cp .env.example .env
```

Remplir `.env` avec vos clés :

```ini
TELEGRAM_TOKEN="123456:ABC-DEF..."
BANANA_GUN_KEY="bg_live_votre_clé"
INFURA_KEY="votre_clé_infura"
```

### 2. Initialiser la Base de Données

```bash
sqlite3 dex_analytics.db < schema.sql
```

## 🤖 Configuration Telegram

### 1. Créer un Bot

- Ouvrez [@BotFather](https://t.me/BotFather) sur Telegram
- Envoyez `/newbot` et suivez les instructions
- Copiez le token dans `.env`

### 2. Obtenir le Chat ID

- Ajoutez le bot à un canal/groupe
- Envoyez un message
- Exécutez :

```bash
curl https://api.telegram.org/bot$TELEGRAM_TOKEN/getUpdates
```

- Cherchez `"id":-10012345...` dans la réponse

## 🚀 Lancer le Bot

### Mode Démo (Sans Trading Réel)

```bash
python dex_bot.py --demo
```

### Mode Production

```bash
nohup python dex_bot.py >> trading.log 2>&1 &
```

### Vérifier les Logs

```bash
tail -f trading.log
```

## 🛡️ Recommandations de Sécurité

### Clés API :
- Ne jamais commiter `.env`
- Utiliser des clés avec permissions minimales

### VPN :
- Toujours actif pendant l'exécution

### Backups :
- Automatiser les backups de `dex_analytics.db`

```bash
0 3 * * * cp dex_analytics.db backups/$(date +\%Y\%m\%d).db
```

## 🔍 Dépannage

### Problèmes Courants

| Symptôme                  | Solution |
|---------------------------|----------|
| API Error 429             | Réduire la fréquence des requêtes |
| Database Locked           | Redémarrer le bot |
| Invalid Telegram Token    | Vérifier le format `123456:ABC-DEF...` |

### Commandes Utiles

```bash
# Vérifier l'intégrité de la DB
sqlite3 dex_analytics.db "PRAGMA integrity_check"

# Forcer un reload des blacklists
pkill -SIGHUP -f dex_bot.py
```

## 📚 Ressources Complémentaires

- [Documentation Banana Gun](https://bananagun.io/docs)
- [Guide DexScreener API](https://docs.dexscreener.com/)
- [Support Technique](https://support.dextradingbot.com)

---

✅ **Installation Terminée !** Le bot est maintenant prêt à analyser les marchés et exécuter des trades sécurisés.
