import logging
import requests
from bet_bot.constants import TELEGRAM_BET_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def send(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_BET_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }

    response = requests.post(url, data=data)
    response_data = response.json()

    if response.ok and response.json().get('ok'):
        logger.info("Telegram message sent successfully")
        message_id = response.json()['result']['message_id']
        return message_id, TELEGRAM_CHAT_ID
    else:
        logger.error("Telegram message not sent")
        logger.error(f"Status code: {response.status_code}")
        logger.error(f"Response: {response_data}")
        return None, None


def edit(message_id, message, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BET_BOT_TOKEN}/editMessageText"
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


