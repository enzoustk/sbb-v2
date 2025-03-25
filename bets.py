bets.py

def add_new_bets():
    from utils import planilha_lock
    with planilha_lock:
        
        try:
            import pandas as pd
            from files.paths import MADE_BETS
            
            """
            Verifica se há eventos para serem atualizados;
            Verifica se o evento está ao vivo;
            Verifica se o evento foi enviado a mais de 8 minutos;
            Verifica se o placar é válido;
            Se houver, processa e atualiza os dados;
            """

            made_bets = pd.read_excel(MADE_BETS)
            old_made_bets = made_bets.copy()
            
            from utils import events_to_update
            new_events = events_to_update()

            for index, event in new_events.iterrows():
                
                try:
                    import logging
                    from datetime import datetime, timedelta
                    from api_requests.fetch import fetch_events_for_id

                    event_id = event['event_id']
                    logging.info(f"Processing event ID: {event_id}")

                    event_data = fetch_events_for_id(event_id)
                    score_final = event_data.get('ss', None)
                    time_sent = pd.to_datetime(event['Horário Envio'])
                    
                    if not datetime.now() - time_sent > timedelta(minutes=8):
                        logging.info(f"Match ID {event_id} too recent. Ignoring for now.")
                        continue
                        
                    if score_final or '-' not in score_final:
                        logging.warning(f"Placar inválido ou ausente para o evento {event_id}.")
                        continue

                    home_score, away_score = map(int, score_final.split('-'))
                    made_bets.at[index, 'final_score'] = f"{home_score}-{away_score}"

                    bet_type = float(event['bet_type'])
                    handicap = float(event['handicap'])
                    odd = float(event['odd'])
                    profit = calculate_pl(bet_type=bet_type, handicap=handicap, odd=odd, home_score=home_score, away_score=away_score)
                    made_bets.at[index, 'pl'] = profit

                except Exception as e:
                    logging.error(f"Error processing event ID {event_id}: {e}")
                    continue

            if not made_bets == old_made_bets:
                made_bets.to_excel(MADE_BETS, index=False)
                logging.info(f"Updated {MADE_BETS} with new bets.")
        
        except Exception as e:
            logging.error(f"Error updating {MADE_BETS}: {e}")

def events_to_update():
    from api_requests.fetch import fetch_live_events
    from files.paths import MADE_BETS
    live_events = fetch_live_events()

    live_events_ids = {str(event['id']) for event in live_events}
    MADE_BETS['event_id'] = MADE_BETS['event_id'].astype(str)

    new_events = MADE_BETS['final_score'].isna()
    new_events = new_events.drop_duplicates(subset=['event_id'])
    new_events = new_events[~new_events['event_id'].isin(live_events_ids)]
    
    return new_events

def write_excel(self):
    import pandas as pd
    from files.paths import MADE_BETS
    
    try:
        file = pd.read_csv(MADE_BETS)
        file = file.append(self.__dict__, ignore_index=True)

    except FileNotFoundError as e:
        import logging
        logging.warning(f'File {MADE_BETS} found, creating new file')
        file = pd.DataFrame(self.__dict__)

    file.to_excel(MADE_BETS, index=False)
    logging.info(f"Bet {self.event_id} saved")