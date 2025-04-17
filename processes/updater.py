import ast
import logging
import pandas as pd
from object.bet import Bet
from data import load, update
from files.paths import LOCK



def run():
    """
    Quando o scanner passar i execuções sem encontrar novos eventos,
    ele chama o updater para processar os eventos que estão no CSV.

    For NOT_ENDED data:
        Inputs results to match data
        If bet, updates pl and telegram message
        Saves all data to a csv file
        Saves made bets to xlsx
        Saves buggy matches to ERROR_EVENTS

    TODO: Create ERROR_EVENTS handling method
    """
    existing_bets = {}

    with LOCK:
        events_to_update = load.data('not_ended')
        not_ended, ended, error_events, made_bets = [], [], [], []
        print('arquivos carregados')
        for match_data in events_to_update.to_dict('records'):
            event_id = match_data.get('event_id')

            if 'event' in match_data:
                try:
                    event_str = match_data['event'].replace("'", '"')
                    event = ast.literal_eval(event_str)
                except Exception as e:
                    print(f"Erro ao converter 'event': {e}")
                    continue 

            if event_id in existing_bets:
                match: Bet = existing_bets[event_id]
                match.update_from_dict(match_data)
            
            else:
                match = Bet(event)
                match.update_from_dict(match_data)
                existing_bets[event_id] = match
        
            match._get_end()          
            
            if match.ended is True:    
                print(f'match {match.event_id} terminou, tratando')
                match.handle_ended_bet()
                match.mark_processed()
                existing_bets.pop(event_id, None)

                if match.bet_type is not None: 
                    made_bets.append(match)
                    match._save_made_bet()

            if match.totally_processed is True: 
                ended.append(match)

            elif match.totally_processed is False: 
                error_events.append(match)

            elif match.totally_processed is None: 
                not_ended.append(match)

            else: 
                logging.warning(
                    f'Total Processing: Labeling Error for Event'
                    f' {match.event_id}'
                    )

        update.historic_data(ended)
        update.error_events(error_events)
        update.not_ended(not_ended)
        
        if made_bets is not None:
            logging.info(f'Added {len(made_bets)} bets to xlsx.')
        