def poisson(lambda_pred: float, handicap: float) -> tuple[float, float]:

    from scipy.stats import poisson

    """
    Calcula a probabilidade dado um handicap.
    TODO: Ajustar para possibilitar uso de outros mercados.
    """
    
    if handicap % 1 == 0.5:  # Handicap terminado em 0.5
        prob_over = 1 - poisson.cdf(int(handicap), lambda_pred)
        prob_under = poisson.cdf(int(handicap), lambda_pred)

    elif handicap % 1 == 0.0:  # Handicap inteiro
        prob_over_raw = 1 - poisson.cdf(int(handicap), lambda_pred)
        prob_under_raw = poisson.cdf(int(handicap) - 1, lambda_pred)
        total = prob_over_raw + prob_under_raw
        prob_over = prob_over_raw / total
        prob_under = prob_under_raw / total

    elif handicap % 1 in [0.25, 0.75]:  # Handicap terminado em 0.25 ou 0.75
        lower = handicap - 0.25
        upper = handicap + 0.25
        prob_over_lower, prob_under_lower = poisson(lambda_pred, lower)
        prob_over_upper, prob_under_upper = poisson(lambda_pred, upper)
        prob_over = (prob_over_lower + prob_over_upper) / 2
        prob_under = (prob_under_lower + prob_under_upper) / 2

    else:
        raise ValueError(f"Handicap inválido: {handicap}")
    
    return prob_over, prob_under

def minimum(lambda_pred: float, initial_line: float, bet_type: str) -> tuple[float, float]:

    current_line = initial_line

    if bet_type.lower() == 'over': step = 0.25
    elif bet_type.lower() == 'under': step = -0.25
    else: raise ValueError(f"Tipo de aposta inválido: {bet_type}")

    """
    Calcular a odd EV == threshold para a linha atual,
    Se a odd mínima for inferior a 1.75, 'piorar' a linha em 0.25
    Repetir até que a odd mínima seja superior a 1.75
    """

    while True:
        from model.config import EV_THRESHOLD
        prob_over, prob_under = poisson(lambda_pred, current_line)

        if bet_type.lower() == 'over': prob = prob_over
        elif bet_type.lower() == 'under': prob = prob_under
        else: raise ValueError(f"Tipo de aposta inválido: {bet_type}")

        minimal_odd = (1.0 + EV_THRESHOLD) / prob

        if minimal_odd >= 1.75:
            return current_line, minimal_odd

        elif minimal_odd < 1.75: current_line += step

        else: raise ValueError(f"Odd mínima inválida: {minimal_odd}")

def probabilities(data: dict, lambda_pred: float) -> tuple[str, float, float, float] | None:
    from model.calculate import poisson
    from model.config import EV_THRESHOLD

    """
    Calcular probabilidades e EV;
    Retornar probabilidades e EV caso seja maior que o threshold;
    Retornar None caso não seja maior que o threshold;
    Imprimir dados do evento;
    """

    prob_over, prob_under = poisson(lambda_pred, data['handicap'])
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
        print('Não há EV')
        return None

def pl(bet_type: str, handicap: float, odd: float, home_score: int, away_score: int) -> float:
    
    """
    Calcular o PL dado um tipo de aposta, handicap, odd e resultado.
    TODO: Permitir outros mercados.
    TODO: Permitir stake variável.
    """

    total_gols = home_score + away_score

    if bet_type.lower() == 'over': bet_outcome = total_gols - handicap
    elif bet_type.lower() == 'under': bet_outcome = handicap - total_gols
    
    else:
        raise ValueError("Tipo de aposta deve ser 'over' ou 'under'")

    if bet_outcome >= 0.5: return (odd - 1) 
    elif bet_outcome == 0.25: return (odd - 1) / 2
    elif bet_outcome == 0: return 0
    elif bet_outcome == -0.25: return -0.5 
    elif bet_outcome <= -0.5: return -1
    
    else: 
        raise ValueError(f"Ajuste de resultado inválido: {bet_outcome}")