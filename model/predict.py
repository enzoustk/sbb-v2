def make_prediction(event, model):
    import logging
    import pandas as pd
    from datetime import datetime
    
    from object.bet import Bet
    from features import create
    from utils import print_separator, csv_atualizado_event
    

    from files.paths import ERROR_EVENTS
    from features.required import REQUIRED_FEATURES
    
    """
    Using the event data, make a prediction based on the model;


    Recieves 'EVENT' from scanner thread.

    1- Preprocess the event;
        1.1- Wait for the CSV to be updated;
        1.2- Check if the event has already failed;
            1.2.1- If it has, break the code and return None;
        1.3- Extract the event data from the API;
    
    2- Predict the event;
        2.1- Calculate the live features needed for the model to predict using the calculate_live_features function;
        2.2- Make the Model Prediction;
        2.3- Turn the prediction into probabilities;
        2.4- See if there is a +EV bet using the calculated_probabilities function;
            
            
    3- Process the bet;
        3.1- If no +EV bet is found, break the code and return None;
        3.2- If a +EV bet is found:
            3.2.1 - Calculate the new minimum line and odd;
            3.2.2 - Update the event data with the betting information, like minimum line, odd, time sent, etc;
            3.2.3 - Generate and send the message to the Telegram channel;
            3.2.4 - Save the bet in the ALL_DATA file;
    """    


    if not csv_atualizado_event.is_set():
        logging.info("Aguardando a atualização inicial do CSV para iniciar as previsões...")
        csv_atualizado_event.wait()

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
        features = create.features(data, live=True, players=(data['players']))

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