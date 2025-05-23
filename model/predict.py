import logging
import pandas as pd
from tabulate import tabulate
from datetime import datetime
from object.bet import Bet
from features import create, check
from utils.utils import print_separator, print_features
from files.paths import ERROR_EVENTS
from features.required import REQUIRED_FEATURES

logger = logging.getLogger(__name__)
bet_logger = logging.getLogger('bet')

def match(dfs: dict, event: dict, models: dict):
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

    try:
    
        hora_identificacao = datetime.now().strftime('%H:%M:%S')
        
        print_separator()
        bet_logger.bet(f"Novo evento identificado às {hora_identificacao}")

        bet = Bet(event)
        bet.get_odds(market='goals')

        # TODO: Adicionar trava para caso features insuficientes, não executar.
        
        
        features = create.features(
            data=dfs[bet.league_id],
            live=True,
            players=bet.players
        )
        
        try:
            X = features[REQUIRED_FEATURES]
            
            if features[REQUIRED_FEATURES].empty:
                logger.warning(f'Empty daframe for {bet.home_str} vs {bet.away_str}')
                check.dataframe(bet.home_player, bet.away_player, df=dfs[bet.league_id])
                return

            print_separator(30)
            bet_logger.bet("Dados reais usados para previsão (X_ao_vivo):")
            bet_logger.bet(f'{print_features(X)}')
            print_separator(30)
            
            lambda_pred = models[bet.league_id].predict(X)
            
            bet.find_ev(lambda_pred)
            if bet.bet_type is not None:
                bet.handle_made_bet()
        
            bet.save_bet()

        
        except KeyError:
            logger.error(f'Error predicting for {bet.home_str} vs {bet.away_str}. Model {models[bet.league_id]} not Found')     
                
    except Exception as e:
        bet_logger.bet(f"Erro ao prever para o jogo {bet.event_id} {bet.home_str} vs {bet.away_str}: {e}")
        logger.error(f"Erro ao prever para o jogo {bet.event_id}: {e}")
