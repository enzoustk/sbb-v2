import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from scipy.optimize import minimize

@dataclass
class EloParams:
    s: float = 400.0     # escala Elo
    K: float = 20.0      # passo de atualização do rating
    h: float = 60.0      # mando de campo em pontos Elo
    nu: float = 0.40     # parâmetro de empate (Davidson)
    R0: float = 1500.0   # rating inicial
    lr_h: float = 0.0    # taxa online p/ drift de h
    lr_nu: float = 0.0   # taxa online p/ drift de nu
    reg_to_mean: float = 0.0  # regressão à média por jogo (0 = sem)

class EloDavidsonModel:
    """
    Elo + Davidson (1X2). Treina h, nu (e opcionalmente K) offline em 1/3,
    depois avalia online no restante com atualização de ratings e drift opcional.
    """
    def __init__(self, params: Optional[EloParams] = None, tune_K: bool = False):
        self.params = params or EloParams()
        self.tune_K = tune_K
        self.ratings: Dict[str, float] = {}
        self.eps = 1e-12

    # ---------- Utilidades ----------
    def _get_rating(self, team: str) -> float:
        if team not in self.ratings:
            self.ratings[team] = self.params.R0
        return self.ratings[team]

    def _set_rating(self, team: str, value: float):
        self.ratings[team] = value

    def _to_outcome(self, row) -> str:
        if 'outcome' in row and pd.notna(row['outcome']):
            return row['outcome']
        # Deduz do placar
        for hcol, acol in [('home_goals','away_goals'), ('home_score','away_score')]:
            if hcol in row and acol in row and pd.notna(row[hcol]) and pd.notna(row[acol]):
                if row[hcol] > row[acol]: return 'H'
                if row[hcol] < row[acol]: return 'A'
                return 'D'
        raise ValueError("Não encontrei 'outcome' nem colunas de placar na linha.")

    # Probabilidades 1X2 (forma “r” evita overflow)
    def _three_way_probs(self, Rh: float, Ra: float, h: float, s: float, nu: float) -> Tuple[float,float,float,float,float]:
        r = 10 ** ((Rh + h - Ra) / (2.0 * s))
        D = r + 1.0/r + 2.0*nu
        pH = r / D
        pD = (2.0*nu) / D
        pA = (1.0/r) / D
        return pH, pD, pA, r, D

    def _score_from_outcome(self, y: str) -> float:
        return 1.0 if y=='H' else (0.5 if y=='D' else 0.0)

    def _logloss(self, pH, pD, pA, y: str) -> float:
        p = pH if y=='H' else (pD if y=='D' else pA)
        return -np.log(max(p, self.eps))

    # Gradientes de log p(y) para drift online de h e nu
    def _grads_logp(self, outcome: str, r: float, D: float, s: float, nu: float) -> Tuple[float,float]:
        """
        Retorna (d log p / d h, d log p / d nu)
        c = ln(10)/(2s)
        """
        c = np.log(10.0)/(2.0*s)
        # dD/dh = c*(r - 1/r)
        dD_dh = c*(r - 1.0/r)

        if outcome == 'H':
            # d log pH / dh = c - (1/D)*dD/dh
            dlogp_dh = c - (dD_dh / D)
            # d log pH / dnu = - (2 / D)
            dlogp_dnu = -(2.0 / D)
        elif outcome == 'D':
            # d log pD / dh = - (1/D) * dD/dh
            dlogp_dh = - (dD_dh / D)
            # d log pD / dnu = 1/nu - (2 / D)
            dlogp_dnu = (1.0/max(nu, self.eps)) - (2.0 / D)
        else:  # 'A'
            # d log pA / dh = -c - (1/D)*dD/dh
            dlogp_dh = -c - (dD_dh / D)
            # d log pA / dnu = - (2 / D)
            dlogp_dnu = -(2.0 / D)

        return dlogp_dh, dlogp_dnu

    # Atualização de ratings + drift (opcional)
    def _update_after_game(self, home: str, away: str, outcome: str):
        Rh = self._get_rating(home)
        Ra = self._get_rating(away)
        pH, pD, pA, r, D = self._three_way_probs(Rh, Ra, self.params.h, self.params.s, self.params.nu)
        Eh = pH + 0.5*pD
        Sh = self._score_from_outcome(outcome)

        # Elo update (simétrico)
        delta = self.params.K * (Sh - Eh)
        Rh_new = Rh + delta
        Ra_new = Ra - delta

        # Regressão à média (opcional, suave por jogo)
        if self.params.reg_to_mean > 0.0:
            a = self.params.reg_to_mean
            Rh_new = (1-a)*Rh_new + a*self.params.R0
            Ra_new = (1-a)*Ra_new + a*self.params.R0

        self._set_rating(home, Rh_new)
        self._set_rating(away, Ra_new)

        # Drift de hiperparâmetros (SGD em -log p)
        if (self.params.lr_h > 0.0) or (self.params.lr_nu > 0.0):
            dlogp_dh, dlogp_dnu = self._grads_logp(outcome, r, D, self.params.s, self.params.nu)
            # L = -log p  ⇒ ∂L/∂θ = -∂logp/∂θ
            self.params.h  = self.params.h  - self.params.lr_h  * (-dlogp_dh)
            self.params.nu = max(1e-6, self.params.nu - self.params.lr_nu * (-dlogp_dnu))

        return pH, pD, pA

    # ---------- Treino offline (calibração de h, nu, K opcional) ----------
    def _simulate_logloss(self, df: pd.DataFrame, h: float, nu: float, K: float) -> float:
        # simula passando pelo treino, atualizando ratings e acumulando log-loss
        saved = (self.ratings.copy(), self.params.h, self.params.nu, self.params.K)
        self.ratings = {}
        self.params.h, self.params.nu, self.params.K = h, max(nu, 1e-6), K

        total_ll = 0.0
        for _, row in df.iterrows():
            home, away = str(row['home']), str(row['away'])
            y = self._to_outcome(row)
            Rh, Ra = self._get_rating(home), self._get_rating(away)
            pH, pD, pA, _, _ = self._three_way_probs(Rh, Ra, self.params.h, self.params.s, self.params.nu)
            total_ll += self._logloss(pH, pD, pA, y)
            # atualiza ratings (sem drift na calibração offline)
            Eh = pH + 0.5*pD
            Sh = self._score_from_outcome(y)
            delta = self.params.K * (Sh - Eh)
            self._set_rating(home, Rh + delta)
            self._set_rating(away, Ra - delta)

        # restore
        self.ratings, self.params.h, self.params.nu, self.params.K = saved
        return total_ll / max(1, len(df))

    def fit_offline(self, df_train: pd.DataFrame):
        # Ordem cronológica se houver 'date'
        if 'date' in df_train.columns:
            df_train = df_train.sort_values('date')
        # Objetivo: minimizar log-loss médio no treino
        x0 = np.array([self.params.h, np.log(self.params.nu), np.log(self.params.K)])
        bounds = [(-200, 200), (np.log(1e-6), np.log(5.0)), (np.log(5.0), np.log(80.0))]

        if not self.tune_K:
            # congela K: remove do vetor
            x0 = np.array([self.params.h, np.log(self.params.nu)])
            bounds = [(-200, 200), (np.log(1e-6), np.log(5.0))]

        def obj(x):
            if self.tune_K:
                h, ln_nu, ln_K = x
                K = float(np.exp(ln_K))
            else:
                h, ln_nu = x
                K = self.params.K
            nu = float(np.exp(ln_nu))
            return self._simulate_logloss(df_train, h, nu, K)

        res = minimize(obj, x0, method='L-BFGS-B', bounds=bounds, options={'maxiter': 200})
        if not res.success:
            print("[Aviso] Otimização não convergiu:", res.message)

        if self.tune_K:
            h, ln_nu, ln_K = res.x
            self.params.h = float(h)
            self.params.nu = float(np.exp(ln_nu))
            self.params.K  = float(np.exp(ln_K))
        else:
            h, ln_nu = res.x
            self.params.h = float(h)
            self.params.nu = float(np.exp(ln_nu))

    # ---------- Avaliação online ----------
    def evaluate_online(self, df_test: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        if 'date' in df_test.columns:
            df_test = df_test.sort_values('date')

        self.ratings = {}  # recomeça com R0 no início do teste
        rows = []
        correct = 0
        cum_ll = 0.0

        for i, row in df_test.iterrows():
            home, away = str(row['home']), str(row['away'])
            y = self._to_outcome(row)

            Rh = self._get_rating(home)
            Ra = self._get_rating(away)
            pH, pD, pA, _, _ = self._three_way_probs(Rh, Ra, self.params.h, self.params.s, self.params.nu)
            y_pred = ['H','D','A'][int(np.argmax([pH,pD,pA]))]
            ll = self._logloss(pH, pD, pA, y)
            correct += int(y_pred == y)
            cum_ll += ll

            # Atualiza (online)
            pH_u, pD_u, pA_u = self._update_after_game(home, away, y)

            rows.append({
                'idx': i,
                'date': row['date'] if 'date' in row else None,
                'home': home, 'away': away, 'y': y, 'pred': y_pred,
                'pH': pH, 'pD': pD, 'pA': pA,
                'logloss': ll,
                'acc_cum': correct / (len(rows)+1),
                'logloss_cum': cum_ll / (len(rows)+1),
                'h': self.params.h, 'nu': self.params.nu
            })

        results = pd.DataFrame(rows)
        summary = {
            'n_games': len(results),
            'accuracy': float(results['pred'].eq(results['y']).mean()),
            'logloss': float(results['logloss'].mean()),
            'h_final': self.params.h,
            'nu_final': self.params.nu,
            'K_used': self.params.K
        }
        return results, summary

    # ---------- Pipeline completo ----------
    def fit_and_evaluate(self, df: pd.DataFrame, train_frac: float = 1/3) -> Tuple[pd.DataFrame, dict, dict]:
        df = df.copy()
        # Ordena por data se existir; senão, respeita ordem atual
        if 'date' in df.columns:
            df = df.sort_values('date')

        n = len(df)
        n_train = max(1, int(np.floor(train_frac * n)))
        df_train = df.iloc[:n_train]
        df_test  = df.iloc[n_train:]

        # Treino offline (calibração)
        self.fit_offline(df_train)
        calib = {'h': self.params.h, 'nu': self.params.nu, 'K': self.params.K}

        # Teste online
        results, summary = self.evaluate_online(df_test)
        return results, summary, calib
