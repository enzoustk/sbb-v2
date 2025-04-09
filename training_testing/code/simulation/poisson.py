def calcular_probabilidades_poisson(lambda_pred, handicap):

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
        prob_over_lower, prob_under_lower = calcular_probabilidades_poisson(lambda_pred, lower)
        prob_over_upper, prob_under_upper = calcular_probabilidades_poisson(lambda_pred, upper)
        prob_over = (prob_over_lower + prob_over_upper) / 2
        prob_under = (prob_under_lower + prob_under_upper) / 2

    else:
        raise ValueError(f"Handicap inválido: {handicap}")
    
    return prob_over, prob_under
