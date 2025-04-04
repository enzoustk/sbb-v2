import pandas as pd
from telegram.constants import REPORT_TOTAL, REPORT_TIME_RANGE_BODY, REPORT_TIME_RANGE_TITLE
from model.config import TIME_RANGES


def generate_total(self,
    df: pd.DataFrame,
    message: str = ''
    ) -> str:

    sub_dfs = {'total': df}
    for bet_type in df['bet_type'].dropna().unique():
        sub_dfs[bet_type] = df[df['bet_type'] == bet_type]


    for data in sub_dfs:
        bet_type = data['bet_type'].unique()
        profit = data['profit'].sum()
        total_emoji = self.get_emoji(profit)
        vol = data['profit'].count()
        if not vol: vol = 0
        roi = profit / vol * 100 if vol > 0 else 0
        players_df = _get_players_df(data)
        notable_players = _get_notable_players(players_df)
        
        message += REPORT_TOTAL.format(
            bet_type=bet_type,
            profit=profit,
            total_emoji=total_emoji,
            vol=vol,
            roi=roi,
            best_player=notable_players['best_player']['player'],
            bp_emoji=notable_players['best_player']['emoji'],
            bp_profit=notable_players['best_player']['profit'],
            worst_player=notable_players['worst_player']['player'],
            wp_emoji=notable_players['worst_player']['emoji'],
            wp_profit=notable_players['worst_player']['profit'],
        )


        


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
        notable_players['worst_player']['emoji'] = _get_emoji(wp_row['profit'])

        
    
    return notable_players
   