import asyncio
from nicegui import ui
from dex_bot import DexBot
from gui import TradingDashboard
from config import Config
import logging
import os

async def main():
    # Configuration initiale
    os.makedirs('data', exist_ok=True)
    
    # Initialisation du bot
    bot = DexBot()
    dashboard = TradingDashboard(bot)
    dashboard.create()
    
    # Boucle principale
    await ui.run_until_disconnected()

if __name__ in ["__main__", "__mp_main__"]:
    logging.basicConfig(level=Config.LOG_LEVEL)
    asyncio.run(main())