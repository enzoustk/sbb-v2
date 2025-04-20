import logging
import sys
import pandas as pd
from files.paths import MADE_BETS
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def breaker(threshold: int | float = -10, hours: int = 16):
    """Checks Current Rolling Profit.
    If it is worse than threshold in the last timeframe hours, it stops the bot.
    
    Arguments:
        threshold (int | float): Value to stop execution,
        timeframe (timedelta): Time period to track profit/loss.
    """

    df = pd.read_excel(MADE_BETS)
    df['Horário Envio'] = pd.to_datetime(df['Horário Envio'])

    date_range = datetime.now() - timedelta(hours=hours)

    filtered_df = df[df['Horário Envio'] >= date_range]
    rolling_profit = filtered_df['Lucro'].sum()

    if rolling_profit < threshold:
        logger.critical(f'Circuit Breaker Started, current profit = {rolling_profit}')
        sys.exit()