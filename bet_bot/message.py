import logging
import requests
from bet_bot.constants import TELEGRAM_BET_BOT_TOKEN, TELEGRAM_CHAT_ID


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
        logging.info("Telegram message sent successfully")
        message_id = response.json()['result']['message_id']
        return message_id, TELEGRAM_CHAT_ID
    else:
        logging.error("Telegram message not sent")
        logging.error(f"Status code: {response.status_code}")
        logging.error(f"Response: {response_data}")
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
        logging.error(f'Error editing message {message_id}: {response.status_code} - {response.text}')


