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

    i_counter = 0  # Iteration with no new events
    with LOCK:
        not_ended = load.data('not_ended')
        read_matches = set(not_ended['event_id'])

    updater_thead = threading.Thread(
        target=updater.run,
        args=(60,),
        daemon=True
    )

    while True:
        live_matches = fetch.live_events()
        unread_matches = [match 
                        for match in live_matches 
                        if match['id'] not in read_matches
        ]
        
        if not unread_matches:
            i_counter += 1
            if i_counter % i == 0:
                updater_thead.start()
                logging.info(f'{i} scans made. No new event found.')
                logging.info('Starting updater thread...')

            if i_counter % (i * 10) == 0:
                logging.info(f'{i*10} scans made. No new event found.')

        try:
            with LOCK:
                df = load.data('historic')
                for match in unread_matches:
                    predict.match(df=df,
                                event=match,
                                model=model,
                    )
                    read_matches.add(match['id'])
                i_counter = 0


        except Exception as e:
            logging.error(f'Error predicting match {match['id']}\n{e}')
        
        time.sleep(sleep_time)
