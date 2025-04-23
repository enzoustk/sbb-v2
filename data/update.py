import os
import logging
import pandas as pd
from object.bet import Bet
from data import load
from api import fetch
from model.betting_config import AJUSTE_FUSO
from files.paths import MODELS, NOT_ENDED, ERROR_EVENTS, LOCK

logger = logging.getLogger(__name__)

"""
def historic_data(data: list):
    """"""Update HISTORIC_DATA.csv with new data.""""""

    if not data:
        logger.debug('No new ended events')
        return
    
    existing_data = load.data('historic')
    existing_data['date'] = pd.to_datetime(existing_data['date'])
    existing_data = existing_data.dropna(axis=1, how='all')
    exclude_keys = remove_columns_to_historic()
    
    new_data = [
        {key: value for key, value in bet.__dict__.items() if key not in exclude_keys}
        for bet in data
    ]

    if not new_data:
        logger.info('No data to update')
        return
    
    new_df = pd.DataFrame(new_data)
    new_df['date'] = pd.to_datetime(new_df['date'])
    new_df = new_df.sort_values(by='date')
    new_df = new_df.dropna(axis=1, how='all')

    if existing_data.empty:
        logger.debug('Existing historic data is empty, creating new file...')
        new_df.to_csv(HISTORIC_DATA, index=False)
        logger.info(f'Historic file created. {len(new_df)} matches added.')
    else:
        combined_df = pd.concat([existing_data, new_df])
        combined_df = combined_df.drop_duplicates(subset='event_id', keep='first')
        combined_df.to_csv(HISTORIC_DATA, index=False)
        logger.info(f'{len(new_df)} new matches added to ended events.')
"""


def historic_data(data: list):
    """Save new events to their respective CSV files based on MODELS' league_id."""
    
    if not data:
        logger.debug('No new events to process')
        return
    
    exclude_keys = remove_columns_to_historic()
    

    new_data = [
        {key: value for key, value in event.__dict__.items() if key not in exclude_keys}
        for event in data
    ]
    
    if not new_data:
        logger.info('No valid data to process')
        return
    
    new_df = pd.DataFrame(new_data)
    new_df['date'] = pd.to_datetime(new_df['date'], errors='coerce')  
    
   
    for league_id, league_group in new_df.groupby('league_id'):
        if isinstance(league_id, float):
            league_id_str = str(int(league_id))
        else:
            league_id_str = str(league_id)
        
        
        if league_id_str not in MODELS:
            logger.warning(f'League ID {league_id} não encontrado no MODELS. Ignorando...')
            continue
            
        
        target_path = MODELS[league_id_str]['historic_data']
        
        try:
            existing_data = pd.read_csv(target_path, low_memory=False)
            existing_data['date'] = pd.to_datetime(existing_data['date'], errors='coerce')
        except FileNotFoundError:
            existing_data = pd.DataFrame(columns=league_group.columns)
            logger.warning(f'Arquivo {target_path} não encontrado. Criando novo...')
        
        
        combined_df = pd.concat([existing_data, league_group])
        combined_df = combined_df.drop_duplicates(
            subset='event_id', 
            keep='first'
        ).sort_values(by='date')
        
       
        combined_df.to_csv(target_path, index=False)
        logger.info(f'League {league_id}: {len(league_group)} novos eventos salvos em {target_path}')


"""
def fill_data_gaps(gap: int = 30):
    """"""Uses API to fill gaps in the when the model was not running.""""""

    with LOCK:
        
        existing_data = load.data('historic')

        if existing_data.empty or 'date' not in existing_data.columns:
            logger.warning("DataFrame 'existing_data' is empty. skipping data gaps fill.")
            return 

        logger.info('Coverting time column to datetime')
        existing_data['date'] = pd.to_datetime(existing_data['date']) + pd.Timedelta(hours=AJUSTE_FUSO)
        existing_data['date_day'] = existing_data['date'].dt.normalize()
        
        dates_to_fetch = []
        processed_dates = set()

        for date, bloco in existing_data.groupby('date_day'):
            if date in processed_dates:
                continue
            bloco = bloco.sort_values('date')
            delta_t = bloco['date'].diff()
            
            if len(bloco[delta_t > pd.Timedelta(minutes=gap)]) > 0:
                dates_to_fetch.append(date)
            
            processed_dates.add(date)

        formatted_dates = "\n".join(date.strftime("%d-%m-%y") for date in processed_dates)
        logger.info(f"Dates to fetch:\n{formatted_dates}")

        
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
            logger.info(f'{len(new_events)} novos eventos adicionados ao histórico.')
"""

def not_ended(data: list):
    """Updates NOT_ENDED.csv with new data."""
    if not data:
        pd.DataFrame().to_csv(NOT_ENDED, index=False)
        logger.info('All not ended data fully processed')
        return
    
    ne_df = pd.DataFrame([bet.__dict__ for bet in data])
    ne_df.to_csv(NOT_ENDED, index=False)
    logger.info(
        'Not_ended events updated.'
        f' {len(ne_df)} left to update.'
        )


def error_events(data: list):
    """Updates ERROR_EVENTS.csv with new data."""

    error_df = pd.DataFrame([event.__dict__ for event in data])
    
    header = not os.path.exists(ERROR_EVENTS)
    
    error_df.to_csv(ERROR_EVENTS, mode='a', index=False, header=header)
    
    if len(error_df > 0):
        logger.info(f' Added {len(error_df)} error events to error file')


def remove_columns_to_historic():
    """Returns columns to be removed from historic data."""
    return {'event', 'hot_emoji', 'message', 'bet_type_emoji'}