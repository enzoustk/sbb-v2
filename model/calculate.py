def poisson_goals(lambda_pred: float, handicap: float) -> tuple[float, float]:

    from scipy.stats import poisson

    """
    Calculate the Probability of a given Goal Line (Handicap).
    TODO: Create Poisson Probabilities for other markets.
    """
    
    if handicap % 1 == 0.5:
        prob_over = 1 - poisson.cdf(int(handicap), lambda_pred)
        prob_under = poisson.cdf(int(handicap), lambda_pred)

    elif handicap % 1 == 0.0:  
        prob_over_raw = 1 - poisson.cdf(int(handicap), lambda_pred)
        prob_under_raw = poisson.cdf(int(handicap) - 1, lambda_pred)
        total = prob_over_raw + prob_under_raw
        prob_over = prob_over_raw / total
        prob_under = prob_under_raw / total

    elif handicap % 1 in [0.25, 0.75]:  
        lower = handicap - 0.25
        upper = handicap + 0.25
        prob_over_lower, prob_under_lower = poisson(lambda_pred, lower)
        prob_over_upper, prob_under_upper = poisson(lambda_pred, upper)
        prob_over = (prob_over_lower + prob_over_upper) / 2
        prob_under = (prob_under_lower + prob_under_upper) / 2

    else:
        raise ValueError(f"Handicap inválido: {handicap}")
    
    return prob_over, prob_under

def min_goal_line(handicap: float, bet_type: str, bet_prob: float) -> tuple[float, float]:
    
    """
    Calcular a odd EV == threshold para a linha atual,
    Se a odd mínima for inferior a 1.75, 'piorar' a linha em 0.25
    Repetir até que a odd mínima seja superior a 1.75
    """

    minimum_line = handicap

    if bet_type.lower() == 'over': 
        step = 0.25
    elif bet_type.lower() == 'under': 
        step = -0.25
    else: 
        raise ValueError(f"Tipo de aposta inválido: {bet_type}")

    while True:
        from model.config import EV_THRESHOLD

        minimum_odd = ((1.0 + EV_THRESHOLD) / bet_prob).round(2)

        if minimum_odd >= 1.75:
            return minimum_line, minimum_odd

        elif minimum_odd < 1.75: minimum_line += step

        else: raise ValueError(f"Odd mínima inválida: {minimum_odd}")

def profit(bet_type: float, handicap: float, total_score: int, bet_odd: float) -> float:
    
    """
    Calcular o PL dado um tipo de aposta, handicap, odd e resultado.
    TODO: Permitir outros mercados.
    TODO: Permitir stake variável.
    """

    if bet_type.lower() == 'over': outcome = total_score - handicap
    elif bet_type.lower() == 'under': outcome = handicap - total_score

    try:
        if outcome >= 0.5: 
            profit = (bet_odd - 1)
            result = 'win' 
        elif outcome == 0.25: 
            profit = (bet_odd - 1) / 2
            result = 'half_win'
        elif outcome == 0: 
            profit = 0
            result = 'push'
        elif outcome == -0.25:
            profit = -0.5 
            result = 'half_loss'
        elif outcome <= -0.5: 
            profit -1
            result = 'loss'
        return profit, result
        
    except: 
        raise ValueError(f"Ajuste de resultado inválido: {outcome}")

def ev(odd, prob):
    return odd * prob -1