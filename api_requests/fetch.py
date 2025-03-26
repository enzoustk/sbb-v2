import requests, logging
from constants.api import API_TOKEN, SPORT_ID, LEAGUE_ID, URLS

"""
Fetch all kinds of data from the API
TODO: Improve error handling.
"""

def live_events() -> list[dict]:

    """
    Fetch live events from the API
    returns a list of live events
    """

    live_events = []
    params = {'token': API_TOKEN, 'sport_id': SPORT_ID}

    try:
        response = requests.get(URLS['inplay'], params=params)
        response.raise_for_status()
        data = response.json()

        if 'results' in data:
            for event in data['results']:
                if event['league']['id'] == LEAGUE_ID:
                    live_events.append(event)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching live events: {e}")
        return []
    
    return live_events

def odds(event_id: str) -> list[dict]:
    
    """
    Fetch odds for any event
    TODO: add parameter to choose market to be collected.
    TODO: Check if the odd is live or pre-live.
    """

    params = {'token': API_TOKEN, 'event_id': event_id}
    
    try:
        response = requests.get(URLS['odds'], params=params)
        response.raise_for_status()
        all_data = response.json()
        
        if all_data and all_data.get('sucess', {}) == 1:
            betting_data = all_data.get('results', {}).get('odds',{})
            return betting_data

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching odds: {e}")
        return []

def events_for_date(dates: list) -> list[dict]:
    
    """
    Fetch all ended events for a specific list of dates
    TODO: add parameter to choose league.
    """

    for date in dates:
        formatted_date = date.strftime('%Y%m%d')
        params = {
            "token": API_TOKEN,
            "sport_id": SPORT_ID,
            "league_id": LEAGUE_ID,
            "day": formatted_date,
            "page": 1
        }

        events = []

        while True:
            response = requests.get(URLS['ended_events'], params=params)
            if response.status_code == 200:
                data = response.json()
                events.extend(data['results'])
                if params['page'] * data['pager']['per_page'] < data['pager']['total']:
                    params['page'] += 1
                else:
                    break
            else:
                logging.error(f"Request failed: {response.status_code} for date {formatted_date}")
                break
    
    return events

def event_for_id(event_id: str) -> dict:

    """
    Fetch event data for a specific event ID
    returns a dictionary with the event data
    """

    params = {'token': API_TOKEN, 'event_id': event_id}

    try:
        response = requests.get(URLS['event'], params=params)
        response.raise_for_status()
        event_data = response.json().get('results', [{}])[0]
        return event_data
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching event data: {e}")
        return {}