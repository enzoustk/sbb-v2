import logging
import threading
import time
from data import load
from api import fetch
from model import predict
from processes import updater
from files.paths import LOCK

logger = logging.getLogger(__name__)

def run(models: dict, i: int = 50, sleep_time: int = 1):
    """Scans all live events and handles them
    
    Arguments:
        model: ML Model used to predict match odds
        i (int): After i runs, it shows a message to assert it is 
        running properly
    """
    logger.info('Scanner Started.')
    i_counter = 0  # Iteration with no new events
    
    with LOCK:
        not_ended = load.data('not_ended')
        
        try:
            read_matches = set(not_ended['event_id'])
        except KeyError:
            logger.error('not_ended data not found.')
            read_matches = set()
        
    while True:        
        live_matches = fetch.live_events()

        unread_matches = [
            match for match in live_matches 
            if int(match['id']) not in read_matches
        ]
        
        if not unread_matches:
            i_counter += 1
            if i_counter % i == 0:
                logger.info(f'{i} scans made. Starting Updater')
                threading.Thread(
                    target=updater.run,
                    daemon=True
                ).start()

        
        if unread_matches:
            try:
                with LOCK:
                    dfs = load.data('historic')
                    for match in unread_matches:
                        predict.match(dfs=dfs,
                                    event=match,
                                    models=models,
                        )
                        read_matches.add(int(match['id']))
                    i_counter = 0

            except Exception as e:
                logger.error(f"Error predicting match {match['id']}\n{e}")
        
        time.sleep(sleep_time)
