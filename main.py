import logging
import threading
from model import get
from data import update
from datetime import datetime
from processes import scanner
from utils.utils import print_separator


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
        level=logging.INFO,
        #filename=f'{now}.log',
        #filemode='w',
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    print_separator()
    logging.info(f'\nStarting Striker Betting Bot...')
    print_separator()
    
    #update.fill_data_gaps()

    model = get.get_model()

    scanner.run(model=model, i=25)