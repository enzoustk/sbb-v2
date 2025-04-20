import logging
from logging_config. settings import configure_logging
from model import get
from processes import scanner


if __name__ == '__main__':
    """
    When Started, the code will:
    1- Fill the data gaps;  
    2- Turn on the scanner;
    3- If scanner finds a new event, it will call the predict function;
    4- If predict function finds a new event, it will call the updater function;

    """    

    configure_logging()

    logger = logging.getLogger(__name__)
    bet_logger = logging.getLogger('bet')


    logger.info(f'\nStarting Striker Betting Bot...')

    #update.fill_data_gaps()
    model = get.model()

    scanner.run(model=model, i=25)