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
    test_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcula médias e desvios padrão (até 50 jogos) para:
      1. Gols marcados pelo jogador quando atua como mandante
      2. Gols marcados pelo jogador quando atua como visitante
      3. Gols em confrontos diretos mandante vs visitante (ignora ordem casa/fora)
    
    Para cada métrica, retorna também o desvio padrão.

    Retorna:
        (train_df_com_covariáveis, test_df_com_covariáveis)
    """

    def compute_rolling_stats(df: pd.DataFrame, history: dict) -> tuple[pd.DataFrame, dict]:
        ma_home, std_home = [], []
        ma_away, std_away = [], []
        ma_h2h, std_h2h = [], []

        for _, row in df.iterrows():
            h, a = row["home_player"], row["away_player"]
            hs, as_ = row["home_score"], row["away_score"]

            # Inicializar histórico se necessário
            for pid in [h, a]:
                if pid not in history["home"]:
                    history["home"][pid] = deque(maxlen=50)
                if pid not in history["away"]:
                    history["away"][pid] = deque(maxlen=50)
            key_h2h = tuple(sorted([h, a]))
            if key_h2h not in history["h2h"]:
                history["h2h"][key_h2h] = deque(maxlen=50)

            # ---- Calcular features antes de atualizar ----
            # 1. jogador mandante
            ma_home.append(np.mean(history["home"][h]) if history["home"][h] else np.nan)
            std_home.append(np.std(history["home"][h]) if history["home"][h] else np.nan)

            # 2. jogador visitante
            ma_away.append(np.mean(history["away"][a]) if history["away"][a] else np.nan)
            std_away.append(np.std(history["away"][a]) if history["away"][a] else np.nan)

            # 3. head-to-head
            ma_h2h.append(np.mean(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan)
            std_h2h.append(np.std(history["h2h"][key_h2h]) if history["h2h"][key_h2h] else np.nan)

            # ---- Atualizar histórico ----
            history["home"][h].append(hs)
            history["away"][a].append(as_)
            history["h2h"][key_h2h].append(hs + as_)  # total de gols do confronto

        df = df.copy()
        df["ma_home"], df["std_home"] = ma_home, std_home
        df["ma_away"], df["std_away"] = ma_away, std_away
        df["ma_h2h"], df["std_h2h"] = ma_h2h, std_h2h

        df = df.dropna(
            subset=["ma_home", "ma_away", "ma_h2h",
                    "std_home", "std_away", "std_h2h"]
        ).copy()

        return df, history

    # Estrutura do histórico
    history = {"home": {}, "away": {}, "h2h": {}}

    # 1) Calcular no treino
    train_with_avg, history = compute_rolling_stats(train_df, history)

    # 2) Continuar no teste
    test_with_avg, _ = compute_rolling_stats(test_df, history)

    # 3) Escalar (fit no train, transform no test)
    scaler = StandardScaler()
    cols = ["ma_home", "std_home",
            "ma_away", "std_away",
            "ma_h2h", "std_h2h"]

    train_with_avg[cols] = scaler.fit_transform(train_with_avg[cols])
    test_with_avg[cols] = scaler.transform(test_with_avg[cols])

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
