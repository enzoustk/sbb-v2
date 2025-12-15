from datetime import datetime
####
import pandas as pd
import numpy as np
from collections import deque
from sklearn.preprocessing import StandardScaler
from typing import Tuple

def input_h2h_features(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    short_window: int = 5,
    long_window: int = 50,
    flag_threshold: float = 1.0,
    return_scaler: bool = False,
    drop_h2h: int = 0
) -> Tuple[pd.DataFrame, pd.DataFrame] | Tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Calcula features baseadas em confrontos diretos (H2H):

      - Média dos gols totais nos últimos `long_window` confrontos (avg_h2h_long)
      - Mediana dos gols totais nos últimos `long_window` confrontos (median_h2h_long)
      - Média dos gols totais nos últimos `short_window` confrontos (avg_h2h_short)

      - Flags baseadas nos últimos `short_window` confrontos comparados à média/desvio
        dos últimos `long_window` confrontos:
          - flag_below_long
          - flag_above_long
          - flag_below_long_1std
          - flag_above_long_1std

      - Flags baseadas nos últimos `short_window` confrontos comparados à mediana
        dos últimos `long_window` confrontos:
          - flag_below_median
          - flag_above_median

      - Flag de consistência de resultado:
          - flag_same_result

    Parâmetros
    ----------
    short_window : int
        Quantidade de confrontos recentes para média curta.
    long_window : int
        Quantidade de confrontos para média longa.
    flag_threshold : float
        Proporção mínima (0.0–1.0) de jogos nos últimos `short_window`
        que precisam atender à condição para marcar a flag.
        Exemplo: 1.0 = 100%, 0.6 = 60%.
    drop_h2h : int
        Valor mínimo de confrontos diretos necessários.
        Linhas com `h2h_count < drop_h2h` serão removidas.
    """

    def compute_h2h_stats(df: pd.DataFrame, history_h2h: dict):
        avg_long, median_long, avg_short = [], [], []
        h2h_count = []
        flags = {
            "flag_below_long": [],
            "flag_above_long": [],
            "flag_same_result": [],
            "flag_below_long_1std": [],
            "flag_above_long_1std": [],
            "flag_below_median": [],
            "flag_above_median": [],
        }

        for _, row in df.iterrows():
            h, a = row["home_player"], row["away_player"]
            hs, as_ = row["home_score"], row["away_score"]
            total = hs + as_
            result = "D" if hs == as_ else ("H" if hs > as_ else "A")

            key_h2h = tuple(sorted([h, a]))
            if key_h2h not in history_h2h:
                history_h2h[key_h2h] = deque(maxlen=max(short_window, long_window))

            past_h2h = [val for _, val, _ in history_h2h[key_h2h]]

            # médias e mediana
            avg_long.append(np.mean(past_h2h[-long_window:]) if past_h2h else np.nan)
            median_long.append(np.median(past_h2h[-long_window:]) if past_h2h else np.nan)
            avg_short.append(np.mean(past_h2h[-short_window:]) if past_h2h else np.nan)
            h2h_count.append(len(past_h2h))

            # calcular flags
            if len(past_h2h) >= short_window:
                last_short = past_h2h[-short_window:]
                mean_long = np.mean(past_h2h[-long_window:])
                med_long = np.median(past_h2h[-long_window:])
                std_long = np.std(past_h2h[-long_window:]) if len(past_h2h) > 1 else 0

                # proporções
                prop_below = np.mean([s < mean_long for s in last_short])
                prop_above = np.mean([s > mean_long for s in last_short])
                prop_below_std = np.mean([s < mean_long - std_long for s in last_short])
                prop_above_std = np.mean([s > mean_long + std_long for s in last_short])
                prop_below_med = np.mean([s < med_long for s in last_short])
                prop_above_med = np.mean([s > med_long for s in last_short])

                flags["flag_below_long"].append(int(prop_below >= flag_threshold))
                flags["flag_above_long"].append(int(prop_above >= flag_threshold))
                flags["flag_below_long_1std"].append(int(prop_below_std >= flag_threshold))
                flags["flag_above_long_1std"].append(int(prop_above_std >= flag_threshold))
                flags["flag_below_median"].append(int(prop_below_med >= flag_threshold))
                flags["flag_above_median"].append(int(prop_above_med >= flag_threshold))

                last_results = [res for _, _, res in history_h2h[key_h2h]][-short_window:]
                most_common_ratio = max(np.mean([r == label for r in last_results]) for label in set(last_results))
                flags["flag_same_result"].append(int(most_common_ratio >= flag_threshold))
            else:
                for k in flags:
                    flags[k].append(0)

            # atualizar histórico
            history_h2h[key_h2h].append((row["date"], total, result))

        df = df.copy()
        df["avg_h2h_long"] = avg_long
        df["median_h2h_long"] = median_long
        df["avg_h2h_short"] = avg_short
        df["h2h_count"] = h2h_count
        for col, values in flags.items():
            df[col] = values

        # filtrar linhas inválidas
        df = df.dropna(subset=["avg_h2h_long", "median_h2h_long", "avg_h2h_short"]).copy()
        if drop_h2h > 0:
            df = df[df["h2h_count"] >= drop_h2h].copy()

        return df, history_h2h

    history_h2h = {}

    train_with_h2h, history_h2h = compute_h2h_stats(train_df, history_h2h)
    test_with_h2h, _ = compute_h2h_stats(test_df, history_h2h)

    # escalar apenas médias/mediana e contagem
    scaler = StandardScaler()
    cols = ["avg_h2h_long", "median_h2h_long", "avg_h2h_short", "h2h_count"]

    train_with_h2h[cols] = scaler.fit_transform(train_with_h2h[cols])
    test_with_h2h[cols] = scaler.transform(test_with_h2h[cols])

    if return_scaler:
        return train_with_h2h, test_with_h2h, scaler
    else:
        return train_with_h2h, test_with_h2h



def split_data(
    split_date: datetime,
    date_column: str,
    df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide os dados em treino e teste a partir de uma data
    """
    df = df.copy()
    mask = df[date_column] >= split_date
    return df[~mask], df[mask]
