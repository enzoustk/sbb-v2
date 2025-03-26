def odds(data: dict, event_id: str, market: str='goals') -> list:

    import logging
    from constants.api import ASIAN_GOALS

    """
    Recieves all odds as a dict,
    Selects desired odds based on valid_odds criteria
    Returns Handicap, Over Odd and Under Odd
    TODO: Handle Different markets and variables, such as Asian Handicap or The Draw 
    """

    if market == 'goals':
        desired_odds = data[ASIAN_GOALS] # ASIAN_GOALS = '1_3'
        valid_odds = []
        
        for odd in desired_odds: 
            if isinstance(odd, dict):
                if all (odd.get(k) != '-' for k in ('handicap', 'over_od', 'under_od')):
                    valid_odds.append(odd)
            
        if not valid_odds:
            logging.warning(f'No odds avaliable for event{event_id}')
            return None, None, None
            
            
        earliest_odds = min(valid_odds, key=lambda x: x.get('add_time', float('inf')))

        return (
            goal_handicap(earliest_odds.get('handicap')),
            earliest_odds.get('over_od'),
            earliest_odds.get('under_od')
        )
    
def goal_handicap(self) -> float | None:
        
    import logging

    """
    Gets the handicap from the API and solves type errors,
    Also, converts it to a float and returns the current handicap if successful.
    """
    handicap = self.event['handicap']

    try:
        if isinstance(handicap, float): return handicap
        
        if isinstance(handicap, str):
            if ',' in handicap:
                handicap_vals = [float(h.strip()) for h in handicap.split(',')]
                current_handicap = sum(handicap_vals) / len(handicap_vals)
            else:
                current_handicap = float(handicap.strip())
            return current_handicap
        
        else:
            logging.error(f"Invalid Handicap or Handicap type: {type(handicap)} - Value: {handicap}")
            return None
    
    except ValueError as ve:
        logging.error(f"Error converting handicap '{handicap}': {ve}")
        return None
