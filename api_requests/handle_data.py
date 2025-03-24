def handle_handicap(handicap: float | str) -> float | None:
    
    import logging
    
    """
    Gets the handicap from the API and solves type errors,
    Also, converts it to a float and returns the current handicap if successful.
    """
    
    try:
        if isinstance(handicap, float):
            return handicap
        
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

def event_to_dict(event) -> dict:
    
    """
    Recieves the event data from the API for one single event.
    Extracts the data and returns a dictionary with the event data.
    """

    return {
        
            'home_str': event.get('home', {}).get('name'),
            'away_str': event.get('away', {}).get('name'),

            'home_player': get_name(side='home', event=event, type='player'),
            'home_team': get_name(side='home', event=event, type='team'),
            
            'away_player': get_name(side='away', event=event, type='player'),
            'away_team': get_name(side='away', event=event, type='team'),
            
            'over_odd': float(event['over_od']),
            'under_odd': float(event['under_od']),

            'handicap': handle_handicap(event.get('handicap', '0')),
            'league': event.get('league', {}).get('name', 'Unknown League'),
            'event_id': event['id'],
            }

def print_event(data: dict) -> None:
    """
    Print the event data;
    """
    print(f"League: {data['league']}")
    print(f"{data['home_player']} ({data['home_team']}) vs {data['away_player']} ({data['away_team']})")
    print('-' * 20)
    print(f"Line: {data['handicap']}")

def get_name(side: str | None = None, event: dict | None = None, type: str | None = None) -> str | None:
    
    if side is None:
        import logging
        logging.error("Error: side is None")
        return None
    
    if event is None:
        import logging
        logging.error("Error: event is None")
        return None
    
    if type is None:
        import logging
        logging.error("Error: you must provide a name")
        return None
    
    """
    Gets team_str: 'Barcelona (Player_Name) Esports'
    if type=team, Returns: 'Barcelona'
    if type=player, Returns: 'Player_Name'
    """

    team_str = event.get(side, {}).get('name')
    
    if type == 'team':
        try:
            team_name = team_str.split('(')[0].strip().lower()
            return team_name
        
        except Exception as e:
            logging.error(f"Error: {e}")
            return None
    
    if type == 'player':
        try:
            start = team_str.find('(') + 1
            end = team_str.find(')')
            return team_str[start:end].lower()
        
        except Exception as e:
            logging.error(f"Error: {e}")
            return None
        
        