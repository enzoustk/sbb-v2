import logging
import pandas as pd
from collections import defaultdict
from files.paths import HISTORIC_DATA, ALL_DATA, NOT_ENDED

def data(file: str, load_ids: bool = False) -> pd.DataFrame | tuple[pd.DataFrame, defaultdict]:
    """_summary_

    Args:
        file (str): _description_
        load_ids (bool, optional): _description_. Defaults to False.

    Returns:
        pd.DataFrame | tuple[pd.DataFrame, defaultdict]: _description_
    """
    
    ids = defaultdict(set)
    data = pd.DataFrame()

    try: 
        if file == 'csv': data = pd.read_csv(HISTORIC_DATA)
        elif file == 'json': data = pd.read_json(ALL_DATA)
        elif file == 'not_ended': data = pd.read_json(NOT_ENDED)

        if load_ids: 
            try:
                for datapoint in data.to_dict('records'):
                    date = datapoint['time_sent'].date()
                    ids[date].add(datapoint['event_id'])
            
            except KeyError as e: 
                logging.warning(f'Missing data {e}')
    
    except FileNotFoundError: 
        logging.warning(f'File {file} not found')
        
    if load_ids: return data, ids
    else: return data
