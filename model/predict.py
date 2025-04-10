def match(event, model):
    import logging
    import pandas as pd
    from datetime import datetime
    from object.bet import Bet
    from features import create
    from utils.utils import print_separator
    from files.paths import ERROR_EVENTS
    from features.required import REQUIRED_FEATURES
        
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

        Exceptions are logged via logging.error().
    """

    with open(ERROR_EVENTS, 'r') as file:
        error_events = set(line.strip() for line in file)
        
    if event['id'] in error_events:
        return []

    try:
       
        hora_identificacao = datetime.now().strftime('%H:%M:%S')
        print(f"Novo evento identificado às {hora_identificacao}")

        data = Bet(event)
        Bet.get_odds(market='goals')
       
        # TODO: Adicionar trava para caso features insuficientes, não executar.
        features = create.features(live=True, players=(data['players']))

        x = pd.DataFrame([features])
        x = x[REQUIRED_FEATURES]

        print_separator()
        print("Dados reais usados para previsão (X_ao_vivo):")
        print(x.to_string(index=False))
        print_separator()
        
        lambda_pred = model.predict(x)[0]
        

        Bet.find_ev(lambda_pred)

        if Bet.bet_type is not None:
            Bet.handle_made_bet()
        
        Bet.save_bet()

    except Exception as e:
        logging.error(f"Erro ao identificar o jogo: {e}")