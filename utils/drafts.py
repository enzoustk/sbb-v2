from telegram.constants import REPORT_TITLE
import pandas as pd

def generate_title(self, df: pd.DataFrame):
    title = {}
    title['interval'] = self.interval
    title['league'] = _get_league(df)
    title['ev_type'] = _get_ev_type
    title['period_type'] = _get_period_type

    message += REPORT_TITLE.format(title)

def _get_league(self, df: pd.DataFrame):
    """
    Se só tem uma liga, retorna essa liga.
    Se tem mais de uma, retorna um str: 'Liga 1,
    Liga 2, Liga 3, ...
    """
    
    leagues = df['league'].drop_duplicates().tolist
    
    if len(leagues) == 1:
        return str(leagues)
    
    else:
        
    


