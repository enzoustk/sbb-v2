def main():

    from object.bet import Bet
    from data import update
    import logging
    import time
    from data import load

    '''
    For NOT_ENDED data:
        Inputs results to match data
        If bet, updates pl and telegram message
    Saves all data to a csv file
    Saves made bets to xlsx
    Saves buggy matches to ERROR_EVENTS
    TODO: Create ERROR_EVENTS handling method
    '''


    
    while True:
        etp = load.data('not_ended') # Events To Process
        not_ended, ended, error_events, made_bets = [], [], [], []



        for match_data in etp.to_dict('records'):
            match = Bet()
            match.__dict__.update(match_data)
            match._get_end()

            if match.ended:
                match.handle_ended_bet()
                match.save_made_bet()
                match.mark_processed()
            
            if match.totally_processed: ended.append(match)
            if match.bet_type is not None: made_bets.append(match)
            elif not match.totally_processed: error_events.append(match)
            elif match.totally_processed is None: not_ended.append(match)
            else: logging.warning(f'Tottaly Processing: Labeling Error for Event {match.event_id}')

        # Salva cada lista de dicionários no lugar certo
        update.csv(ended)
        update.error_events(error_events)
        update.not_ended(not_ended)

if __name__ == '__main__':
    main()