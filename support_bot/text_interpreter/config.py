import ollama
import re
from telegram import Update
from get_file import get_markdown, get_txt
from telegram.ext import ContextTypes

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from constants import OLLAMA_MODEL


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Olá! Bem Vindo à Striker. Pergunte o que quiser.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    try:
        user_input = update.message.text
        
        # Carrega contexto do Markdown
        md_context = get_markdown()
        txt_context = get_txt()
        
        # Gera resposta com Ollama usando o contexto
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": md_context},
                {"role": "system", "context": txt_context},
                {"role": "user", "content": user_input}
            ],
            stream=False
        )
        
        # Remove possíveis blocos <think> e formata a resposta
        clean_response = re.sub(r'<think>.*?</think>', '', response['message']['content'], flags=re.DOTALL).strip()
        
        await update.message.reply_text(clean_response)
        
    except Exception as e:
        error_message = f"⚠️ Erro: {str(e)}"
        await update.message.reply_text(error_message)