import pandas as pd
import numpy as np
from object.bet import Bet
from collections import deque
from data import load


def initialize_player_data(
    history: dict = {"player": {}, "h2h": {}},
    drop_h2h: int = 0
) -> dict:
    """
    Percorre o dataframe de partidas e gera o 'history' -> dict com os dados de cada player.

    Args:
        history (dict): dicionário inicial de históricos.
        drop_h2h (int): valor mínimo de confrontos diretos necessários.
                        Linhas com h2h_count < drop_h2h serão descartadas.
    
    Returns:
        dict: histórico atualizado.
    """
    
    ma_player, std_player = [], []
    ma_h2h, std_h2h = [], []
    h2h_count = []

    raw_data = load.data(file='historic')
    df = raw_data['22614']

    for _, row in df.iterrows():
        h, a = row["home_player"].lower(), row["away_player"].lower()
        hs, as_ = row["home_score"], row["away_score"]

        # inicializar histórico do jogador se necessário
        for pid in [h, a]:
            if pid not in history["player"]:
                history["player"][pid] = deque(maxlen=50)

        # inicializar histórico de confrontos
        key_h2h = tuple(sorted([h, a]))
        if key_h2h not in history["h2h"]:
            history["h2h"][key_h2h] = deque(maxlen=50)

        # ---- calcular features antes de atualizar ----
        # jogador mandante
        ma_player.append(np.mean(history["player"][h]) if history["player"][h] else np.nan)
        std_player.append(np.std(history["player"][h]) if history["player"][h] else np.nan)

        # jogador visitante
        ma_player.append(np.mean(history["player"][a]) if history["player"][a] else np.nan)
        std_player.append(np.std(history["player"][a]) if history["player"][a] else np.nan)

        # head-to-head
        ma_h2h.append(np.mean(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan)
        std_h2h.append(np.std(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan)

        # contagem de confrontos diretos
        h2h_count.append(len(history["h2h"][key_h2h]))

        # ---- atualizar histórico ----
        history["player"][h].append(hs)
        history["player"][a].append(as_)
        history["h2h"][key_h2h].append(hs + as_)

    df = df.copy()
    df["ma_home"], df["std_home"] = ma_player[0::2], std_player[0::2]
    df["ma_away"], df["std_away"] = ma_player[1::2], std_player[1::2]
    df["ma_h2h"], df["std_h2h"] = ma_h2h, std_h2h
    df["h2h_count"] = h2h_count

    # drop linhas inválidas
    df = df.dropna(
        subset=["ma_home", "ma_away", "ma_h2h",
                "std_home", "std_away", "std_h2h"]
    ).copy()

    if drop_h2h > 0:
        df = df[df["h2h_count"] >= drop_h2h].copy()

    return history


def update(event: Bet, history: dict) -> dict:
    """
    Atualiza o histórico com os dados de um novo evento (partida).
    """
    h, a = event.home_player.lower(), event.away_player.lower()
    hs, as_ = event.home_score, event.away_score

    for pid in [h, a]:
        if pid not in history["player"]:
            history["player"][pid] = deque(maxlen=50)

    key_h2h = tuple(sorted([h, a]))
    if key_h2h not in history["h2h"]:
        history["h2h"][key_h2h] = deque(maxlen=50)

    history["player"][h].append(hs)
    history["player"][a].append(as_)
    history["h2h"][key_h2h].append(hs + as_)

    return history


def get_features(event: Bet, history: dict, drop_h2h: int = 0) -> pd.DataFrame:
    """
    Calcula as features de um evento (partida) com base no histórico atual,
    sem atualizar os deques.

    Args:
        event (Bet): objeto contendo as informações da partida
        history (dict): histórico de jogadores e confrontos
        drop_h2h (int): valor mínimo de confrontos diretos necessários.
                        Se h2h_count < drop_h2h, retorna DataFrame vazio.

    Returns:
        pd.DataFrame: com colunas
            [ma_home, std_home, ma_away, std_away, ma_h2h, std_h2h, h2h_count]
    """
    h, a = event.home_player.lower(), event.away_player.lower()

    for pid in [h, a]:
        if pid not in history["player"]:
            history["player"][pid] = deque(maxlen=50)

    key_h2h = tuple(sorted([h, a]))
    if key_h2h not in history["h2h"]:
        history["h2h"][key_h2h] = deque(maxlen=50)

    # calcular features
    ma_home = np.mean(history["player"][h]) if history["player"][h] else np.nan
    std_home = np.std(history["player"][h]) if history["player"][h] else np.nan

    ma_away = np.mean(history["player"][a]) if history["player"][a] else np.nan
    std_away = np.std(history["player"][a]) if history["player"][a] else np.nan

    ma_h2h = np.mean(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan
    std_h2h = np.std(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan

    h2h_count = len(history["h2h"][key_h2h])

    features = pd.DataFrame([[
        ma_home, std_home,
        ma_away, std_away,
        ma_h2h, std_h2h,
        h2h_count
        ]], columns=[
        "ma_home", "std_home",
        "ma_away", "std_away",
        "ma_h2h", "std_h2h",
        "h2h_count"
        ])

    # aplicar filtro de drop_h2h
    if drop_h2h > 0 and h2h_count < drop_h2h:
        return pd.DataFrame(columns=features.columns)

    return features


    
