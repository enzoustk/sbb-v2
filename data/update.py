def update_dataframe():
    
    import pandas as pd
    from data import load
    from files.paths import HISTORIC_DATA
    
    '''
    APPROACH 1: Use ALL_DATA file to update the HISTORIC_DATA.csv file.
    TODO: Add a API pull function, to add events that are not stored.
    '''

    """
    Carrega os dados do json
    Inicia Variável bet com os dados do json
    """

    json_data = load.json() 
    csv_data = load.csv()


    new_matches = []
    
    for match in json_data.to_dict('records'): 
        if csv_data.empty or not any(csv_data['event_id'] == match['event_id']):
            new_matches.append(match)

    
    if new_matches:
        new_data = pd.DataFrame(new_matches)
        
        if not csv_data.empty:
            csv_data = pd.concat([csv_data, new_data], ignore_index=True)
        else:
            csv_data = new_data
        
        if 'time_sent' in csv_data.columns:
            csv_data = csv_data.sort_values(by='date')
        
        # Salva o resultado no CSV
        csv_data.to_csv(HISTORIC_DATA, index=False)
        print(f"Total de matches adicionados: {len(new_matches)}")
    
    return csv_data
        
def update_from_api(gap: int = 30):
    from api_requests import fetch
    from data import load
    import pandas as pd
    from model.config import AJUSTE_FUSO
    from files.paths import ALL_DATA, HISTORIC_DATA
    from collections import defaultdict
    from object.bet import Bet

    '''
    Finds all data gaps in the all_files file.
    Pulls all-day API data for days containing gaps 
    Checks if it is not in the ALL_DATA.json and neither in HISTORIC_DATA.csv
    If it is not, appends to HISTORIC_DATA.csv
    TODO: Remover o dia de hoje de processed_dates
    '''

    json_data = pd.DataFrame(load.json)
    
    json_data['time_sent'] = pd.to_datetime(json_data['time_sent']) + pd.Timedelta(hours=AJUSTE_FUSO)
    json_data['date'] = json_data['time_sent'].dt.normalize()
    
    dates_to_fetch = []
    processed_dates = set()

    for date, bloco in json_data.groupby('date'):
            
            if date in processed_dates: continue
            bloco = bloco.sort_values('time_sent')
            delta_t = bloco['time_sent'].diff()
        
            if len(bloco[delta_t > pd.Timedelta(minutes=gap)]) > 0:
                dates_to_fetch.append(date)
            
            processed_dates.add(date)

    matches_fetched = fetch.events_for_date(dates=dates_to_fetch)
    
    '''
    existing_ids = set()
    for item in ALL_DATA: existing_ids.add(item['event_id'])
    for item in HISTORIC_DATA: existing_ids.add(['event_id'])
    '''

    existing_data = defaultdict(set)
    
    for dataset in [ALL_DATA, HISTORIC_DATA]:   
        for item in dataset:
            date = item['time_sent'].date()
            existing_data[date].add(item['event_id'])

    for datapoint in matches_fetched:

        date = datapoint['time_sent'].date()
        event_id = datapoint['event_id']
                       
        if event_id in existing_data.get(date, set()): 
            continue

        # Processa o novo evento
        match = Bet()
        match.__dict__.update(datapoint)
        match.to_historic_file()

        existing_data[date].add(event_id)