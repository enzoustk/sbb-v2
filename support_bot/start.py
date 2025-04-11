from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from support_bot.constants import SUPPORT_BOT_TOKEN

def start(update: Update):
    buttons = [
        [InlineKeyboardButton("Construir Relatório Personalizado", callback_data='build_report')]
    ]
    
    update.message.reply_text(
        "Seja Bem-vindo ao suporte da Striker.\n Escolha uma Ação.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == 'build_report':
        query.edit_message_text("Você clicou em Construir um Relatório?")


updater = Updater(SUPPORT_BOT_TOKEN)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(handle_button))

updater.start_polling()
updater.idle()