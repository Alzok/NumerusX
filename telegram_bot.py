from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler

class TelegramInterface:
    def __init__(self):
        self.bot = Bot(token=Config.TG_TOKEN)
        self.updater = Updater(token=Config.TG_TOKEN)
        
    def alert(self, message):
        self.bot.send_message(
            chat_id=Config.TG_CHAT_ID,
            text=f"🚨 {message}",
            parse_mode="Markdown"
        )
    
    def start(self):
        self.updater.start_polling()