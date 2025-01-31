import asyncio
import logging
import signal
import sys
from nicegui import ui
from logging.handlers import RotatingFileHandler
from dex_bot import DexBot
from gui import TradingDashboard
from config import Config
from logger import DexLogger

def configure_logging():
    """Configuration avancée du système de logging"""
    logger = logging.getLogger()
    logger.setLevel(Config.LOG_LEVEL)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler pour fichiers logs
    file_handler = RotatingFileHandler(
        'data/numerusx.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def check_environment():
    """Vérifie les variables d'environnement requises"""
    required_vars = ['ENCRYPTION_KEY', 'ENCRYPTED_SOLANA_PK']
    missing = [var for var in required_vars if not getattr(Config, var, None)]
    
    if missing:
        logging.critical(f"Variables manquantes: {', '.join(missing)}")
        sys.exit(1)

async def shutdown():
    """Arrêt propre de l'application"""
    logging.info("Arrêt en cours...")
    await ui.shutdown()
    logging.info("Nettoyage terminé")
    sys.exit(0)

def handle_signals():
    """Gestion des signaux système"""
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: asyncio.create_task(shutdown()))

async def main():
    """Point d'entrée principal de l'application"""
    try:
        # Configuration initiale
        configure_logging()
        check_environment()
        handle_signals()

        logging.info("Initialisation du bot...")
        bot = DexBot()
        
        logging.info("Préparation de l'interface...")
        dashboard = TradingDashboard(bot)

        # Mise à jour asynchrone des données
        async def update_loop():
            while True:
                dashboard.update_dashboard()
                await asyncio.sleep(Config.UI_UPDATE_INTERVAL)

        asyncio.create_task(update_loop())

        logging.info("Démarrage de l'interface utilisateur...")
        await ui.run_until_disconnected()

    except Exception as e:
        logging.critical(f"Erreur critique: {str(e)}", exc_info=True)
        await shutdown()

if __name__ in ["__main__", "__mp_main__"]:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Arrêt par l'utilisateur")
        sys.exit(0)