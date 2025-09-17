"""Formats and validates the data from the API."""

import logging
from api.constants import MARKET_IDS

logger = logging.getLogger(__name__)

def select_latest_null_time_str(odds_list: list[dict]) -> dict | None:
    """
    1) Filtra seleções com time_str == None ou 'null' e retorna a de maior add_time.
    2) Se não encontrar, filtra seleções com ss == '0:0' e time_str == '1 - 05:00'
       e retorna a de maior add_time.
    3) Se ainda não achar, retorna None.
    """
    try:
        # Regra 1: time_str é None ou 'null'
        null_ts = [
            o for o in odds_list
            if o.get("time_str") in (None, "null")
        ]
        if null_ts:
            return max(null_ts, key=lambda o: int(o.get("add_time", 0)))

        # Regra 2: fallback em ss=='0:0' e time_str=='1 - 05:00'
        fallback = [
            o for o in odds_list
            if o.get("ss") == '0:0' and o.get("time_str") == '1 - 05:00'
        ]
        if fallback:
            return max(fallback, key=lambda o: int(o.get("add_time", 0)))

    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao selecionar latest_null_time_str: {e}")

    return None

def odds(
    betting_data: dict,
    event_id: str,
    market: str = 'spread',
) -> tuple[float | None, float | None, float | None, float | None]:
    """
    Receives a dict and returns (handicap, home_od, away_od) for the requested market.
    """
    odds_data = betting_data.get('results', {}).get('odds', {})
    market_key = MARKET_IDS.get(market)
    if market_key not in odds_data:
        logger.error(f"Betting Market '{market}' not found for event {event_id}")
        return {
            'home_handicap': None,
            'away_handicap': None,
            'home_od': None,
            'away_od': None,
            
            'handicap': None,
            'over_od': None,
            'under_od': None

        }

    market_data = odds_data[market_key]

    # Vai filtrar para o market correto
    valid_odds = filter_odds(market_data, market=market)

    if not valid_odds:
        logger.warning(f"No odds available for event {event_id} in market '{market}'")
        return {
            'home_handicap': None,
            'away_handicap': None,
            'home_od': None,
            'away_od': None,
            
            'handicap': None,
            'over_od': None,
            'under_od': None

        }
    
    selected = min(
        valid_odds,
        key=lambda x:
        x.get(
        'add_time', float('inf'))
        )

    if market == 'spread':
        home_handicap = spread(selected.get('handicap'))
        away_handicap = -home_handicap if home_handicap is not None else None

        try:
            home_od = float(selected.get('home_od'))
            away_od = float(selected.get('away_od'))
        
        except (TypeError, ValueError) as e:
            logger.error(f"Error converting home/away odds for event {event_id}: {e}")
            return home_handicap, away_handicap, None, None

        return {
            'home_handicap': home_handicap,
            'away_handicap': away_handicap,
            'home_od': home_od,
            'away_od': away_od
        }
    
    if market == 'total':
        
        handicap = float(goal_handicap(selected.get('handicap')))

        try:
            over_od = float(selected.get('over_od'))
            under_od = float(selected.get('under_od'))
        
        except (TypeError, ValueError) as e:
            logger.error(f"Error converting home/away odds for event {event_id}: {e}")
            
        
        return handicap, over_od, under_od
        

def spread(spread) -> float | None:
    """
    Converte handicap vindo como string ou número para float,
    retornando None em caso de erro.
    """
    try:
        if isinstance(spread, str):
            return float(spread.strip())
        return float(spread)
    except (TypeError, ValueError) as ve:
        logger.error(f"Error converting handicap '{spread}': {ve}")
        return None

def filter_odds(market_data: list[dict], market: str = 'spread') -> list[dict]:
    """
    Filtra lista de odds mantendo apenas entradas com o trio de odds válido.
    """
    assert market in {'spread', 'total'}, f"market inválido: {market!r}. Deve ser 'spread' ou 'total'."

    if market == 'spread':
        market_1 = 'home'
        market_2 = 'away'
    
    else:
        market_1 = 'over'
        market_2 = 'under'

    return [
        odd for odd in market_data
        if (
            isinstance(odd, dict)
            and odd.get(f"{market_1}_od") not in (None, '-')
            and odd.get(f"{market_2}_od") not in (None, '-')
            and odd.get("handicap") not in (None, '-')
        )
    ]
    
def goal_handicap(handicap) -> float | None:

    """
    Gets the handicap from the API and solves type errors,
    Also, converts it to a float and returns the current handicap if successful.
    """

    try: 
        if isinstance(handicap, str):
            if ',' in handicap:
                handicap_vals = [float(h.strip()) for h in handicap.split(',')]
                handicap = sum(handicap_vals) / len(handicap_vals)
            
            else:
                handicap = float(handicap.strip())
        
        return handicap
    
    except ValueError as ve:
        logger.error(f"Error converting handicap '{handicap}': {ve}")
        return None
