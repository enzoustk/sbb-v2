def print_separator():
    print('\n' + '-' * 60)

def events_to_update():
    from api_requests.pull_data import fetch_live_events
    from constants.file_params import MADE_BETS
    live_events = fetch_live_events()

    live_events_ids = {str(event['id']) for event in live_events}
    MADE_BETS['event_id'] = MADE_BETS['event_id'].astype(str)

    new_events = MADE_BETS['final_score'].isna()
    new_events = new_events.drop_duplicates(subset=['event_id'])
    new_events = new_events[~new_events['event_id'].isin(live_events_ids)]
    
    return new_events
