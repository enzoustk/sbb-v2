import logging
import threading
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
    
    logging.info('Starting updater...')
    logging.info('Filling data gaps...')
    
    update.fill_data_gaps()

    scanner.run(model='', i=50)