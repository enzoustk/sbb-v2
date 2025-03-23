def send_telegram_message(message):
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