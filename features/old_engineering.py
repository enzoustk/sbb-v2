import pandas as pd
import numpy as np
import logging
from datetime import datetime
from utils.constants import FILE_PATH_CONFRONTOS_IDX, FILE_PATH_JOGADORES_IDX, FILE_PATH_TIMES_IDX, FILE_PATH_INDICES_FEATURES

def calcular_features(df, include_current_game=False, save_indices=False):
    # Carregar índices de jogadores e times
    jogador_df = pd.read_csv(FILE_PATH_JOGADORES_IDX)
    time_df = pd.read_csv(FILE_PATH_TIMES_IDX)

    jogador_index = dict(zip(jogador_df['jogador'], jogador_df['idx_jogador']))
    time_index = dict(zip(time_df['time'], time_df['idx_time']))

    df = df.copy()

    df['idx_jogador_casa'] = df['jogador_casa'].map(jogador_index)
    df['idx_jogador_fora'] = df['jogador_fora'].map(jogador_index)
    df['idx_time_casa'] = df['time_casa'].map(time_index)
    df['idx_time_fora'] = df['time_fora'].map(time_index)

    df['confronto_key'] = df.apply(lambda row: tuple(sorted([row['idx_jogador_casa'], row['idx_jogador_fora']])), axis=1)
    df['confronto_idx'] = df['confronto_key'].apply(lambda x: hash(x))
    df['h2h_count'] = df.groupby('confronto_key').cumcount()

    if include_current_game:
        df['l1'] = df.groupby('confronto_key')['gols_totais'].shift(0)
        df['l2'] = df.groupby('confronto_key')['gols_totais'].shift(1)
        df['l3'] = df.groupby('confronto_key')['gols_totais'].shift(2)
    else:
        df['l1'] = df.groupby('confronto_key')['gols_totais'].shift(1)
        df['l2'] = df.groupby('confronto_key')['gols_totais'].shift(2)
        df['l3'] = df.groupby('confronto_key')['gols_totais'].shift(3)

    df['mediana_3'] = df[['l1', 'l2', 'l3']].median(axis=1)
    df['std_3'] = df[['l1', 'l2', 'l3']].std(axis=1, ddof=1)
    df['media_3'] = df[['l1', 'l2', 'l3']].mean(axis=1)
    df['moda_3'] = df[['l1', 'l2', 'l3']].apply(lambda row: row.mode().iloc[0] if not row.mode().empty else np.nan, axis=1)

    if include_current_game:
        df['mediana_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.expanding().median())
        df['std_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.expanding().std(ddof=1))
        df['media_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.expanding().mean())
        df['moda_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.expanding().apply(lambda s: s.mode().iloc[0] if not s.mode().empty else np.nan))
        df['ewma_total_15'] = df.groupby('confronto_key')['gols_totais'].transform(
            lambda x: x.ewm(span=max(1, int(len(x) * 0.15)), adjust=False).mean())
        df['ewma_total_3'] = df.groupby('confronto_key')['gols_totais'].transform(
            lambda x: x.ewm(span=max(1, int(len(x) * 0.03)), adjust=False).mean())
    else:
        df['mediana_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.shift().expanding().median())
        df['std_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.shift().expanding().std(ddof=1))
        df['media_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.shift().expanding().mean())
        df['moda_total'] = df.groupby('confronto_key')['gols_totais'].transform(lambda x: x.shift().expanding().apply(lambda s: s.mode().iloc[0] if not s.mode().empty else np.nan))
        df['ewma_total_15'] = df.groupby('confronto_key')['gols_totais'].transform(
            lambda x: x.shift().ewm(span=max(1, int(len(x) * 0.15)), adjust=False).mean())
        df['ewma_total_3'] = df.groupby('confronto_key')['gols_totais'].transform(
            lambda x: x.shift().ewm(span=max(1, int(len(x) * 0.03)), adjust=False).mean())

    primeira_partida = df['data'].min()
    df['tempo_dia_zero'] = (df['data'] - primeira_partida).dt.days

    df['day_of_week'] = df['data'].dt.weekday
    df['hour_of_day'] = df['data'].dt.hour
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    df['hour_sin'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)

    if save_indices:
        indices_df = df[['confronto_id', 'idx_jogador_casa', 'idx_jogador_fora', 'idx_time_casa', 'idx_time_fora']].drop_duplicates()
        indices_df.to_excel(FILE_PATH_INDICES_FEATURES, index=False)

    return df

def calcular_features_treinamento(df):
    return calcular_features(df, include_current_game=False, save_indices=True)

def calcular_features_ao_vivo(
    jogador_casa,
    jogador_fora,
    time_casa,
    time_fora,
    df_dados
):
    """
    Calcula as features ao vivo utilizando o DataFrame df_dados,
    que deve ser carregado previamente (do CSV ou outro local).
    """

    # Carrega índices de jogadores e times
    jogador_df = pd.read_csv(FILE_PATH_JOGADORES_IDX)
    time_df = pd.read_csv(FILE_PATH_TIMES_IDX)

    jogador_index = dict(zip(jogador_df['jogador'], jogador_df['idx_jogador']))
    time_index = dict(zip(time_df['time'], time_df['idx_time']))

    jogador_casa_id = jogador_index.get(jogador_casa.lower())
    jogador_fora_id = jogador_index.get(jogador_fora.lower())
    time_casa_id = time_index.get(time_casa.lower())
    time_fora_id = time_index.get(time_fora.lower())

    if None in [jogador_casa_id, jogador_fora_id, time_casa_id, time_fora_id]:
        logging.error(
            f"IDs não encontrados para {jogador_casa}/{time_casa} ou "
            f"{jogador_fora}/{time_fora}."
        )
        return None

    # Cria/atualiza a coluna 'confronto_key' no df_dados
    df_dados['confronto_key'] = df_dados.apply(
        lambda row: tuple(sorted([row['idx_jogador_casa'], row['idx_jogador_fora']])),
        axis=1
    )

    # Filtra para encontrar somente os confrontos entre jogador_casa/jogador_fora
    confronto_df = df_dados[
        (
            (df_dados['idx_jogador_fora'] == jogador_fora_id) &
            (df_dados['idx_jogador_casa'] == jogador_casa_id)
        )
        |
        (
            (df_dados['idx_jogador_fora'] == jogador_casa_id) &
            (df_dados['idx_jogador_casa'] == jogador_fora_id)
        )
    ].copy()

    # Calcula features do histórico
    confronto_df = calcular_features(confronto_df, include_current_game=True)

    # Calcula tempo relativo desde a primeira partida do dataset
    primeira_partida = df_dados['data'].min()
    confronto_df['tempo_dia_zero'] = (confronto_df['data'] - primeira_partida).dt.days

    # Adiciona informações de data/hora do momento atual
    agora = datetime.now()
    confronto_df['day_of_week'] = agora.weekday()
    confronto_df['hour_of_day'] = agora.hour
    confronto_df['day_sin'] = np.sin(2 * np.pi * confronto_df['day_of_week'] / 7)
    confronto_df['day_cos'] = np.cos(2 * np.pi * confronto_df['day_of_week'] / 7)
    confronto_df['hour_sin'] = np.sin(2 * np.pi * confronto_df['hour_of_day'] / 24)
    confronto_df['hour_cos'] = np.cos(2 * np.pi * confronto_df['hour_of_day'] / 24)

    if confronto_df.empty:
        logging.warning("Nenhum dado relevante encontrado no confronto_df.")
        return None

    # Retorna apenas as features do último confronto (linha mais recente)
    ultimo_confronto = confronto_df.iloc[-1]
    return ultimo_confronto.to_dict()