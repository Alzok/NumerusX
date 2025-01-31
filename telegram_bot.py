from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler
import logging
from config import Config

class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=Config.TG_TOKEN)
        self.updater = Updater(token=Config.TG_TOKEN)
        self._setup_handlers()
    
    def _setup_handlers(self):
        # Configuration des commandes
        pass
    
    def send_alert(self, message):
        pass