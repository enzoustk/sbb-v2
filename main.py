from threads import threads
from data import update

def main():
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

def thread_1():  # Scanner
    threads.scanner(model='', i=500)

def thread_2():  # Updater
    update.fill_data_gaps
    









if __name__ == '__main__':
    main()