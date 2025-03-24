import numpy as np
import pandas as pd
from features.h2h_acessor import H2HAcessor

from files.paths import GAME_DATA
from features.required import REQUIRED_COLUMNS

def time_features(data):
    
    """
    Creation of all time-related features
    Exports: date, last_h2h, time_since_start, day_of_week, hour_of_day, day_angle, hour_angle

    TODO: Is it necessary to export both the angle and the day_of_week and hour_of_day respectively?
    TODO: Analyze if it really helps or causes overfitting.
    """

    data['last_h2h'] = data.h2h.date.transform(lambda x: x.diff().dt.total_seconds() / 3600)
    data['time_since_start'] = (data['date'] - data['date'].min()).dt.days.astype(float)
    data['day_of_week'] = data['date'].dt.weekday.astype(float)
    data['hour_of_day'] = data['date'].dt.hour.astype(float)

    # Add calculation of cyclic components
    data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
    data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
    data['hour_sin'] = np.sin(2 * np.pi * data['hour_of_day'] / 24)
    data['hour_cos'] = np.cos(2 * np.pi * data['hour_of_day'] / 24) 

    # Now we generate the arctangents
    data['day_angle'] = np.arctan2(data['day_sin'], data['day_cos'])
    data['hour_angle'] = np.arctan2(data['hour_sin'], data['hour_cos'])

    # Generate h2h_count
    data['h2h_count'] = data.h2h.cumcount() + 1

    # Drop auxiliary columns
    data = data.drop(['day_sin','day_cos','hour_sin','hour_cos'], axis = 1)
    
    return data

def goal_features(data, time, normalize, live) -> pd.DataFrame: 

    """
    Asserts required columns;
    Normalizes total_goals if normalize is True;
    Shifts total_goals if live is False;
    Creates a working copy of the dataframe;
    Creates all goal-related features.
    Returns the dataframe with the new features appended.
    
    TODO: Finish normalization logic all around the code and repository.
    """
    
    if not REQUIRED_COLUMNS.issubset(data.columns):
        raise ValueError(f"DataFrame must contain the following columns: {REQUIRED_COLUMNS}") 

    data = data.copy()

    if normalize == True:
        data['total_goals'] = data['total_goals'] / data['league'].map(time)

    if live == False:
        data['total_goals'] = data.groupby('matchup_key')['total_goals'].shift()

    def lags(data) -> pd.DataFrame:
        """
        Creates lags for the data
        L1 = Last Match total Score
        L2 = Last 2 Match total Score
        L3 = Last 3 Match total Score

        Creates a new column for each lag, with the lag number.
        TODO: Make this dynamic, so it can be used for any number of lags.
        """
        max_lags = 3
        for lag in range(1, max_lags + 1):
            data[f'l{lag}'] = data.groupby('matchup_key')['gols_totais'].shift(lag)
        
        return data

    def rolling_stats(data, window: int = 3) -> pd.DataFrame:
        
        """
        Creates rolling statistics for the data
        window: Matches that will be used to calculate the statistic
        returns a new column for each statistic: median, std, avg
        """
        
        stats = {
            f'median_{window}': lambda x: x.rolling(window).median(),
            f'std_{window}': lambda x: x.rolling(window).std(ddof=0),
            f'avg_{window}': lambda x: x.rolling(window).mean(),
        }

        for name, func in stats.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(func)
        
        return data

    def ewma(data, alpha: float) -> pd.DataFrame:
        
        """
        Creates a EWMA with the final_score of past matches.
        alpha: intensity weighted on most recent matches
        """

        data[f'ewma_{alpha}'] = data.groupby('matchup_key')['gols_totais'].transform(
            lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        
        return data

    def cumulative_stats(data) -> pd.DataFrame:

        """
        Creates cumulative statistics for the data
        Uses all data to calculate the statistic
        returns a new column for each statistic: median, std, avg
        """
        
        stats = {
            'median': lambda x: x.expanding().median(),
            'std': lambda x: x.expanding().std(ddof=0),
            'avg': lambda x: x.expanding().mean(),
        }

        for name, func in stats.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(func)
        
        return data
    
    data = (data
        .pipe(lags)
        .pipe(rolling_stats)
        .pipe(ewma(alpha=0.3))
        .pipe(ewma(alpha=0.15))
        .pipe(cumulative_stats)
    )

    return data   

def matchup_key(row):
    return tuple(sorted([
    str(row['home_player']).lower(),
    str(row['away_player']).lower()]))

def features(
    data: pd.DataFrame = GAME_DATA,
    lookback_data: pd.DataFrame | None = None,
    live: bool = True,
    normalizar: bool = False,
    tempo: bool = False,
    players: tuple[str, str] = ('', '')
    ) -> pd.DataFrame:
    
    """
    Creates all features for the model
    
    If lookback_data is provided, it will be used to create the features:
        - original_data will be marked as True
        - lookback_data will be marked as False
        - both will be concatenated and sorted by date
        - at the end, lookback_data will be dropped
    
    If live is True, it will return the last match of the two players.

    1- Creates and asserts matchup_key is a tuple of the two players;
    2- Assert date is a datetime object and sorts by date;
    3- Creates all time-related features;
    4- Creates all goal-related features;
    5- Returns the dataframe with the new features appended.
    """

    data['matchup_key'] = data.apply(matchup_key, axis=1)   

    if lookback_data is not None:
        
        original_data = data.copy()
        original_data['__original__'] = True

        lookback_data = lookback_data.copy()
        lookback_data['__original__'] = False
        data = pd.concat([original_data, lookback_data], ignore_index=True)

    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date').reset_index(drop=True)
    
    data = time_features(data)

    data = goal_features(data, normalizar, live, tempo)
    
    if lookback_data is not None:
        data = data[data['__original__']].drop(columns=['__original__'])
        data = data.reset_index(drop=True)

    if live == True: 
        try:  
            data = data[data['matchup_key'] == players]
            current_match = data.tail(1)
            return current_match
        
        except:
            raise ValueError(f"Players {players} not found in the data")

    return data