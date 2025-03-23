import pandas as pd, numpy as np
from features.h2h_acessor import H2HAcessor
from constants.file_params import GAME_DATA

def create_time_features():
    
    import pandas as pd, numpy as np
    

    """
    Cria todas as Features com Relação ao Tempo
    TODO: Analisar se realmente ajuda ou causa overfitting.
    Exporta: date, last_h2h, time_since_start, day_of_week, hour_of_day, day_angle, hour_angle
    TODO: É necessário exportar tanto o ângulo quanto o day_of_week e hour_of_day respectivos?
    """

    data = GAME_DATA

    data['date'] = pd.to_datetime(data['date'])
    data['last_h2h'] = data.h2h.date.transform(lambda x: x.diff().dt.total_seconds() / 3600)
    data['time_since_start'] = (data['date'] - data['date'].min()).dt.days.astype(float)
    data['day_of_week'] = data['date'].dt.weekday.astype(float)
    data['hour_of_day'] = data['date'].dt.hour.astype(float)

    # Adicionar cálculo das componentes cíclicas
    data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
    data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
    data['hour_sin'] = np.sin(2 * np.pi * data['hour_of_day'] / 24)
    data['hour_cos'] = np.cos(2 * np.pi * data['hour_of_day'] / 24) 

    # Agora então geramos as arctangentes
    data['day_angle'] = np.arctan2(data['day_sin'], data['day_cos'])
    data['hour_angle'] = np.arctan2(data['hour_sin'], data['hour_cos'])

    # Gerar h2h_count
    data['h2h_count'] = data.h2h.cumcount() + 1

    # Dropar colunas auxiliares 
    data = data.drop(['day_sin','day_cos','hour_sin','hour_cos'], axis = 1)
    
    return data

def create_goal_features(data, time, normalize, live) -> pd.DataFrame: 

    # Validação inicial
    required_columns = {'jogador_casa', 'jogador_fora', 'gols_totais', 'league'}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"DataFrame deve conter as colunas: {required_columns}") 

    data = data.copy()

    # 1. Normalização
    if normalize:
        data['gols_totais'] = data['gols_totais'] / data['league'].map(time)

    if not live:
        data['gols_totais'] = data.groupby('matchup_key')['gols_totais'].shift()

    # 2. Features Lag (Live Mode Safe)
    def criar_lags(data) -> pd.DataFrame:
        max_lags = 3
        for lag in range(1, max_lags + 1):
            if live:
                data[f'l{lag}'] = data.groupby('matchup_key')['gols_totais'].shift(lag)
            else:
                data[f'l{lag}'] = data.groupby('matchup_key')['gols_totais'].transform(lambda x: x.shift(lag))
        return data

    # 3. Rolling Statistics (Otimizado)
    def criar_rolling_stats(data, window: int = 3) -> pd.DataFrame:
        stats = {
            'median_3': lambda x: x.rolling(window).median(),
            'std_3': lambda x: x.rolling(window).std(ddof=0),
            'avg_3': lambda x: x.rolling(window).mean(),
        }

        for name, func in stats.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(func)
        
        return data

    # 4. EWMA (Versão Vetorizada)
    def criar_ewma(data) -> pd.DataFrame:
        alpha_config = {
            'ewma_15': 0.15,
            'ewma_3': 0.03
        }

        for name, alpha in alpha_config.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(
                lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        
        return data
    

    # 5. Cumulative Statistics (Performance)
    def criar_cumulative_stats(data) -> pd.DataFrame:
        stats = {
            'median': lambda x: x.expanding().median(),
            'std': lambda x: x.expanding().std(ddof=0),
            'avg': lambda x: x.expanding().mean(),
        }

        for name, func in stats.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(func)
        
        return data
    

    # Pipeline de execução
    data = (data
        .pipe(criar_lags)
        .pipe(criar_rolling_stats)
        .pipe(criar_ewma)
        .pipe(criar_cumulative_stats)
    )

    return data   

def calculate_features(
    data: pd.DataFrame = GAME_DATA,
    lookback_data: pd.DataFrame | None = None,
    live: bool = True,
    normalizar: bool = False,
    tempo: bool = False
    ) -> pd.DataFrame:
    
    #Marcar dados pertencetes ao 'data' original
    original_data = data.copy()
    original_data['__original__'] = True

    #Fazer uso de dados de treino, caso existentes 
    if lookback_data is not None:
        lookback_data = lookback_data.copy()
        lookback_data['__original__'] = False
        data = pd.concat([original_data, lookback_data], ignore_index=True)
    else:
        data = original_data

    #Garantir datetime e ordenação cronológica 
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date').reset_index(drop=True)

    data['matchup_key'] = data.apply(lambda row: tuple(sorted([
        str(row['jogador_casa']).lower(),
        str(row['jogador_fora']).lower()])),
        axis=1)
    
    # Geração de features propriamente dita:
    
    """
    # Índices:
    if live:
        data = coletar_indices(data,INDICES_DATABASE)
    elif not live:
        data = criar_indices(data, INDICES_DATABASE)
    """

    # Temporais
    data = create_time_features(data)

    # Lags
    data = create_goal_features(
        data,
        normalizar = normalizar,
        live = live,
        tempo = tempo
        )
    
    # Filtro final e limpeza de dados externos
    data = data[data['__original__']].drop(columns=['__original__'])
    data = data.reset_index(drop=True)
    return data

def calculate_training_features():
    return calculate_features(live=False)

def calculate_live_features(home_player, away_player):
    """
    Cria um dataframe somente com as features em H2H dos dois jogadores,
    Calcula as features ao vivo utilizando o DataFrame criado,
    Retorna um dataframe de uma linha com as features calculadas.
    """
    # Criar chave de confronto normalizada
    matchup_key = tuple(sorted([
        str(home_player).lower(),
        str(away_player).lower()
    ]))
    
    # Filtrar histórico usando a lógica existente do accessor h2h
    confronto_df = GAME_DATA[GAME_DATA['matchup_key'] == matchup_key]
    
    if confronto_df.empty:
        return pd.DataFrame()
    
    # Reutilizar a função calculate_features existente
    return calculate_features(
        data=confronto_df,
        live=True
    ).tail(1)