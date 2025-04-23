import argparse
from api import fetch
from data import load 
from object.bet import Bet

def cancel_bet(event_id: str, score: str | None = None):
    
    if score is not None:
        home_score, away_score = map(int, score.split('-'))
        total_score = home_score + away_score

    historic_df = load.data('historic')
    historic_filtered = historic_df[historic_df['event_id'] == event_id]
    
    bet = Bet(fetch.event_for_id([historic_filtered['event_id']]))
    bet.update_from_dict(historic_filtered.to_dict('records'))
    
    
    if not total_score: #Ou seja, anularemos a tip
        bet.cancel()

    elif total_score: #Ou seja, mudaremos o placar da tip
        bet.change_score(home_score, away_score)
