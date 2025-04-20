import logging
from files.paths import LOG_PATHS


BET_LEVEL = 15
LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
BET_FORMAT = '%(asctime)s | %(name)s'
LOG_FILES = {
    'bet': LOG_PATHS['bet'],
    'error': LOG_PATHS['error']
}


logging.addLevelName(BET_LEVEL, 'BET')

def log_bet(self, message, *args, **kwargs):
    if self.isEnabledFor(BET_LEVEL):
        self._log(BET_LEVEL, message, args, **kwargs)

logging.Logger.bet = log_bet


class BetFilter(logging.Filter):
    """Filtra apenas logs do nível BET"""
    def filter(self, record):
        return record.levelno == BET_LEVEL


def create_console_handler():
    """Handler para output no terminal"""
    handler = logging.StreamHandler()
    handler.setLevel(BET_LEVEL)
    return handler

def create_bet_handler():
    """Handler específico para logs BET com formatação customizada"""
    handler = logging.FileHandler(LOG_FILES['bet'])
    handler.setLevel(BET_LEVEL)
    handler.addFilter(BetFilter())
    
    bet_formatter = logging.Formatter(BET_FORMAT, datefmt='%d-%m %H:%M:%S')
    handler.setFormatter(bet_formatter)
    
    return handler


def create_error_handler():
    """Handler para logs de erro (WARNING+)"""
    handler = logging.FileHandler(LOG_FILES['error'])
    handler.setLevel(logging.WARNING) 
    return handler


def configure_logging():
    formatter = logging.Formatter(LOG_FORMAT, datefmt='%d-%m %H:%M:%S')

    handlers = {
        'bet': create_bet_handler(),
        'console': create_console_handler(),
        'error': create_error_handler(),
    }

    for handler in handlers.values():
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(BET_LEVEL)

    root_logger.addHandler(handlers['console'])
    root_logger.addHandler(handlers['error'])


    bet_logger = logging.getLogger('bet')
    bet_logger.addHandler(handlers['bet'])
    bet_logger.propagate = True