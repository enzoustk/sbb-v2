import os
from dotenv import load_dotenv

load_dotenv()

BET_LEVEL = 15

LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'

BET_FORMAT = '%(asctime)s | %(name)s'

TELEGRAM_LOG_CHAT_ID = int(os.environ.get("TELEGRAM_LOG_CHAT_ID", "0"))

LOG_PATHS = {
    'bet': r'files\logs\bet.log',
    'error': r'files\logs\error.log'
}