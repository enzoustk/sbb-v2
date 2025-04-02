import json
import logging
import pandas as pd

from object.bet import Bet
from collections import defaultdict

from data import load
from api import fetch

from model.config import AJUSTE_FUSO
from files.paths import ALL_DATA, HISTORIC_DATA, NOT_ENDED


def update_csv(data: list):
    """
    Atualiza o arquivo HISTORIC_DATA.csv com novos dados, ordenando por data e evitando duplicatas.
    """

    try: 
        existing_data = pd.read_csv(HISTORIC_DATA)
    except FileNotFoundError: 
        existing_data = pd.DataFrame()

    
    exclude_keys = remove_columns_to_csv()
    new_data = [
        {key: value for key, value in bet.__dict__.items() if key not in exclude_keys}  
        for bet in data
        ]

    new_df = pd.DataFrame(new_data)

    if existing_data.empty:
        new_df.to_csv(HISTORIC_DATA, index=False)
        logging.info('File Historic Data updated sucessfully')
        return

    new_df = pd.concat([existing_data, new_df], ignore_index=True)
    new_df['time_sent'] = pd.to_datetime(new_df['time_sent'], format='%d/%m/%Y', errors='coerce')
    new_df = new_df.sort_values(by='date', ascending=False)
    new_df = new_df.drop_duplicates()

    new_df.to_csv(HISTORIC_DATA, index=False)

def fill_data_gaps(gap: int = 30):
    
    """
    Finds all data gaps in the all_files file.
    Pulls all-day API data for days containing gaps
    Runs only at start of application 
    Checks if it is not in the ALL_DATA.json and neither in HISTORIC_DATA.csv
    If it is not, appends to HISTORIC_DATA.csv
    TODO: Remover o dia de hoje de processed_dates
    """

    json_data = load.data('json')
    json_data['time_sent'] = pd.to_datetime(json_data['time_sent']) + pd.Timedelta(hours=AJUSTE_FUSO)
    json_data['date'] = json_data['time_sent'].dt.normalize()
    
    dates_to_fetch = []
    processed_dates = set()

    for date, bloco in json_data.groupby('date'):
            
            if date in processed_dates: continue
            bloco = bloco.sort_values('time_sent')
            delta_t = bloco['time_sent'].diff()
        
            if len(bloco[delta_t > pd.Timedelta(minutes=gap)]) > 0:
                dates_to_fetch.append(date)
            
            processed_dates.add(date)

    matches_fetched = fetch.events_for_date(dates=dates_to_fetch)
    
    existing_data = defaultdict(set)
    
    for dataset in [ALL_DATA, HISTORIC_DATA]:   
        for item in dataset:
            date = item['time_sent'].date()
            existing_data[date].add(item['event_id'])

    for datapoint in matches_fetched:

        date = datapoint['time_sent'].date()
        event_id = datapoint['event_id']
                    
        if event_id in existing_data.get(date, set()): 
            continue

        # Processa o novo evento
        match = Bet()
        match.__dict__.update(datapoint)
        match.to_historic_file()

        existing_data[date].add(event_id)

def not_ended(data: list):
    
    """
    Rewrites NOT_ENDED json with events that are still unended after iteration
    """
    
    with open(NOT_ENDED, 'w') as ne_file:
        ne_data = [bet.__dict__ for bet in data]
        json.dump(ne_data, ne_file, indent=4)
        logging.info('Not ended events updated sucessfully')

def error_events(data: list):
    """
    Appens buggy events to ERROR Events
    """
    with open(NOT_ENDED, 'a') as error_file:
        error_data = [event.__dict__ for event in data]
        json.dump(error_data, error_file, indent=4)
        logging.info('Not ended events updated sucessfully')

def remove_columns_to_csv():
    return {'event', 'hot_emoji', 'message', 'bet_type_emoji'}