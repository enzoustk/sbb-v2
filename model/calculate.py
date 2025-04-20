import logging
import numpy as np
from scipy.stats import poisson
from model.betting_config import EV_THRESHOLD

logger = logging.getLogger(__name__)
bet_logger = logging.getLogger('bet')

def poisson_log_loss(y_true, y_pred):

    prob = np.array([poisson.pmf(k, y_pred) for k in y_true])
    return -np.mean(np.log(prob + 1e-10)) 


def poisson_goals(
    lambda_pred: float,
    handicap: float
    ) -> tuple[float, float]:

    """
    Calculate the Probability of a given Goal Line (Handicap).
    TODO: Create Poisson Probabilities for other markets.
    """
    def half_goal_handicap(handicap, lambda_pred) -> tuple[float,float]:
        prob_over = 1 - (poisson.cdf(int(handicap), lambda_pred))
        prob_under = (poisson.cdf(int(handicap), lambda_pred))
        
        return float(prob_over), float(prob_under)
    
    def integer_handicap(handicap,lambda_pred) -> tuple[float,float]:
        prob_over_raw = 1 - (poisson.cdf(int(handicap), lambda_pred))
        prob_under_raw = (poisson.cdf(int(handicap) - 1, lambda_pred))
        
        total = prob_over_raw + prob_under_raw
        
        prob_over = prob_over_raw / total
        prob_under = prob_under_raw / total

        return float(prob_over), float(prob_under)
    
    def quarter_handicap(handicap,lambda_pred) -> tuple[float,float]:
        
        lower = handicap - 0.25
        upper = handicap + 0.25
        probs_over = []
        probs_under = []

        for line in lower, upper:
            if line % 1 == 0.5:
                over, under = half_goal_handicap(
                handicap=line,
                lambda_pred=lambda_pred
            )
                
            elif line % 1 == 0.0:  
                over, under = integer_handicap(
                handicap=line,
                lambda_pred=lambda_pred
            )
            
            probs_over.append(over)
            probs_under.append(under)
        
        prob_over = sum(probs_over) / len(probs_over) 
        prob_under = sum(probs_under) / len(probs_under)
        
        return float(prob_over), float(prob_under)

    if handicap % 1 == 0.5:
        prob_over, prob_under = half_goal_handicap(
            handicap=handicap,
            lambda_pred=lambda_pred
        )

    elif handicap % 1 == 0.0:  
        prob_over, prob_under = integer_handicap(
            handicap=handicap,
            lambda_pred=lambda_pred
        )

    elif handicap % 1 in [0.25, 0.75]:  
        prob_over, prob_under = quarter_handicap(
            handicap=handicap,
            lambda_pred=lambda_pred
        )
    
    else:
        logger.error(f'Invalid Handicap used to estimate goal probabilities: {handicap}')
        raise ValueError(f"Handicap inválido: {handicap}")
    
    return prob_over, prob_under


def min_goal_line(
    lambda_pred: float,
    handicap: float,
    bet_type: str,
    bet_prob: float
    ) -> tuple[float, float]:
    
    """
    Calcular a odd EV == threshold para a linha atual,
    Se a odd mínima for inferior a 1.75, 'piorar' a linha em 0.25
    Repetir até que a odd mínima seja superior a 1.75
    """

    minimum_line = handicap

    if bet_type.lower() == 'over': 
        step = 0.25
        prob = 0

    elif bet_type.lower() == 'under': 
        step = -0.25
        prob = 1

    else: 
        logger.error(f"Tipo de aposta inválido: {bet_type}")

    while True:
        
        bet_prob = poisson_goals(lambda_pred=lambda_pred, handicap=minimum_line)

        minimum_odd = round((1.0 + EV_THRESHOLD) / bet_prob[prob], 2)

        if minimum_odd >= 1.75:
            return minimum_line, minimum_odd

        elif minimum_odd < 1.75: 
            minimum_line += step
        
        else: 
            logger.error(f'Invalid Min. Odd: {minimum_odd}')


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
            profit = -1
            result = 'loss'
        
        return profit, result
        
    except: 
        logger.error(f"Ajuste de resultado inválido: {outcome}")
        return 0, 'error'


def ev(odd, prob):
    return odd * prob -1