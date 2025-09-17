import os

BET_LEVEL = 15

LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'

BET_FORMAT = '%(asctime)s | %(name)s'

TELEGRAM_LOG_CHAT_ID = -1002343941988

LOG_PATHS = {
    'bet': os.path.join('files', 'logs', 'bet.log'),
    'error': os.path.join('files', 'logs', 'error.log')
}