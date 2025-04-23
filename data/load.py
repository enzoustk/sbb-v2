import logging
import pandas as pd
from files.paths import MODELS, NOT_ENDED 

logger = logging.getLogger(__name__)

"""
def data(
        file: str,
        load_ids: bool = False
        ) -> pd.DataFrame | tuple[pd.DataFrame, defaultdict]:
    """"""Loads data from a CSV file and optionally returns IDs grouped by date.

    Args:
        file (str): Nome do arquivo a ser carregado ('historic', 'all_data', 'not_ended').
        load_ids (bool, optional): Se True, retorna um dicionário de IDs agrupados por data. Defaults to False.

    Returns:
        pd.DataFrame | tuple[pd.DataFrame, defaultdict]: DataFrame com os dados e (opcionalmente) IDs por data.
    """"""

    ids = defaultdict(set)
    data = pd.DataFrame()

    try:
        if file == 'historic':
            data = pd.read_csv(HISTORIC_DATA, low_memory=False)
            if not data.empty:
                # Converter colunas apenas se existirem
                if 'date' in data.columns:
                    data['date'] = pd.to_datetime(data['date'])
                if 'time_sent' in data.columns:
                    data['time_sent'] = pd.to_datetime(data['time_sent'])
        
        elif file == 'not_ended':
            try:
                data = pd.read_csv(NOT_ENDED)  
            except pd.errors.EmptyDataError:
                data = pd.DataFrame()

        if load_ids:
            try:
                for datapoint in data.to_dict('records'):
                    date = datapoint['time_sent'].date()
                    ids[date].add(datapoint['event_id'])
            except KeyError as e:
                logger.warning(f'Missing Column: {e}')
    
    except FileNotFoundError:
        logger.warning(f'File {file} not found '
                        f'Creating it...')

    return (data, ids) if load_ids else data
"""

def data(file: str,) -> dict[str, pd.DataFrame]:
    
    if file == 'historic':
        try:
            data = {
                key: pd.read_csv(value['historic_data'], low_memory=False)
                for key, value in MODELS.items()     
            }

            for model_name, df in data.items():  # ✅
                # Verificar colunas no DataFrame atual (df)
                if 'date' in df.columns:  # ✅
                    df['date'] = pd.to_datetime(df['date'])  # ✅
                if 'time_sent' in df.columns:  # ✅
                    df['time_sent'] = pd.to_datetime(df['time_sent'])  # ✅
                data[model_name] = df

        except Exception as e:
            logger.error(f'Error Loading Historic data {e}')
    
    elif file == 'not_ended':
        try:
            data = pd.read_csv(NOT_ENDED)  
        except pd.errors.EmptyDataError:
            data = pd.DataFrame()
    
    return data