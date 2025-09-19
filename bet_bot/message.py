import time
import logging
import requests
from bet_bot.constants import TELEGRAM_BET_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def send(
    message: str,
    chat_id: str = TELEGRAM_CHAT_ID,
    token: str = TELEGRAM_BET_BOT_TOKEN
    ):

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True
    }

    response = requests.post(url, data=data)
    try:
        response_data = response.json()
    except ValueError:
        logger.error("Resposta do Telegram não é JSON:")
        logger.error(response.text)
        return None, None

    if response.ok and response_data.get('ok'):
        message_id = response_data['result']['message_id']
        logger.info(f"Telegram message sent successfully. ID: {message_id}")
        return message_id, TELEGRAM_CHAT_ID

    # checa rate limit via status_code
    if response.status_code == 429:
        logger.warning("Too Many Requests, sleeping...")
        retry_after = response_data.get("parameters", {}).get("retry_after", 60)
        time.sleep(retry_after + 1)
        return None, None

    # erro genérico
    logger.error("Telegram message not sent")
    logger.error(f"Status code: {response.status_code}")
    logger.error(f"Response: {response_data}")
    return None, None


def edit(
    message_id: str,
    message: str, 
    chat_id: str = TELEGRAM_CHAT_ID,
    token: str = TELEGRAM_BET_BOT_TOKEN
    ):

    url = f"https://api.telegram.org/bot{token}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True
    }

    response = requests.post(url, data=data)
    try:
        response_data = response.json()
    except ValueError:
        logger.error(f"Resposta inválida ao editar mensagem {message_id}: {response.text}")
        return False

    if response.ok and response_data.get('ok'):
        logger.info(f"Message {message_id} edited successfully.")
        return True

    if response.status_code == 429:
        logger.warning("Too Many Requests ao editar, sleeping...")
        retry_after = response_data.get("parameters", {}).get("retry_after", 60)
        time.sleep(retry_after + 1)
        return False

    logger.error(f"Error editing message {message_id}: {response.status_code} - {response_data}")
    return False
