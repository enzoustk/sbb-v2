import numpy as np
import pandas as pd
from datetime import datetime,timedelta
from collections import deque
from sklearn.preprocessing import StandardScaler

def input_h2h_features(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    return_scaler: bool = False,
    drop_h2h: int = 0
) -> tuple[pd.DataFrame, pd.DataFrame] | tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Calcula features baseadas em confrontos diretos (H2H) e histórico individual de jogadores,
    removendo partidas ocorridas em até 1h antes do evento:
      - Média dos gols totais do confronto (avg_h2h)
      - Mediana dos gols totais do confronto (median_h2h)
      - Lags de 1 até 20 confrontos anteriores (lag_1 ... lag_20)
      - Quantidade de confrontos já disputados (h2h_count)
      - Média de gols do jogador mandante (avg_home_player)
      - Média de gols do jogador visitante (avg_away_player)

    Parâmetros
    ----------
    drop_h2h : int
        Valor mínimo de confrontos diretos necessários.
        Linhas com `h2h_count < drop_h2h` serão removidas.
    """

    def compute_h2h_stats(df: pd.DataFrame, history_h2h: dict, history_player: dict):
        avg_h2h, median_h2h = [], []
        avg_home_player, avg_away_player = [], []
        lags = {f"lag_{i}": [] for i in range(1, 21)}
        h2h_count = []

        for _, row in df.iterrows():
            h, a = row["home_player"], row["away_player"]
            hs, as_ = row["home_score"], row["away_score"]
            t = pd.to_datetime(row["date"])

            # inicializar históricos
            key_h2h = tuple(sorted([h, a]))
            if key_h2h not in history_h2h:
                history_h2h[key_h2h] = deque(maxlen=50)
            for pid in [h, a]:
                if pid not in history_player:
                    history_player[pid] = deque(maxlen=50)

            # --- filtrar histórico com janela de 1h ---
            cutoff = t - timedelta(hours=1)
            history_h2h[key_h2h] = deque(
                [(ts, val) for ts, val in history_h2h[key_h2h] if ts < cutoff],
                maxlen=50
            )
            history_player[h] = deque(
                [(ts, val) for ts, val in history_player[h] if ts < cutoff],
                maxlen=50
            )
            history_player[a] = deque(
                [(ts, val) for ts, val in history_player[a] if ts < cutoff],
                maxlen=50
            )

            # ---- calcular features H2H ----
            past_h2h = [val for ts, val in history_h2h[key_h2h]]
            avg_h2h.append(np.mean(past_h2h) if past_h2h else np.nan)
            median_h2h.append(np.median(past_h2h) if past_h2h else np.nan)
            h2h_count.append(len(past_h2h))
            for i in range(1, 21):
                lags[f"lag_{i}"].append(
                    past_h2h[-i] if len(past_h2h) >= i else np.nan
                )

            # ---- calcular features individuais ----
            past_h = [val for ts, val in history_player[h]]
            past_a = [val for ts, val in history_player[a]]
            avg_home_player.append(np.mean(past_h) if past_h else np.nan)
            avg_away_player.append(np.mean(past_a) if past_a else np.nan)

            # ---- atualizar históricos ----
            history_h2h[key_h2h].append((t, hs + as_))
            history_player[h].append((t, hs))
            history_player[a].append((t, as_))

        df = df.copy()
        df["avg_h2h"] = avg_h2h
        df["median_h2h"] = median_h2h
        df["h2h_count"] = h2h_count
        df["avg_home_player"] = avg_home_player
        df["avg_away_player"] = avg_away_player
        for col, values in lags.items():
            df[col] = values

        # filtrar linhas inválidas
        df = df.dropna(
            subset=["avg_h2h", "median_h2h", "avg_home_player", "avg_away_player"]
        ).copy()
        if drop_h2h > 0:
            df = df[df["h2h_count"] >= drop_h2h].copy()

        return df, history_h2h, history_player

    history_h2h, history_player = {}, {}

    train_with_h2h, history_h2h, history_player = compute_h2h_stats(train_df, history_h2h, history_player)
    test_with_h2h, _, _ = compute_h2h_stats(test_df, history_h2h, history_player)

    # escalar avg, median, h2h_count e médias dos jogadores
    scaler = StandardScaler()
    cols = ["avg_h2h", "median_h2h", "h2h_count", "avg_home_player", "avg_away_player"]

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
