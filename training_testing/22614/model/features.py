import pandas as pd
import numpy as np

def time_features(
    data: pd.DataFrame
    ) -> pd.DataFrame:

    data['day_of_week'] = data['date'].dt.weekday.astype(float)
    data['hour_of_day'] = data['date'].dt.hour.astype(float)

    data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
    data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
    data['hour_sin'] = np.sin(2 * np.pi * data['hour_of_day'] / 24)
    data['hour_cos'] = np.cos(2 * np.pi * data['hour_of_day'] / 24) 

    data = data.drop(
        ['day_of_week','hour_of_day'],
        axis = 1)
    
    return data


def matchup_features(
    data: pd.DataFrame,
    n: int = 9
) -> pd.DataFrame:
    """
    Creates all features related to number of matches played and its attributes.
    """
    # Ordena por data e cria cópia segura
    data = data.sort_values('date').copy()
    
    # 1. Time since start
    data['time_since_start'] = (data['date'] - data['date'].min()).dt.days.astype(float)
    
    # 2. Last H2H (horas desde a última partida do mesmo matchup)
    data['last_h2h'] = (
        data.groupby('matchup_key')['date']
        .transform(lambda x: x.diff().dt.total_seconds() / 3600)
    )
    
    # 3. H2H Count (total acumulado de partidas por matchup)
    data['h2h_count'] = data.groupby('matchup_key').cumcount() + 1
    
    # 4. H2H N Hours Count (partidas nas últimas N horas) ***CORREÇÃO FINAL***
    data['tmp_window_start'] = data['date'] - pd.Timedelta(hours=n)
    
    # Usa merge_asof para contagem temporal eficiente
    data = data.sort_values('date')
    data[f'h2h_{n}h_count'] = (
        data.groupby('matchup_key', group_keys=False)
        .apply(
            lambda grp: grp.apply(
                lambda row: grp[
                    (grp['date'] > row['tmp_window_start']) & 
                    (grp['date'] < row['date'])
                ].shape[0],
                axis=1
            )
        )
    ).astype(int)
    
    # 5. Is Return Match (verifica se é revanche imediata)
    data['current_pair'] = data.apply(
        lambda x: tuple(sorted([x['home_team'], x['away_team']])), 
        axis=1
    )
    data['previous_pair'] = data.groupby('matchup_key')['current_pair'].shift(1)
    data['is_return_match'] = (data['current_pair'] == data['previous_pair']).astype(int).fillna(0)
    
    # Remove colunas auxiliares
    return data.drop(['current_pair', 'previous_pair', 'tmp_window_start'], axis=1)


