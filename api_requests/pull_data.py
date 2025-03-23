def fetch_live_events():
    
    import requests
    import logging
    from constants.api_params import API_TOKEN, SPORT_ID, LEAGUE_ID, INPLAY_URL
    
    """
    Procura na API jogos ao Vivo e retorna uma lista de eventos ao vivo
    :param token: Token de acesso a API
    :param sport_id: ID do esporte a ser filtrado
    """

    live_events = []
    params = {'token': API_TOKEN, 'sport_id': SPORT_ID}

    try:
        response = requests.get(INPLAY_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if 'results' in data:
            for event in data['results']:
                if event['league']['id'] == LEAGUE_ID:  # Filtra pela liga especificada
                    live_events.append(event)

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar eventos ao vivo: {e}")
    
    return live_events

def fetch_odds(event_id):
   
    import requests, logging
    from constants.api_params import API_TOKEN, ODDS_URL
    
    """
    Busca as Odds para qualquer evento
    TODO: adicionar parâmetro para escolher mercado a ser coletado.
    """

    params = {'token': API_TOKEN, 'event_id': event_id}
    
    try:
        response = requests.get(ODDS_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar dados de odds: {e}")
        return None

def fetch_events_for_date(date):

    import requests, logging
    from constants.api_params import API_TOKEN, SPORT_ID, LEAGUE_ID, ENDED_EVENTS_URL
    
    """
    Busca eventos encerrados para uma data específica
    """

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
        response = requests.get(ENDED_EVENTS_URL, params=params)
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