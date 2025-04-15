import os
import logging
import pandas as pd
from object.bet import Bet
from data import load
from api import fetch
from model.betting_config import AJUSTE_FUSO
from files.paths import HISTORIC_DATA, NOT_ENDED, ERROR_EVENTS, LOCK


def historic_data(data: list):
    """Update HISTORIC_DATA.csv with new data."""

    # Funções já definidas em outros locais do código
    existing_data = load.data('historic')
    existing_data['date'] = pd.to_datetime(existing_data['date'])
    exclude_keys = remove_columns_to_historic()
    
    new_data = [
        {key: value for key,
        value in bet.__dict__.items()
        if key not in exclude_keys}  
        for bet in data
    ]
    
    new_df = pd.DataFrame(new_data)
    new_df['date'] = pd.to_datetime(new_df['date'])
    new_df = new_df.sort_values(by='date')
    

    combined_df = pd.concat([existing_data, new_df], ignore_index=True)
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    



def fill_data_gaps(gap: int = 30):
    """Uses API to fill gaps in the when the model was not running."""

    with LOCK:
        
        existing_data = load.data('historic_data')

        if existing_data.empty or 'time_sent' not in existing_data.columns:
            logging.warning("DataFrame 'existing_data' is empty. skipping data gaps fill.")
            return 

        existing_data['time_sent'] = pd.to_datetime(existing_data['time_sent']) + pd.Timedelta(hours=AJUSTE_FUSO)
        existing_data['date'] = existing_data['time_sent'].dt.normalize()
        
        dates_to_fetch = []
        processed_dates = set()

        for date, bloco in existing_data.groupby('date'):
            if date in processed_dates:
                continue
            bloco = bloco.sort_values('time_sent')
            delta_t = bloco['time_sent'].diff()
            
            if len(bloco[delta_t > pd.Timedelta(minutes=gap)]) > 0:
                dates_to_fetch.append(date)
            
            processed_dates.add(date)

        matches_fetched = fetch.events_for_date(
            dates=dates_to_fetch
        )
        
        new_events = []
        
        for datapoint in matches_fetched:
            event_id = datapoint['event_id']
            
            if event_id in existing_data['event_id'].values:
                continue
            
            match = Bet(datapoint)
            match.__dict__.update(datapoint)
            new_events.append(match.__dict__)
        
        if new_events:
            new_events_df = pd.DataFrame(new_events)

            final_df = pd.concat([existing_data, new_events_df])
            final_df = final_df.drop_duplicates()
            final_df['date'] = pd.to_datetime(final_df['date'])   
            final_df = final_df.sort_values(by='date')

            final_df.to_csv(HISTORIC_DATA, mode='w', index=False)
            logging.info(f'{len(new_events)} novos eventos adicionados ao histórico.')


def not_ended(data: list):
    """Updates NOT_ENDED.csv with new data."""
    if not data:
        pd.DataFrame().to_csv(NOT_ENDED, index=False)
        logging.info('All not ended data fully processed')
        return
    
    ne_df = pd.DataFrame([bet.__dict__ for bet in data])
    ne_df.to_csv(NOT_ENDED, index=False)
    logging.info('Eventos não finalizados atualizados com sucesso.')


def error_events(data: list):
    """Updates ERROR_EVENTS.csv with new data."""

    error_df = pd.DataFrame([event.__dict__ for event in data])
    
    
    header = not os.path.exists(ERROR_EVENTS)
    
    error_df.to_csv(ERROR_EVENTS, mode='a', index=False, header=header)
    logging.info('Eventos com erro adicionados ao arquivo.')


def remove_columns_to_historic():
    """Returns columns to be removed from historic data."""
    return {'event', 'hot_emoji', 'message', 'bet_type_emoji'}