def goal_features(
    data: pd.DataFrame, 
    pace: bool, 
    normalize: bool,
    live: bool
    ) -> pd.DataFrame: 
    
    """
    if not REQUIRED_COLUMNS.issubset(data.columns):
        logging.error(f"DataFrame must contain the following columns: {REQUIRED_COLUMNS}") 
    """

    data = data.copy()

    
    data["original_total_score"] = data["total_score"].copy()

    if normalize == True:
        data['total_score'] = data['total_score'] / data['league'].map(pace)

    if live == False:
        data['total_score'] = data.groupby('matchup_key')['total_score'].shift()
    
    #  Extrai posições do matchup_key
    data['home_pos'] = data['matchup_key'].str[0]
    data['away_pos'] = data['matchup_key'].str[1]
        
    # Define scores dinamicamente para cada posição
    data['score_home_pos'] = np.where(
        data['home_pos'] == data['home_team'],  # Condição
        data['home_score'],                      # Valor se True
        data['away_score']                       # Valor se False
    )
        
    data['score_away_pos'] = np.where(
        data['away_pos'] == data['away_team'],
        data['away_score'],
        data['home_score']
    )

    def lags(data: pd.DataFrame = data) -> pd.DataFrame:
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
            data[f'l{lag}'] = data.groupby('matchup_key')['total_score'].shift(lag)
        
        return data

    def rolling_stats(data: pd.DataFrame = data, window: int = 3) -> pd.DataFrame:
        
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
            data[name] = data.groupby('matchup_key')['total_score'].transform(func)
        
        return data

    def ewma(data: pd.DataFrame = data, alpha: float = 0.03) -> pd.DataFrame:
        
        """
        Creates a EWMA with the final_score of past matches.
        alpha: intensity weighted on most recent matches
        """

        data[f'ewma_{alpha}'] = data.groupby('matchup_key')['total_score'].transform(
            lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        
        return data

    def cumulative_stats_indv(data: pd.DataFrame) -> pd.DataFrame:
        """
        Creates cumulative statistics (median, std, avg) for both 'home_pos_score' and 'away_pos_score'.
        Statistics are calculated within each group of 'matchup_key'.
        Returns new columns for each combination of metric and score type (e.g., 'home_median', 'away_avg').
        """
        
        # Define as estatísticas a serem calculadas
        stats = {
            'median': lambda x: x.expanding().median(),
            'std': lambda x: x.expanding().std(ddof=0),
            'avg': lambda x: x.expanding().mean(),
        }

        # Colunas alvo e prefixos para os novos nomes
        score_columns = {
            'score_home_pos': 'home',
            'score_away_pos': 'away'
        }

        # Calcula as estatísticas para cada coluna e métrica
        for score_col, prefix in score_columns.items():
            for stat_name, stat_func in stats.items():
                new_col = f"{prefix}_{stat_name}"
                data[new_col] = data.groupby('matchup_key')[score_col].transform(stat_func)
        
        return data
    

    
    def rolling_stats_indv(data: pd.DataFrame, window: int = 3) -> pd.DataFrame:
        """
        Cria estatísticas rolantes seguras contra data leakage:
        - Ordena por data dentro de cada grupo
        - Usa janela fechada à esquerda (closed='left')
        - Adiciona shift(1) para excluir valor atual
        """
        data = data.sort_values('date').copy()
        
        # Novo dicionário de estatísticas com proteção contra leakage
        stats = {
            'median': lambda x: (
                x.rolling(window, min_periods=1, closed='left')
                .median()
            ),
            'std': lambda x: (
                x.rolling(window, min_periods=1, closed='left')
                .std(ddof=0)
                .shift(1)
            ),
            'avg': lambda x: (
                x.rolling(window, min_periods=1, closed='left')
                .mean()
            )
        }

        # Cálculo para home_pos
        for stat, func in stats.items():
            data[f'{stat}_{window}_home_pos'] = (
                data.groupby('home_pos', group_keys=False)['score_home_pos']
                .transform(func)
            )
        
        # Cálculo para away_pos
        for stat, func in stats.items():
            data[f'{stat}_{window}_away_pos'] = (
                data.groupby('away_pos', group_keys=False)['score_away_pos']
                .transform(func)
            )
        
        return data

    def consistency(data: pd.DataFrame, window: int =3) -> pd.DataFrame:     
        data[f'consistency_{window}_home_pos'] = data[f'avg_{window}_home_pos'] / (data[f'std_{window}_home_pos'] + 1e-6).clip(lower=-10,upper=10)
        data[f'consistency_{window}_away_pos'] = data[f'avg_{window}_away_pos'] / (data[f'std_{window}_away_pos'] + 1e-6).clip(lower=-10,upper=10)
        return data

    def deltas(data: pd.DataFrame, lower: int = 3, upper: int = 10, metric: str = 'avg') ->pd.DataFrame:
        window = f'{upper}-{lower}'
        data[f'delta_{metric}_{window}_home_pos'] = data[f'{metric}_{lower}_home_pos'] - data[f'{metric}_{upper}_home_pos']
        data[f'delta_{metric}_{window}_away_pos'] = data[f'{metric}_{lower}_away_pos'] - data[f'{metric}_{upper}_away_pos']
        return data

    data = lags(data)
    data = rolling_stats(data, window=3)
    data = rolling_stats(data, window=10)
    data = rolling_stats_indv(data, window=10)
    data = rolling_stats_indv(data, window=3)
    data = consistency(data, window=3)
    data = consistency(data, window=10)
    data = deltas(data, metric='avg')
    data = deltas(data, metric='std')
    data = ewma(data, alpha=0.03)
    data = ewma(data, alpha=0.15)
    #data = cumulative_stats(data)
    data = cumulative_stats_indv(data)

    data["total_score"] = data["original_total_score"]
    data = data.drop(columns=["original_total_score"])  


    return data   


def matchup_key(row):
    """Creates a column with the matchup key for the two players"""
    return tuple(sorted([
    str(row['home_player']).lower(),
    str(row['away_player']).lower()]))


def features(
    data: pd.DataFrame,
    lookback_data: pd.DataFrame | None = None,
    live: bool = True,
    normalize: bool = False,
    pace: bool = False,
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

    #TODO: Fix normalize param

    data = data.copy()


    data['matchup_key'] = data.apply(matchup_key, axis=1)   
    data = data.sort_values(['matchup_key', 'date']).reset_index(drop=True)
    
    if lookback_data is not None:
        original_data = data.copy()
        original_data['__original__'] = True

        lookback_data = lookback_data.copy()
        lookback_data['__original__'] = False
        lookback_data['matchup_key'] = lookback_data.apply(matchup_key, axis=1)  # Correção aqui
        
        data = pd.concat([original_data, lookback_data], ignore_index=True)

    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date']).reset_index(drop=True)
    
    #data = time_features(data)
    data = matchup_features(data)
    data = goal_features(data, pace, normalize, live)
    
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