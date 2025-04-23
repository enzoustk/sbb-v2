import ast
import time
import logging
from processes import circuit
from object.bet import Bet
from data import load, update
from files.paths import LOCK

logger = logging.getLogger(__name__)

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

    logger.debug('Starting Updater..')
    existing_bets = {}

    with LOCK:
        events_to_update = load.data('not_ended')
        logger.debug(f'Updating data for {len(events_to_update)} events')
        
        if events_to_update.empty:
            logger.debug('No events to Update.')
            return

        ended = []
        not_ended = []
        error_events = [] 

        for match_data in events_to_update.to_dict('records'):
            event_id = match_data.get('event_id')

            if 'event' in match_data:
                try:
                    event_str = match_data['event'].replace("'", '"')
                    event = ast.literal_eval(event_str)
                except Exception as e:
                    logging.exception(f"Error formatting 'event': {e}")
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
                match.handle_ended_bet()
                time.sleep(1)
                match.mark_processed()
                existing_bets.pop(event_id, None)

            if match.totally_processed is True: 
                ended.append(match)

            elif match.totally_processed is False: 
                error_events.append(match)

            elif match.totally_processed is None: 
                not_ended.append(match)

            else: 
                logger.error(
                    f'Total Processing: Labeling Error for Event'
                    f' {match.event_id}'
                    )
            

        update.historic_data(ended)
        update.error_events(error_events)
        update.not_ended(not_ended)

        """
        circuit.breaker(
            threshold=-10,
            hours=16
        )
        """