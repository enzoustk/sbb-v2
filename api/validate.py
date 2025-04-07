"""Formats and validates the data from the API."""

import logging
from api.constants import MARKET_IDS

def odds(betting_data: dict, event_id: str, market: str='goals') -> list:

    """Recieves a dict and returns desired odds.
   
    Arguments:
        betting_data (dict): Dictionary with all odds with market_ids as
            keys and a list of dict odds as items.
            Example: "1_3": [{"id": "50385504", "over_od": "6.150","handicap": "2.5", ... }]
        event_id (str): Id for an especific match

    Returns Handicap, Over Odd and Under Odd
    TODO: Handle Different markets and variables, such as Asian Handicap or The Draw 
    """
    
    valid_odds = []
    market_data = betting_data.get(MARKET_IDS[market], None) 
    earliest_odds = min(valid_odds, key=lambda x: x.get('add_time', float('inf')))
    
    if not market_data: 
        logging.warning(f'Betting Market not found for market: {market}')
        return 
    
    if market == 'goals': 
        valid_odds = goal_odds(market_data=market_data)
        return (
            goal_handicap(earliest_odds.get('handicap')),
            earliest_odds.get('over_od'),
            earliest_odds.get('under_od')
        )

            
    if not valid_odds:
        logging.warning(f'No odds avaliable for event{event_id}')
        return [None, None, None]
                       
    
def goal_handicap(market_data) -> float | None:

    """
    Gets the handicap from the API and solves type errors,
    Also, converts it to a float and returns the current handicap if successful.
    """

    handicap = market_data['handicap']

    try: 
        if isinstance(handicap, str):
            if ',' in handicap:
                handicap_vals = [float(h.strip()) for h in handicap.split(',')]
                handicap = sum(handicap_vals) / len(handicap_vals)
            
            else:
                handicap = float(handicap.strip())
        
        return handicap
    
    except ValueError as ve:
        logging.error(f"Error converting handicap '{handicap}': {ve}")
        return None


def goal_odds(market_data) -> list[dict]:
    """Recieves a list of odds and returns the odds with handicap, over and under odds."""
    
    for odd in market_data: 
            if isinstance(odd, dict):
                if all (odd.get(k) != '-' for k in ('handicap', 'over_od', 'under_od')):
                    market_data.append(odd)

