import pandas as pd
import numpy as np

def calcular_features(df, include_current_game=False):
    # Criar cópia segura do DataFrame
    df = df.copy()
    df = df.sort_values('data')

    # ========= 0. Pré-processamento Inicial =========
    # Mapeamento da duração da partida
    duracao_mapeamento = {38439: 6, 22614: 8, 37298: 8, 23114: 12}
    df['duracao_partida'] = df['league'].map(duracao_mapeamento).fillna(8).astype(float)

    # Criar índices únicos
    jogadores = sorted(set(df['jogador_casa'].str.lower()) | set(df['jogador_fora'].str.lower()))
    jogador_index = {jogador: idx for idx, jogador in enumerate(jogadores)}
    
    times = sorted(set(df['time_casa'].str.lower()) | set(df['time_fora'].str.lower()))
    time_index = {time: idx for idx, time in enumerate(times)}

    # Mapear IDs
    df['idx_jogador_casa'] = df['jogador_casa'].str.lower().map(jogador_index).astype(int)
    df['idx_jogador_fora'] = df['jogador_fora'].str.lower().map(jogador_index).astype(int)
    df['idx_time_casa'] = df['time_casa'].str.lower().map(time_index).astype(int)
    df['idx_time_fora'] = df['time_fora'].str.lower().map(time_index).astype(int)

    # ========= 1. Features de Confronto =========
    df['confronto_key'] = df.apply(lambda row: tuple(sorted([row['idx_jogador_casa'], row['idx_jogador_fora']])), axis=1)
    unique_confrontos = df['confronto_key'].unique()
    confronto_index = {key: idx for idx, key in enumerate(unique_confrontos)}
    df['confronto_idx'] = df['confronto_key'].map(confronto_index).astype(int)
    
    # Features históricas
    df['h2h_count'] = df.groupby('confronto_key').cumcount().astype(float)
    df['data'] = pd.to_datetime(df['data'])
    
    # Cálculo do ult_h2h com conversão explícita
    df['ult_h2h'] = df.groupby('confronto_key')['data'].transform(
        lambda x: x.diff().dt.total_seconds().astype(float) / 3600
    )
    if not include_current_game:
        df['ult_h2h'] = df.groupby('confronto_key')['ult_h2h'].shift()

    # ========= 2. Features Temporais de Gols =========
    def safe_mode(s):
        modes = s.mode()
        return modes.iloc[0] if not modes.empty else np.nan

    # Lags
    for i in range(1, 4):
        df[f'l{i}'] = df.groupby('confronto_key')['gols_totais'].shift(i).astype(float)

    # Janela móvel
    rolling_config = {
        'mediana_3': lambda x: x.shift().rolling(3).median(),
        'std_3': lambda x: x.shift().rolling(3).std(ddof=1),
        'media_3': lambda x: x.shift().rolling(3).mean(),
        'moda_3': lambda x: x.shift().rolling(3).apply(safe_mode, raw=False)
    }
    
    for name, func in rolling_config.items():
        df[name] = df.groupby('confronto_key')['gols_totais'].transform(func).astype(float)

    # Cumulativas
    cumul_shift = lambda x: x.shift().expanding()
    cumulative_config = {
        'mediana_total': lambda x: cumul_shift(x).median(),
        'std_total': lambda x: cumul_shift(x).std(ddof=1),
        'media_total': lambda x: cumul_shift(x).mean(),
        'moda_total': lambda x: cumul_shift(x).apply(safe_mode, raw=False)
    }
    
    for name, func in cumulative_config.items():
        df[name] = df.groupby('confronto_key')['gols_totais'].transform(func).astype(float)

    # EWMA
    df['ewma_total_15'] = df.groupby('confronto_key')['gols_totais'].transform(
        lambda x: x.shift().ewm(span=max(1, int(len(x)*0.15)), adjust=False).mean()
    ).astype(float)
    
    df['ewma_total_3'] = df.groupby('confronto_key')['gols_totais'].transform(
        lambda x: x.shift().ewm(span=3, adjust=False).mean()
    ).astype(float)

    # ========= 3. Features Temporais =========
    primeira_partida = df['data'].min()
    df['tempo_dia_zero'] = (df['data'] - primeira_partida).dt.days.astype(float)
    
    # Ciclos temporais
    df['day_of_week'] = df['data'].dt.weekday.astype(float)
    df['hour_of_day'] = df['data'].dt.hour.astype(float)  # Corrigir nome da coluna

    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7).astype(float)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7).astype(float)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24).astype(float)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24).astype(float)  # Usar hour_of_day


    # ========= 4. Target Encoding =========
    global_mean = df['gols_totais'].mean()
    alpha = 5

    # Função de encoding genérica
    def target_encoder(group, global_mean, alpha):
        cum_sum = group.expanding().sum().shift()
        cum_count = group.expanding().count().shift()
        return (cum_sum + global_mean * alpha) / (cum_count + alpha)

    # Aplicar encoding
    encoding_config = {
        'te_confronto': 'confronto_idx',
        'te_jogador_casa': 'idx_jogador_casa',
        'te_jogador_fora': 'idx_jogador_fora',
        'te_time_casa': 'idx_time_casa',
        'te_time_fora': 'idx_time_fora'
    }
    
    for target_col, group_col in encoding_config.items():
        df[target_col] = df.groupby(group_col)['gols_totais'].transform(
            lambda x: target_encoder(x, global_mean, alpha)
        ).astype(float).fillna(global_mean)

    # ========= 5. One-Hot Encoding e Normalização =========
    # One-Hot para league com conversão explícita
    league_dummies = pd.get_dummies(df['league'], prefix='league').astype(float)
    df = pd.concat([df, league_dummies], axis=1)

    # Normalização pelas durações
    goal_features = ['l1', 'l2', 'l3', 'mediana_3', 'std_3', 'media_3', 'moda_3',
                    'mediana_total', 'std_total', 'media_total', 'moda_total',
                    'ewma_total_15', 'ewma_total_3']
    
    for col in goal_features:
        df[col] = (df[col] / df['duracao_partida']).astype(float)

    # ========= 6. Validação Final =========
    required_numeric = [
        'tempo_dia_zero', 'day_of_week', 'hour_of_day',
        'day_sin', 'day_cos', 'hour_sin', 'hour_cos',
        'h2h_count', 'ult_h2h', 'te_confronto',
        'te_time_casa', 'te_time_fora', 'te_jogador_casa',
        'te_jogador_fora', 'league_38439', 'league_22614',
        'league_37298', 'league_23114', 'l1', 'l2', 'l3',
        'mediana_3', 'std_3', 'media_3', 'moda_3',
        'ewma_total_15', 'ewma_total_3', 'mediana_total',
        'std_total', 'media_total', 'moda_total'
    ]

    # Verificação de tipos e NaNs
    for col in required_numeric:
        if not pd.api.types.is_float_dtype(df[col]):
            raise TypeError(f"Coluna {col} tem tipo inválido: {df[col].dtype}")
        
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            df[col] = df[col].fillna(global_mean)
            print(f"Preenchidos {nan_count} NaNs na coluna {col} com média global")

    return df
