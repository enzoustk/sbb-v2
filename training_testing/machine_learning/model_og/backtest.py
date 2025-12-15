import numpy as np
import pandas as pd
from scipy.stats import poisson
import matplotlib.pyplot as plt


class Backtester:
    def __init__(self, df: pd.DataFrame, y_pred):
        self.df = df.copy()
        self.df['pred'] = y_pred

    def make_backtest(self):
        self.df['1_3_handicap'] = self.df['1_3_handicap'].apply(self.goal_handicap)
        
        # transformar valores inválidos em NaN e converter para float
        cols = ['1_3_handicap', '1_3_over_od', '1_3_under_od', 'total_score', 'pred']
        for col in cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # extrair colunas como arrays NumPy
        handicap = self.df['1_3_handicap'].values
        over_od = self.df['1_3_over_od'].values
        under_od = self.df['1_3_under_od'].values
        total_score = self.df['total_score'].values
        pred = self.df['pred'].values
            
        valid_mask = ~(
            np.isnan(handicap) |
            np.isnan(over_od) |
            np.isnan(under_od) |
            np.isnan(total_score) |
            np.isnan(pred)
        )

        probs = np.full((len(self.df), 2), np.nan)  # inicializa com NaN
        probs[valid_mask] = np.array([
            self.poisson_goals(p, h) for p, h in zip(pred[valid_mask], handicap[valid_mask])
        ])
        prob_over = probs[:, 0]
        prob_under = probs[:, 1]

        # expectativa de valor
        ev_over = np.full(len(self.df), np.nan)
        ev_over[valid_mask] = [self.ev(o, prob) for o, prob in zip(over_od[valid_mask], prob_over[valid_mask])]

        ev_under = np.full(len(self.df), np.nan)
        ev_under[valid_mask] = [self.ev(u, prob) for u, prob in zip(under_od[valid_mask], prob_under[valid_mask])]

        # inicializar arrays de saída
        ev_bet = np.full(len(self.df), np.nan)
        bet_type = np.full(len(self.df), None, dtype=object)
        bet_profit = np.full(len(self.df), np.nan)

        # escolher entre over e under
        mask_over = valid_mask & (ev_over > ev_under) & (ev_over > 0)
        mask_under = valid_mask & (ev_under >= ev_over) & (ev_under > 0)

        # quando over é melhor
        ev_bet[mask_over] = ev_over[mask_over]
        bet_type[mask_over] = "over"

        bet_profit[mask_over] = [
            self.profit("over", h, ts, o)
            for h, ts, o in zip(handicap[mask_over], total_score[mask_over], over_od[mask_over])
        ]

        # quando under é melhor
        ev_bet[mask_under] = ev_under[mask_under]
        bet_type[mask_under] = "under"
        bet_profit[mask_under] = [
            self.profit("under", h, ts, o)
            for h, ts, o in zip(handicap[mask_under], total_score[mask_under], under_od[mask_under])
        ]

        # salvar no dataframe
        self.df['over_prob'] = prob_over
        self.df['under_prob'] = prob_under
        self.df['ev_over'] = ev_over
        self.df['ev_under'] = ev_under
        self.df['ev_bet'] = ev_bet
        self.df['bet_type'] = bet_type
        self.df['bet_profit'] = bet_profit

    def lucro_por_threshold(self, step=0.01, max_threshold=1.0):
        """
        Calcula métricas por threshold de EV:
        - Lucro total
        - ROI (lucro / número de apostas)

        Espera colunas:
            'ev_bet' : valor esperado
            'bet_profit' : lucro/prejuízo da aposta
        """
        thresholds = np.arange(0, max_threshold + step, step)
        results = []

        for t in thresholds:
            mask = self.df['ev_bet'] >= t
            df_filtrado = self.df.loc[mask]

            total_profit = df_filtrado['bet_profit'].sum(skipna=True)
            num_bets = df_filtrado.shape[0]

            roi = total_profit / num_bets if num_bets > 0 else np.nan

            results.append({
                "threshold": round(t, 2),
                "total_profit": total_profit,
                "roi": roi
            })

        return pd.DataFrame(results)

    def desempenho_por_data(self, ev_ts: float) -> pd.DataFrame:
        """
        Calcula métricas diárias aplicando um threshold de EV.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame com colunas:
            - 'date' (datetime)
            - 'ev_bet' (valor esperado da aposta)
            - 'bet_profit' (lucro/prejuízo da aposta)
        ev_ts : float
            Threshold de EV (filtra apenas apostas com ev_bet >= ev_ts)

        Returns
        -------
        pd.DataFrame
            Índice = datas
            Colunas:
            - 'total_profit' : lucro do dia
            - 'num_bets' : número de apostas do dia
            - 'roi' : lucro / nº de apostas
            - 'saldo_acumulado' : lucro acumulado ao longo dos dias
        """
        # filtrar pelas apostas acima do threshold
        df_filtrado = self.df.loc[self.df['ev_bet'] >= ev_ts].copy()

        # agrupar por data
        daily = (
            df_filtrado
            .groupby(df_filtrado['date'].dt.date)
            .agg(
                total_profit=("bet_profit", "sum"),
                num_bets=("bet_profit", "count")
            )
        )

        # calcular ROI e saldo acumulado
        daily["roi"] = daily["total_profit"] / daily["num_bets"]
        daily["saldo_acumulado"] = daily["total_profit"].cumsum()

        return daily.reset_index().rename(columns={"date": "data"})

    def plot_ev_ts(self,
        step=0.01,
        max_ts=0.5
    ):
        # Plotar saldo por EV Threshold
        self.resultados = self.lucro_por_threshold(step=step, max_threshold=max_ts)

        plt.figure(figsize=(10,5))

        # cores: verde se lucro > 0, vermelho se <= 0
        colors = np.where(self.resultados['total_profit'] >= 0, 'green', 'red')

        bars = plt.barh(
            self.resultados['threshold'],
            self.resultados['total_profit'],
            height=0.008,
            align='center',
            color=colors,
            alpha=0.8
        )


        plt.axvline(0, color='black', linestyle='--', linewidth=1)
        plt.ylabel("Threshold de EV", fontsize=12)
        plt.xlabel("Lucro Total", fontsize=12)
        plt.title("Lucro acumulado por Threshold de EV", fontsize=14, weight="bold")


        for bar in bars[::5]:
            width = bar.get_width()
            if not np.isnan(width):
                plt.text(
                    width,
                    bar.get_y() + bar.get_height()/2,
                    f"{width:.1f}",
                    ha='left', va='center',
                    fontsize=8
                )

        plt.tight_layout()
        plt.show()

    def save_xlsx(self, filename: str):
        self.df.to_xlsx(f'{filename}.xlsx', index=False)


    # ====================== Métodos Auxiliares
    def poisson_goals(
        self,
        lambda_pred: float,
        handicap: float
        ) -> tuple[float, float]:

        """
        Calculate the Probability of a given Goal Line (Handicap).
        TODO: Create Poisson Probabilities for other markets.
        """
        def half_goal_handicap(handicap, lambda_pred) -> tuple[float,float]:
            prob_over = 1 - (poisson.cdf(int(handicap), lambda_pred))
            prob_under = (poisson.cdf(int(handicap), lambda_pred))
            
            return float(prob_over), float(prob_under)
        
        def integer_handicap(handicap,lambda_pred) -> tuple[float,float]:
            prob_over_raw = 1 - (poisson.cdf(int(handicap), lambda_pred))
            prob_under_raw = (poisson.cdf(int(handicap) - 1, lambda_pred))
            
            total = prob_over_raw + prob_under_raw
            
            prob_over = prob_over_raw / total
            prob_under = prob_under_raw / total

            return float(prob_over), float(prob_under)
        
        def quarter_handicap(handicap,lambda_pred) -> tuple[float,float]:
            
            lower = handicap - 0.25
            upper = handicap + 0.25
            probs_over = []
            probs_under = []

            for line in lower, upper:
                if line % 1 == 0.5:
                    over, under = half_goal_handicap(
                    handicap=line,
                    lambda_pred=lambda_pred
                )
                    
                elif line % 1 == 0.0:  
                    over, under = integer_handicap(
                    handicap=line,
                    lambda_pred=lambda_pred
                )
                
                probs_over.append(over)
                probs_under.append(under)
            
            prob_over = sum(probs_over) / len(probs_over) 
            prob_under = sum(probs_under) / len(probs_under)
            
            return float(prob_over), float(prob_under)

        if handicap % 1 == 0.5:
            prob_over, prob_under = half_goal_handicap(
                handicap=handicap,
                lambda_pred=lambda_pred
            )

        elif handicap % 1 == 0.0:  
            prob_over, prob_under = integer_handicap(
                handicap=handicap,
                lambda_pred=lambda_pred
            )

        elif handicap % 1 in [0.25, 0.75]:  
            prob_over, prob_under = quarter_handicap(
                handicap=handicap,
                lambda_pred=lambda_pred
            )
        
        else:
            print(f'Invalid Handicap used to estimate goal probabilities: {handicap}')
            raise ValueError(f"Handicap inválido: {handicap}")
                
        return prob_over, prob_under

    def profit(self, bet_type: str, handicap: float, total_score: int, bet_odd: float) -> float:
        
        """
        Calcular o PL dado um tipo de aposta, handicap, odd e resultado.
        TODO: Permitir outros mercados.
        TODO: Permitir stake variável.
        """

        if bet_type.lower() == 'over': outcome = total_score - handicap
        elif bet_type.lower() == 'under': outcome = handicap - total_score

        try:
            if outcome >= 0.5:
                return bet_odd - 1
            elif np.isclose(outcome, 0.25):
                return (bet_odd - 1) / 2
            elif np.isclose(outcome, 0.0):
                return 0
            elif np.isclose(outcome, -0.25):
                return -0.5
            elif outcome <= -0.5:
                return -1
            
        except: 
            print(f"Ajuste de resultado inválido: {outcome}")
            return 0

    def ev(self, odd, prob):
        return odd * prob -1

    def goal_handicap(self, handicap) -> float | None:

        """
        Gets the handicap from the API and solves type errors,
        Also, converts it to a float and returns the current handicap if successful.
        """

        try: 
            if isinstance(handicap, str):
                if ',' in handicap:
                    handicap_vals = [float(h.strip()) for h in handicap.split(',')]
                    handicap = sum(handicap_vals) / len(handicap_vals)
                
                else:
                    handicap = float(handicap.strip())
            
            return handicap
        
        except ValueError as ve:
            print(f"Error converting handicap '{handicap}': {ve}")