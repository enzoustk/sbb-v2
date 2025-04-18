import requests, logging
from model.betting_config import HOT_THRESHOLD, HOT_TIPS_STEP, MAX_HOT
from bet_bot.constants import TELEGRAM_BET_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_MESSAGE,MIN_LINE_MESSAGE,MIN_ODD_MESSAGE


def generate(data):
    
    """
    1- Create template message;
    2- Build minimum line message;
    3- Build EV message;
    Return message;
    """

    message = TELEGRAM_MESSAGE.format(**data)
    
    if data['handicap'] == data['minimum_line']:
        message += MIN_ODD_MESSAGE.format(**data)
    
    elif data['handicap'] != data['minimum_line']:
        message += MIN_LINE_MESSAGE.format(**data)
    
    else: raise ValueError(f"Linha inválida: {data['handicap']} != {data['minimum_line']}")

    
    _ev = data['ev']
    i = 0
    if _ev >= HOT_THRESHOLD: 
        message += f"\n⚠️ EV:"
    
    while True:
        if _ev >= HOT_THRESHOLD:
            message += "🔥"
            _ev -= HOT_TIPS_STEP
            i += 1
        if i == MAX_HOT: break
        else: break
    
    message += "\n"

    return message


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
