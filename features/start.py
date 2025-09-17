import pandas as pd
import numpy as np
from object.bet import Bet
from collections import deque
from data import load



def initialize_player_data(history: dict = {"player": {}, "h2h": {}}) -> tuple[pd.DataFrame, dict]:
    """
    Percorre o dataframe de partidas e gera o 'history' -> dict com os dados de cada player
    """
    
    ma_player, std_player = [], []
    ma_h2h, std_h2h = [], []

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

        # ---- atualizar histórico ----
        history["player"][h].append(hs)
        history["player"][a].append(as_)
        history["h2h"][key_h2h].append(hs + as_)

    df = df.copy()
    # atenção: como temos duas entradas (h e a), é melhor separar colunas
    df["ma_home"], df["std_home"] = ma_player[0::2], std_player[0::2]
    df["ma_away"], df["std_away"] = ma_player[1::2], std_player[1::2]
    df["ma_h2h"], df["std_h2h"] = ma_h2h, std_h2h

    df = df.dropna(
        subset=["ma_home", "ma_away", "ma_h2h",
                "std_home", "std_away", "std_h2h"]
    ).copy()

    return history

def update(event: Bet, history: dict) -> dict:
    """
    Atualiza o histórico com os dados de um novo evento (partida).

    Args:
        event (Bet): objeto contendo as informações da partida
                     -> event.home_player, event.away_player,
                        event.home_score, event.away_score
        history (dict): dicionário de históricos com deques
    
    Returns:
        dict: histórico atualizado
    """
    h, a = event.home_player.lower(), event.away_player.lower()
    hs, as_ = event.home_score, event.away_score

    # inicializar histórico do jogador se necessário
    for pid in [h, a]:
        if pid not in history["player"]:
            history["player"][pid] = deque(maxlen=50)

    # inicializar histórico de confrontos
    key_h2h = tuple(sorted([h, a]))
    if key_h2h not in history["h2h"]:
        history["h2h"][key_h2h] = deque(maxlen=50)

    # atualizar histórico
    history["player"][h].append(hs)
    history["player"][a].append(as_)
    history["h2h"][key_h2h].append(hs + as_)

def get_features(event: Bet, history: dict) -> pd.DataFrame:
    """
    Calcula as features de um evento (partida) com base no histórico atual,
    sem atualizar os deques.

    Args:
        event (Bet): objeto contendo as informações da partida
        history (dict): histórico de jogadores e confrontos

    Returns:
        pd.DataFrame: DataFrame com as features:
            [ma_home, std_home, ma_away, std_away, ma_h2h, std_h2h]
    """
    h, a = event.home_player.lower(), event.away_player.lower()

    # inicializar se ainda não existir (para evitar KeyError)
    for pid in [h, a]:
        if pid not in history["player"]:
            history["player"][pid] = deque(maxlen=50)

    key_h2h = tuple(sorted([h, a]))
    if key_h2h not in history["h2h"]:
        history["h2h"][key_h2h] = deque(maxlen=50)

    # calcular médias e desvios
    ma_home = np.mean(history["player"][h]) if history["player"][h] else np.nan
    std_home = np.std(history["player"][h]) if history["player"][h] else np.nan

    ma_away = np.mean(history["player"][a]) if history["player"][a] else np.nan
    std_away = np.std(history["player"][a]) if history["player"][a] else np.nan

    ma_h2h = np.mean(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan
    std_h2h = np.std(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan

    # cria DataFrame com nomes de colunas
    features = pd.DataFrame([[
        ma_home, std_home,
        ma_away, std_away,
        ma_h2h, std_h2h
        ]], columns=[
        "ma_home", "std_home",
        "ma_away", "std_away",
        "ma_h2h", "std_h2h"
        ])

    return features

    
