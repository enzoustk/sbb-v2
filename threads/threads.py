import time
import logging
from object.bet import Bet
from object.report import DailyReport

from api import fetch
from model import predict
from data import load, update
from utils import csv_atualizado_event


def scanner(model, i: int = 500):
    """Scans all live events and handles them
    
    Arguments:
        model: ML Model used to predict match odds
        i (int): After i runs, it shows a message to assert it is 
        running properly
    """

    iwnne = 0  # Iteration with no new events
    read_matches = set()

    if not csv_atualizado_event.is_set():
        logging.info('Waiting for csv file to be updated')
        csv_atualizado_event.wait()

    while True:
        
        live_matches = fetch.live_events()
        unread_matches = [match 
                        for match in live_matches 
                        if match['id'] not in read_matches
        ]
        
        if not unread_matches:
            iwnne += 1
            if iwnne % i == 0:
                updater()
                logging.info(f'{i} scans made. No new event found.')

        try:
            df = load.data('csv')
            for match in unread_matches:
                predict.match(df=df,
                            event=match,
                            model=model,
                )
                read_matches.add(match['id'])
            iwnne = 0


        except Exception as e:
            logging.error(f'Error predicting match {match['id']}\n{e}')

def updater(time_sleep: int = 60):
    """
    For NOT_ENDED data:
        Inputs results to match data
        If bet, updates pl and t    elegram message
    Saves all data to a csv file
    Saves made bets to xlsx
    Saves buggy matches to ERROR_EVENTS

    Deve ser avisado por algum outro código que tem o que procurar;
    Fica no Loop Infinito procurando o que processar;
    Se não tiver nada, espera 60s e tenta de novo.
    Se tiver, processa tudo e salva no CSV;
    Se ele processar tudo, quebra o loop e precisa ser chamado de novo;


    TODO: Create ERROR_EVENTS handling method
    """
    
    existing_bets = {}

    while True:
        events_to_update = load.data('not_ended')
        not_ended, ended, error_events, made_bets = [], [], [], []

        for match_data in events_to_update.to_dict('records'):
            event_id = match_data.get('event_id')

           
            if event_id in existing_bets:
                match = existing_bets[event_id]
                match.__dict__.update(match_data) 
            
            else:
                match = Bet()
                match.__dict__.update(match_data)
                existing_bets[event_id] = match

        
            match._get_end()

            if match.ended:
                match.handle_ended_bet()
                match.save_made_bet()
                match.mark_processed()
                existing_bets.pop(event_id, None)

            if match.totally_processed: 
                ended.append(match)

            if match.bet_type is not None: 
                made_bets.append(match)

            elif not match.totally_processed: 
                error_events.append(match)

            elif match.totally_processed is None: 
                not_ended.append(match)

            else: 
                logging.warning(
                    f'Total Processing: Labeling Error for Event'
                    f' {match.event_id}'
                    )

        update.csv(ended)
        update.error_events(error_events)
        update.not_ended(not_ended)

        if len(not_ended) == 0:
            break

        time.sleep(time_sleep)

def send_report():
    return DailyReport().send()