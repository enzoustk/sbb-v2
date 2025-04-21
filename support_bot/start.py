import sys
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update


from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from support_bot.constants import SUPPORT_BOT_TOKEN
from object.daily_report import NormalReport



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[
        InlineKeyboardButton("Ver Relatório Mensal", callback_data='build_report')
    ]]
    
    await update.message.reply_text(
        "Seja Bem-vindo ao suporte da Striker.\nNo momento, só podemos construir "
        "um relatório Diário Idêntico ao do Canal Principal.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Confirma o clique
    
    if query.data == 'build_report':
        try:
            # Envia o relatório para o chat do usuário
            report = NormalReport()
            report.build_and_send(
                chat_id=query.message.chat_id,
                token= SUPPORT_BOT_TOKEN)  # <-- chat_id correto aqui
            
            # Feedback visual (opcional: edita a mensagem original)
            await query.edit_message_text("✅ Relatório mensal enviado! Verifique sua conversa.")
        except Exception as e:
            print(f"Erro ao enviar relatório: {e}")
            await query.edit_message_text("❌ Falha ao enviar o relatório. Tente novamente mais tarde.")

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    report = NormalReport()
    report.build_and_send(chat_id=str(update.message.chat_id))
    await update.message.reply_text("Relatório enviado com sucesso!")
    """
    except Exception as e:
        logger.error(f'Error Sending Report: {e}')
        await update.message.reply_text("Erro ao enviar relatório. Verifique os logs.")
    """
    
def main():
    # Configuração moderna usando Application Builder
    application = Application.builder().token(SUPPORT_BOT_TOKEN).build()
    
    # Registro dos handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.add_handler(CommandHandler('relatorio', relatorio))
    
    # Inicia o bot
    application.run_polling()

if __name__ == '__main__':
    main()