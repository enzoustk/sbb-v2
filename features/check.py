import pandas as pd
import logging

logger = logging.getLogger(__name__)
bet_logger = logging.getLogger('bet')

def dataframe(home_player: str, away_player: str, df: pd.DataFrame):
    df['home_player'] = df['home_player'].str.lower()
    df['away_player'] = df['away_player'].str.lower()
    home = home_player.lower()
    away = away_player.lower()

    # Contagens separadas
    home_as_home = (df['home_player'] == home).sum()
    home_as_away = (df['away_player'] == home).sum()
    away_as_home = (df['home_player'] == away).sum()
    away_as_away = (df['away_player'] == away).sum()

    # Contagem de jogos entre eles, qualquer que seja a posição
    mutual_games = (
        ((df['home_player'] == home) & (df['away_player'] == away)) |
        ((df['home_player'] == away) & (df['away_player'] == home))
    ).sum()

    home_appearances = home_as_home + home_as_away
    away_appearances = away_as_home + away_as_away

    logger.warning(f"""Apperances in dataframe:
        {home_player}: {home_appearances}, {away_player}: {away_appearances}, H2H: {mutual_games}""")

    


