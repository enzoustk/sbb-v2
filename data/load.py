import logging
import pandas as pd
from collections import defaultdict
from files.paths import HISTORIC_DATA, ALL_DATA, NOT_ENDED 

def data(file: str, load_ids: bool = False) -> pd.DataFrame | tuple[pd.DataFrame, defaultdict]:
    """Loads data from a CSV file and optionally returns IDs grouped by date.

    Args:
        file (str): Nome do arquivo a ser carregado ('historic', 'all_data', 'not_ended').
        load_ids (bool, optional): Se True, retorna um dicionário de IDs agrupados por data. Defaults to False.

    Returns:
        pd.DataFrame | tuple[pd.DataFrame, defaultdict]: DataFrame com os dados e (opcionalmente) IDs por data.
    """

    ids = defaultdict(set)
    data = pd.DataFrame()

    try:
        if file == 'historic':
            data = pd.read_csv(HISTORIC_DATA)
        elif file == 'all_data':
            data = pd.read_csv(ALL_DATA)
        elif file == 'not_ended':
            data = pd.read_csv(NOT_ENDED)  


        if load_ids:
            try:
                for datapoint in data.to_dict('records'):
                    date = datapoint['time_sent'].date()
                    ids[date].add(datapoint['event_id'])
            except KeyError as e:
                logging.warning(f'Missing Column: {e}')
    
    except FileNotFoundError:
        logging.warning(f'File {file} not found '
                        f'Creating it...')

    return (data, ids) if load_ids else data