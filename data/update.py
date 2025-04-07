import os
import logging
import pandas as pd
from object.bet import Bet
from data import load
from api import fetch
from model.config import AJUSTE_FUSO
from files.paths import ALL_DATA, HISTORIC_DATA, NOT_ENDED, ERROR_EVENTS, LOCK


def historic_data(data: list):
    """Update HISTORIC_DATA.csv with new data."""

    existing_data = load.data('historic')
    
    exclude_keys = remove_columns_to_historic()
    new_data = [
        {key: value for key,
        value in bet.__dict__.items()
        if key not in exclude_keys}  
        for bet in data
    ]
    
    new_df = pd.DataFrame(new_data)
    
    if existing_data.empty:
        new_df.to_csv(HISTORIC_DATA, index=False)
    else:
        combined_df = pd.concat([existing_data, new_df], ignore_index=True)
        combined_df['time_sent'] = pd.to_datetime(combined_df['time_sent'], errors='coerce')
        combined_df = combined_df.sort_values(by='date', ascending=False)
        combined_df = combined_df.drop_duplicates()
        combined_df.to_csv(HISTORIC_DATA, index=False)
    
    logging.info('Historic data updated successfully.')

def fill_data_gaps(gap: int = 30):
    """Uses API to fill gaps in the when the model was not running."""

    with LOCK:
        all_data = load.data('all_data')
        all_data['time_sent'] = pd.to_datetime(all_data['time_sent']) + pd.Timedelta(hours=AJUSTE_FUSO)
        all_data['date'] = all_data['time_sent'].dt.normalize()
        
        dates_to_fetch = []
        processed_dates = set()

        for date, bloco in all_data.groupby('date'):
            if date in processed_dates:
                continue
            bloco = bloco.sort_values('time_sent')
            delta_t = bloco['time_sent'].diff()
            
            if len(bloco[delta_t > pd.Timedelta(minutes=gap)]) > 0:
                dates_to_fetch.append(date)
            
            processed_dates.add(date)

        matches_fetched = fetch.events_for_date(dates=dates_to_fetch)
        
    
        historic_data = pd.read_csv(HISTORIC_DATA)
        existing_all_data = pd.read_csv(ALL_DATA)
        existing_data = pd.concat([historic_data, existing_all_data], ignore_index=True)
        existing_data['time_sent'] = pd.to_datetime(existing_data['time_sent'])
        
        new_events = []
        for datapoint in matches_fetched:
            date = pd.to_datetime(datapoint['time_sent']).date()
            event_id = datapoint['event_id']
            
            if event_id in existing_data[existing_data['event_id'] == event_id]['event_id'].values:
                continue
            
            match = Bet()
            match.__dict__.update(datapoint)
            new_events.append(match.__dict__)
        
        if new_events:
            new_events_df = pd.DataFrame(new_events)
            new_events_df.to_csv(HISTORIC_DATA, mode='a', index=False, header=False)
            logging.info(f'{len(new_events)} novos eventos adicionados ao histórico.')

def not_ended(data: list):
    """Updates NOT_ENDED.csv with new data."""

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