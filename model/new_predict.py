from utils import csv_atualizado_event
import logging
from constants.file_params import ERROR_EVENTS

def find_player_name(team_name):
    
    try:
        start = team_name.find('(') + 1
        end = team_name.find(')')
        return team_name[start:end].lower()
    
    except Exception as e:
        logging.error(f"Erro ao extrair nome do jogador e time: {e}")
        return team_name

def handle_handicap(handicap):
    try:
        if isinstance(handicap, float):
            return handicap
        
        if isinstance(handicap, str):
            if ',' in handicap:
                handicap_vals = [float(h.strip()) for h in handicap.split(',')]
                handicap_atual = sum(handicap_vals) / len(handicap_vals)
            else:
                handicap_atual = float(handicap.strip())
            return handicap_atual
        else:
            logging.error(f"Tipo inválido para handicap: {type(handicap)} - Valor: {handicap}")
            return None
    except ValueError as ve:
        logging.error(f"Erro ao converter handicap '{handicap}': {ve}")
        return None

def extract_data(event):

    home_team= event.get('home', {}).get('name')
    away_team = event.get('away', {}).get('name')
    
    over_odds = float(event['over_od'])
    under_odds = float(event['under_od'])
    
    handicap = handle_handicap(event.get('handicap', '0'))
    home_player = find_player_name(home_team)
    away_player = find_player_name(away_team)

    home_team_str = home_team.split('(')[0].strip().lower()
    away_team_str = away_team.split('(')[0].strip().lower()

    #Extração da liga
    league = event.get('league', {}).get('name', 'Liga Desconhecida')

    """
    Retorna os dados do evento
    """
    return {'home_player':  home_player,
            'home_team':    home_team_str,
            'away_player':  away_player,
            'away_team':    away_team_str,
            'over_odds':    over_odds,
            'under_odds':   under_odds,
            'handicap':     handicap,
            'league':       league}

def print_event_data(data):
    """
    Imprimir dados do evento;
    """
    print(f"Liga: {data['league']}")
    print(f"{data['home_player']} ({data['home_team']}) vs {data['away_player']} ({data['away_team']})")
    print('-' * 20)
    print(f"Linha: {data['handicap']}")
    
def calculate_probabilities(data, lambda_pred):
    from model.model_config import EV_THRESHOLD
    from model.predict import calculate_poisson

    """
    Calcular probabilidades e EV;
    Retornar probabilidades e EV caso seja maior que o threshold;
    Retornar None caso não seja maior que o threshold;
    Imprimir dados do evento;
    """

    prob_over, prob_under = calculate_poisson(lambda_pred, data['handicap'])
    ev_over = data['over_odds'] * prob_over - 1
    ev_under = data['under_odds'] * prob_under - 1
    
    print(f"Lambda: {lambda_pred}")
    print('-' * 20)
    print(f"Probabilidade Over: {prob_over*100:.2f}%")
    print(f"Probabilidade Under: {prob_under*100:.2f}%")
    print(f"EV Over: {ev_over*100:.2f}%")
    print(f"EV Under: {ev_under*100:.2f}%")
    print('-' * 60)

    if ev_over >= EV_THRESHOLD:
        return 'over', data['over_odds'], prob_over, ev_over
    
    elif ev_under >= EV_THRESHOLD:
        return 'under', data['under_odds'], prob_under, ev_under
    
    else:
        return None, None, None

def gerar_mensagem(data):
    
    """
    Gerar mensagem para o Telegram;
    Se EV >= HOT_THRESHOLD, exibir "chamas";
    """

    from constants.telegram_params import (TELEGRAM_MESSAGE,
                            HOT_THRESHOLD, HOT_TIPS_STEP)
    
    mensagem = TELEGRAM_MESSAGE.format(**data)
    
    _ev = data['ev']
    if _ev >= HOT_THRESHOLD: 
        mensagem += f"\n⚠️ EV:"
    
    while True:
        if _ev >= HOT_THRESHOLD:
            mensagem += "🔥"
            _ev -= HOT_TIPS_STEP
        else: break
    
    mensagem += "\n"

    print(mensagem)

def predict(event, model, df_dados):

    
    if not csv_atualizado_event.is_set():
        logging.info("Aguardando a atualização inicial do CSV para iniciar as previsões...")
        csv_atualizado_event.wait()

    # Evita repetir se o evento já falhou
    with open(ERROR_EVENTS, 'r') as file:
        error_events = set(line.strip() for line in file)
        
    if event['id'] in error_events:
        return []

    bets = []

    try:
        from datetime import datetime
        hora_identificacao = datetime.now().strftime('%H:%M:%S')
        print(f"Novo evento identificado às {hora_identificacao}")

        #Extrair dados do evento
        data = extract_data(event)

        """
        Calcular features ao vivo
        TODO: Adicionar trava para caso features insuficientes, não executar.
        """
        from features.new_engineering import calculate_live_features
        features = calculate_live_features(data['home_player'], data['away_player'])
       


        import pandas as pd
        from utils import print_separator
        from features.required_features import REQUIRED_FEATURES
        
        #Criar DataFrame com features
        x = pd.DataFrame([features])
        x = x[REQUIRED_FEATURES]

        print_separator()
        print("Dados reais usados para previsão (X_ao_vivo):")
        print(x.to_string(index=False))
        print_separator()

        """
        Fazer previsão;
        Probabilidades via distribuição de Poisson;
        Imprimir dados do evento;
        """
        
        lambda_pred = model.predict(x)[0]
        print_event_data(data)
        bet_type, odd, prob, ev = calculate_probabilities(data, lambda_pred)

        if bet_type is None:
            print("Nenhuma aposta válida encontrada")
            return None
            
        from model.bets import calculate_new_minimum
        minimum_line = calculate_new_minimum(lambda_pred, data['handicap'], bet_type)
        data.update({
            'bet_type': bet_type,
            'minimum_line': minimum_line,
            'odd': odd,
            'prob': prob,
            'ev': ev
        })
        
        gerar_mensagem(data)
        """
        TODO: enviar mensagem para o Telegram;
        TODO: salvar aposta em xlsx;
        """



    except Exception as e:
        logging.error(f"Erro ao identificar o jogo: {e}")


