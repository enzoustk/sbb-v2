def save_bet(data):
 
    from utils import planilha_lock

    with planilha_lock:
        
        """
        1- Converts EV percentage to "hot_ev";
        2- Adjusts time by subtracting 3 hours;
        3- Creates a new DataFrame with the data;
        4- Saves the new DataFrame to an Excel file;
        """
        from constants.telegram_params import HOT_THRESHOLD, HOT_TIPS_STEP, MAX_HOT
        
        i = 0
        hot_ev = 0
        _ev = data['ev']

        while True:
            if _ev >= HOT_THRESHOLD:
                hot_ev += 1
                i += 1
                _ev -= HOT_TIPS_STEP
            
            if i == MAX_HOT: break
            
            else: break

        
        
        """
        Ajusta o horário para reduzir 3 horas;
        TODO: Remover hardcode de 3 horas
        """
        import pandas as pd
        time_sent = pd.to_datetime(time_sent) - pd.Timedelta(hours=3)
        
        event_data = {
            'event_id': [data['event_id']],
            'time_sent': [time_sent],
            'league': [data['league']],
            'home_team': [data['home_team']],
            'home_player': [data['home_player']],
            'away_team': [data['away_team']],
            'away_player': [data['away_player']],
        }

        bet_data = {
            'bet_type': [data['bet_type']],
            'handicap': [data['handicap']],
            'odd': [data['odd']],
            'ev': [data['ev']],
            'hot_ev': [hot_ev],
            'line_min': [data['minimum_line']],
            'odd_min': [data['minimum_odd']],
        }

        message_data = {
            'message_id': [data['message_id']],
            'edited': None,
            'canceled': None,
        }

        result_data = {
            'pl': None,
            'final_score': None,
        }

        new_bet = {
            **event_data,
            **bet_data,
            **result_data,
            **message_data,
        }

        try:
            from files.paths import MADE_BETS
            file = pd.read_excel(MADE_BETS)
            file.append(new_bet, ignore_index=True)
        
        except FileNotFoundError:
            import logging
            logging.warning(f"File not found: {MADE_BETS}. Creating a new file.")
            file = pd.DataFrame(new_bet)

        file.to_excel(MADE_BETS, index=False)
        logging.info(f"New bet saved in: {MADE_BETS}")

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
                    from model.calculate import calculate_pl

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

def update_dataframe():
    pass
