""" Fetch all kinds of data from the API """
"""TODO: Improve error handling."""


import requests
import logging
from api.constants import API_TOKEN, SPORT_ID, URLS, LEAGUE_IDS

logger = logging.getLogger(__name__)

def live_events(league_ids: dict = LEAGUE_IDS) -> list[dict]:

    """Fetch real-time ongoing sports events for specific leagues

    Args:
    league_ids (dict, optional): Mapping of league identifiers. 
        Format example: {"soccer": 1, "basketball": 2}. 
        Defaults to LEAGUE_IDS.
    
    Raises:
        RequestException: if any error pulling data

    Returns:
        list of dict: live_events where each dict contains:
        TODO: Fill what each dict contains.
    """

    params = {'token': API_TOKEN, 'sport_id': SPORT_ID}

    try:
        response = requests.get(URLS['inplay'], params=params)
        response.raise_for_status()
        data = response.json()

        live_events = [event for event in data['results'] if event['league']['id'] in league_ids.keys()]
        return live_events


    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching live events: {e}")
        return []


def odds(event_id: str) -> list[dict]:
    
    """Fetch all odds for a specific event

    Args:
        event_id (str): Id for an especific match
        Format example: '982131'

    Raises: 
        RequestException: if any error pulling event odds

    Returns:
        list of dict with all event odds.
        

    TODO: Add parameter to choose market to be collected.
    TODO: Check if the odd is live or pre-live.
    """

    params = {'token': API_TOKEN, 'event_id': event_id}
    
    try:
        response = requests.get(URLS['odds'], params=params)
        response.raise_for_status()
        all_data = response.json()
        
        return all_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching odds: {e}")
        return []


def events_for_date(dates: list, league_ids: dict = LEAGUE_IDS) -> list[dict]:
    
    """Fetch all ended events for a specific list of dates

    Args:
        dates (list): List of dates to fetch events from.
        league_ids (dict, optional): Mapping of league identifiers. 
        Format example: {"soccer": 1, "basketball": 2}. 
        Defaults to LEAGUE_IDS.

    Returns:
        events: list of dicts containing all events.
    
    TODO: add parameter to choose league.
    """
    logger.info('Starting to fetch data')

    league_ids = (LEAGUE_IDS.keys())

    all_events = []

    params = {
        "token": API_TOKEN,
        "sport_id": SPORT_ID,
        "league_id": league_ids,  
        "page": 1
    }
    
    for date in dates:

        params['page'] = 1
        params['day'] = date.strftime('%Y%m%d')
        logger.info(f"Fetching events for {date.strftime('%d-%m-%y')}")

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
                logger.error(f"Request failed: {response.status_code} for date {date.strftime('%d-%m-%y')}")
                break
        
        logger.info(f"Fetched {len(events)} events for date {date.strftime('%Y-%m-%d')}")
        
        all_events.extend(events)

    return all_events


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
        logger.error(f"Error fetching event data: {e}")
        return {}