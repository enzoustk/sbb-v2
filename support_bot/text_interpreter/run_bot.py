from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import start, handle_message
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from support_bot.constants import SUPPORT_BOT_TOKEN

def main():
    app = Application.builder().token(SUPPORT_BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot em execução...")
    app.run_polling()

main()