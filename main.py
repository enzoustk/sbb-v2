import logging
from data import update
from threads import threads


"""
Thread 1:   Scanner no Pau o tempo todo

Thread 2:   0. |Ao ligar o código: fill_data_gaps;
            1. |Lê JSON not_ended;
                1.1 |Se tiver jogo com aposta feita, time.sleep (60s):
                        1.1.1 | Ficar procurando placar p/ Processar;
                1.2 | Else: tenta processar todos os not_ended sem aposta

Thread 3:   Envia o Relatório todo dia 00:00

Thread 4?   Retreinar o Modelo
"""
def main():
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

    threads.scanner(model='', i=500)










if __name__ == '__main__':
    main()