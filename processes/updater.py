import time
import logging
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

        update.historic_data(ended)
        update.error_events(error_events)
        update.not_ended(not_ended)
