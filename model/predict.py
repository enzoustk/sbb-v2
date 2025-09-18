import logging
import pandas as pd
import numpy as np
from tabulate import tabulate
from datetime import datetime
from object.bet import Bet
from utils.utils import print_separator, print_features
from files.paths import ERROR_EVENTS
from features.start import get_features

logger = logging.getLogger(__name__)
bet_logger = logging.getLogger('bet')

def match(
    dfs: dict,
    history: dict,
    event: dict,
    models: dict,
    scalers: dict,
    predictor: str):
    """Processes live betting events using a predictive model.

    Performs error checking, feature engineering, model prediction, and bet handling
    for live sports betting opportunities.

    Args:
        event (dict): Event data received from the scanning thread.
            Expected to contain an 'id' field and player/market data.

    Returns:
        list: Empty list if event is invalid or has errors. Returns None implicitly
            in other failure cases (via exception handling).

    Steps:
        1. **Error Checking**:
            - Checks if event ID exists in ERROR_EVENTS file
            - Returns empty list for known bad events

        2. **Data Preparation**:
            - Extracts betting odds for 'goals' market via `Bet.get_odds()`
            - Creates live features using `create.features()` with player data
            - Filters features to model's REQUIRED_FEATURES

        3. **Model Prediction**:
            - Makes prediction using pre-trained model
            - Calculates +EV opportunities via `Bet.find_ev()`

        4. **Bet Handling**:
            - If +EV bet found:
                * Updates bet details with `Bet.handle_made_bet()`
                * Persists bet to NOT_ENDED file via `Bet.save_bet()`
            - Logs errors during processing

        Exceptions are logged via logger.error().
    """
    try:
        with open(ERROR_EVENTS, 'r', encoding='latin-1') as file:
            error_events = set(line.strip() for line in file)
    except FileNotFoundError:
        logger.info('Error Events file not found. Skipping it')
        error_events = set()
        
    if event['id'] in error_events:
        return []


    
    hora_identificacao = datetime.now().strftime('%H:%M:%S')
    
    print_separator()
    bet_logger.bet(f"Novo evento identificado às {hora_identificacao}")



    # TODO: Adicionar trava para caso features insuficientes, não executar.
        
    if predictor == 'ml_goals':
        predict_ml_model(
            dfs=dfs,
            history=history,
            models=models,
            scalers=scalers,
            event=event)
        
    if predictor == 'elo':
        predict_elo_model()

def predict_ml_model(
        history: dict,
        dfs: dict,
        scalers: dict,
        models: dict,
        event: dict
        ):

        bet = Bet(event)
        bet.get_odds(market='total')

        features = get_features(
            event=bet,
            history=history,
            drop_h2h=10
        )

        if features.isnull().values.any() or features.empty:
            bet_logger.bet(f'Pulando pois o evento {bet.home_player} vs {bet.away_player} possui features nan')   # mantém o anterior
            return
    
        
        try:
            X = features
            
            if (isinstance(features, (pd.DataFrame, pd.Series)) and features.empty) or \
            (isinstance(features, np.ndarray) and features.size == 0):
                logger.warning(f'Empty dataframe/array for {bet.home_str} vs {bet.away_str}')
                return

            print_separator(30)
            bet_logger.bet("Dados reais usados para previsão (X_ao_vivo):")
            bet_logger.bet(f'{bet.home_player} vs {bet.away_player}')
            bet_logger.bet(f'Features Normais:')
            bet_logger.bet(f'{print_features(X)}')
            bet_logger.bet(f'Features Escaladas:')
            bet_logger.bet(print(scalers[bet.league_id].transform(features)))
            print_separator(30)
            
            lambda_pred = models[bet.league_id].predict(scalers[bet.league_id].transform(features))
            
            bet.find_ev(lambda_pred)
            if bet.bet_type is not None:
                bet.handle_made_bet()
            bet.save_bet()
        
        except KeyError as e:
            logger.error(f'Error predicting for {bet.home_str} vs {bet.away_str}. Model {bet.league_id} not Found\n Error: {e}')     
                
def predict_elo_model():
    pass