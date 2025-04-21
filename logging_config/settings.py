import logging
from bet_bot import message
from logging_config.constants import(
    BET_LEVEL, LOG_FORMAT, BET_FORMAT, 
    TELEGRAM_LOG_CHAT_ID, LOG_PATHS
)

logging.addLevelName(BET_LEVEL, 'BET')

class TelegramMessageHandler(logging.Handler):
    """Handler customizado que usa seu módulo message para enviar logs"""
    def emit(self, record):
        try:
            log_message = self.format(record)
            message.send(message=log_message, chat_id=TELEGRAM_LOG_CHAT_ID)
        except Exception as e:
            logging.getLogger().error(f"Erro no handler Telegram: {str(e)}", exc_info=True)

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
    handler = logging.FileHandler(LOG_PATHS['bet'])
    handler.setLevel(BET_LEVEL)
    handler.addFilter(BetFilter())
    
    bet_formatter = logging.Formatter(BET_FORMAT, datefmt='%d-%m %H:%M:%S')
    handler.setFormatter(bet_formatter)
    
    return handler

def create_error_handler():
    """Handler para logs de erro (WARNING+)"""
    handler = logging.FileHandler(LOG_PATHS['error'])
    handler.setLevel(logging.WARNING)
    return handler

def create_telegram_handler():
    """Novo handler usando seu módulo message"""
    handler = TelegramMessageHandler()
    handler.setLevel(logging.WARNING)
    return handler

def configure_logging():
    formatter = logging.Formatter(LOG_FORMAT, datefmt='%d-%m %H:%M:%S')

    handlers = {
        'bet': create_bet_handler(),
        'console': create_console_handler(),
        'error': create_error_handler(),
        'telegram': create_telegram_handler()
    }

    for name, handler in handlers.items():
        if handler and name != 'bet':
            handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(BET_LEVEL)

    # Adiciona handlers principais
    root_logger.addHandler(handlers['console'])
    root_logger.addHandler(handlers['error'])
    root_logger.addHandler(handlers['telegram'])

    # Configura logger específico para BET
    bet_logger = logging.getLogger('bet')
    bet_logger.addHandler(handlers['bet'])
    bet_logger.propagate = True