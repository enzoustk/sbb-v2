import logging
import threading
import time
from data import load
from api import fetch
from model import predict
from processes import updater
from files.paths import LOCK, NOT_ENDED


def run(model, i: int = 50, sleep_time: int = 1):
    """Scans all live events and handles them
    
    Arguments:
        model: ML Model used to predict match odds
        i (int): After i runs, it shows a message to assert it is 
        running properly
    """
    logging.info('Scanner Started.')
    i_counter = 0  # Iteration with no new events
    
    with LOCK:
        not_ended = load.data('not_ended')
        
        try:
            read_matches = set(not_ended['event_id'])
        except KeyError:
            logging.error('not_ended data not found.')
            read_matches = set()
        
    while True:
        print('i_counter = ', i_counter)
        
        live_matches = fetch.live_events()

        unread_matches = [
            match for match in live_matches 
            if int(match['id']) not in read_matches
        ]
        
        if not unread_matches:
            i_counter += 1
            if i_counter % i == 0:
                logging.info(f'{i} scans made. No new event found.')
                logging.info('Starting updater thread...')
                threading.Thread(
                    target=updater.run,
                    daemon=True
                ).start()

            if i_counter % (i * 10) == 0:
                logging.info(f'{i*10} scans made. No new event found.')
        
        if unread_matches:
            try:
                with LOCK:
                    df = load.data('historic')
                    for match in unread_matches:
                        predict.match(df=df,
                                    event=match,
                                    model=model,
                        )
                        read_matches.add(int(match['id']))
                    i_counter = 0


            except Exception as e:
                logging.error(f'Error predicting match {match['id']}\n{e}')
        
        time.sleep(sleep_time)
