from data import load
import pandas as pd
from files.paths import ALL_DATA, ERROR_EVENTS, NOT_ENDED
import logging
import os
from object.bet import Bet

def handle_not_ended_events(self):
    """Processa eventos não finalizados usando CSV."""
    try:
        not_ended_df = pd.read_csv(NOT_ENDED)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        not_ended_df = pd.DataFrame()

    ended_data, error_data = [], []

    for _, row in not_ended_df.iterrows():
        bet = Bet()
        bet.__dict__.update(row.to_dict())
        bet._get_end()

        if bet.ended:
            try:
                bet.finish_processing()
                ended_data.append(bet.__dict__)
            except Exception as e:
                logging.error(f"Erro ao processar evento {bet.event_id}: {e}")
                error_data.append(bet.__dict__)

    # Salva dados finalizados
    if ended_data:
        ended_df = pd.DataFrame(ended_data)
        ended_df.to_csv(ALL_DATA, mode='a', index=False, header=not os.path.exists(ALL_DATA))

    # Salva erros
    if error_data:
        error_df = pd.DataFrame(error_data)
        error_df.to_csv(ERROR_EVENTS, mode='a', index=False, header=not os.path.exists(ERROR_EVENTS))

    # Atualiza NOT_ENDED.csv
    not_ended_df = not_ended_df[~not_ended_df['event_id'].isin([bet['event_id'] for bet in ended_data + error_data])]
    not_ended_df.to_csv(NOT_ENDED, index=False)