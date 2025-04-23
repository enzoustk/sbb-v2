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
    response_data = response.json()

    if response.ok and response.json().get('ok'):
        message_id = response.json()['result']['message_id']
        logger.info(f"Telegram message sent successfully. ID: {message_id}")
        return message_id, TELEGRAM_CHAT_ID
    else:
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
    if response.status_code == 200:
        edited = True
        return edited
    else:
        logger.error(f'Error editing message {message_id}: {response.status_code} - {response.text}')


