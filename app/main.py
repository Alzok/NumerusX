import asyncio
import logging
from nicegui import ui
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from dex_bot import DexBotPro
from gui import TradingGUI
from config import Config
from logger import DexLogger

# Configuration thread-safe pour les logs
log_queue = Queue(-1)
logging.basicConfig(handlers=[QueueHandler(log_queue)], level=Config.LOG_LEVEL)

async def main():
    # Initialisation des composants
    bot = DexBotPro()
    gui = TradingGUI(bot)
    
    # Configuration du système de logs
    file_handler = RotatingFileHandler(
        'data/trading.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    listener = QueueListener(log_queue, file_handler)
    listener.start()
    
    try:
        # Création de l'interface
        gui.create_interface()
        
        # Mise à jour périodique
        ui.timer(Config.GUI_REFRESH_RATE, lambda: update_display())
        
        await ui.run_until_disconnected()
    finally:
        listener.stop()
        bot.stop()

def update_display():
    """Actualise l'interface de manière sécurisée"""
    try:
        with open('data/trading.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()[-50:]
            gui.log.content = '\n'.join(lines)
    except Exception as e:
        logging.error(f"Erreur d'actualisation : {str(e)}")

if __name__ in ["__main__", "__mp_main__"]:
    asyncio.run(main())