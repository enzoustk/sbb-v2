def generate(data):
    
    from constants.telegram_params import (
    TELEGRAM_MESSAGE,MIN_LINE_MESSAGE,MIN_ODD_MESSAGE)
    from model.config import (HOT_THRESHOLD, HOT_TIPS_STEP, MAX_HOT)

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
    from constants import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    import requests, logging

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }

    response = requests.post(url, data=data)

    if response.ok and response.json().get('ok'):
        logging.info("Telegram message sent successfully")
        message_id = response.json()['result']['message_id']
        return message_id
    else:
        logging.error("Telegram message not sent")
        return None