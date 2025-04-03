import pandas as pd
from telegram.constants import REPORT_TOTAL, REPORT_TIME_RANGE_BODY, REPORT_TIME_RANGE_TITLE
from model.config import TIME_RANGES


def generate_total(self,
    df: pd.DataFrame,
    message: str = ''
    ) -> str:


    profit = df['profit'].sum()
    total_emoji = self.get_emoji(profit)
    vol = df['profit'].count()
    roi = profit / vol * 100 if vol > 0 else 0
    players_df = _get_players_df(df)
    notable_players = _get_notable_players(players_df)

        


def _get_notable_players(self,
    df: pd.DataFrame
    ) -> dict:
    
    notable_players = {}

    if not df.empty and 'profit' in df.columns:
        
        bp_row = df.loc[df['profit'].idxmax()]
        notable_players['best_player'] = bp_row.to_dict()
        notable_players['best_player']['emoji'] = _get_emoji(bp_row['profit'])
        
        wp_row = df.loc[df['profit'].idxmin()]
        notable_players['worst_player'] = wp_row.to_dict()
        notable_players['wors_player']['emoji'] = _get_emoji(wp_row['profit'])

        
    
    return notable_players
   