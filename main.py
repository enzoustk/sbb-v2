import logging
import threading
from datetime import datetime
from data import update
from processes import scanner


if __name__ == '__main__':
    """
    When Started, the code will:
    1- Fill the data gaps;  
    2- Turn on the scanner;
    3- If scanner finds a new event, it will call the predict function;
    4- If predict function finds a new event, it will call the updater function;

    """
    now = datetime.now().strftime("%d-%m %H%M%S")
    logging.basicConfig(
        level=logging.WARNING,
        filename=f'{now}.log',
        filemode='w',
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info('Starting updater...')
    logging.info('Filling data gaps...')
    
    update.fill_data_gaps()

    scanner.run(model='', i=50)