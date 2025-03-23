def calculate_poisson(lambda_pred, handicap):

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
        prob_over_lower, prob_under_lower = calculate_poisson(lambda_pred, lower)
        prob_over_upper, prob_under_upper = calculate_poisson(lambda_pred, upper)
        prob_over = (prob_over_lower + prob_over_upper) / 2
        prob_under = (prob_under_lower + prob_under_upper) / 2

    else:
        raise ValueError(f"Handicap inválido: {handicap}")
    
    return prob_over, prob_under

def calculate_new_minimum(lambda_pred, initial_line, bet_type):
    from model.bets import calculate_poisson

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
        from model.model_config import EV_THRESHOLD
        prob_over, prob_under = calculate_poisson(lambda_pred, current_line)

        if bet_type.lower() == 'over': prob = prob_over
        elif bet_type.lower() == 'under': prob = prob_under
        else: raise ValueError(f"Tipo de aposta inválido: {bet_type}")

        minimal_odd = (1.0 + EV_THRESHOLD) / prob

        if 1.75 <= minimal_odd:
            return current_line, minimal_odd

        elif minimal_odd < 1.75: current_line += step

        else: raise ValueError(f"Odd mínima inválida: {minimal_odd}")
        
def calculate_pl(bet_type, handicap, odd, home_score, away_score):
    
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