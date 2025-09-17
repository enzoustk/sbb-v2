import numpy as np
import pandas as pd
from datetime import datetime
from collections import deque
from sklearn.preprocessing import StandardScaler

import pandas as pd
import numpy as np
from collections import deque
from sklearn.preprocessing import StandardScaler

def input_averages(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    return_scaler: bool = False
) -> tuple[pd.DataFrame, pd.DataFrame] | tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Calcula médias e desvios padrão (até 50 jogos) para:
      1. Gols marcados pelo jogador (independente de casa/fora)
      2. Gols em confrontos diretos (ignora ordem casa/fora)
    """

    def compute_rolling_stats(df: pd.DataFrame, history: dict) -> tuple[pd.DataFrame, dict]:
        ma_player, std_player = [], []
        ma_h2h, std_h2h = [], []

        for _, row in df.iterrows():
            h, a = row["home_player"], row["away_player"]
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

        return df, history

    # histórico único por jogador
    history = {"player": {}, "h2h": {}}

    # treino
    train_with_avg, history = compute_rolling_stats(train_df, history)
    # teste
    test_with_avg, _ = compute_rolling_stats(test_df, history)

    # escalar
    scaler = StandardScaler()
    cols = ["ma_home", "std_home",
            "ma_away", "std_away",
            "ma_h2h", "std_h2h"]

    train_with_avg[cols] = scaler.fit_transform(train_with_avg[cols])
    test_with_avg[cols] = scaler.transform(test_with_avg[cols])

    if return_scaler:
        return train_with_avg, test_with_avg, scaler
    else:
        return train_with_avg, test_with_avg



def split_data(
    split_date: datetime,
    date_column: str,
    df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide os dados e retorna treino, teste
    """
    df = df.copy()
    mask = df[date_column] >= split_date

    
    return df[~mask], df[mask]
