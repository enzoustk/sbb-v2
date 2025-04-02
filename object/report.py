import locale
import pandas as pd
from data import load
from datetime import datetime, timedelta
from files.paths import HISTORIC_DATA
from telegram.constants import (MONTH_NAMES,
    REPORT_TITLE, REPORT_BODY, REPORT_TOTAL,
    REPORT_TIME_RANGE_TITLE, REPORT_TIME_RANGE_BODY,
)

"""
Quebrar os dataframes por liga
Gerar um Relatório filtrado para cada liga
Gerar um Relatório Total
Gerar um Relatório Hot Tips Total    
"""

class Report():
    def __init__(self, 
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent'
    ):
        
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
        self.df = self._get_df(date_column, df)
        self.date_column = df[date_column]
    
    # ----------------------------------- #

    def _get_df(self, date_column: str, df: pd.DataFrame | None = None):
        
        if df is None:
            try: 
                df = pd.read_csv(HISTORIC_DATA)
                df = df.dropna(subset='bet_type')
                df[date_column] = pd.to_datetime(
                    df[date_column]
                )
                print(f"Data loaded sucessfully: {len(df)} lines")
                return df
            except Exception as e: 
                print(f"Error loading data: {e}")
                return pd.DataFrame()

        if df is not None: 
            print(f"Data loaded sucessfully with {len(df)} lines")
            return df

class DailyReport(Report):

    

    def __init__(self, 
            df: pd.DataFrame | None = None,
            ):
        
        """Carrega o dataframe df, 
        se não for especificado, usa o df HISTORIC_DATA
        filta os dados para só ter apostas.
        """

        super().__init__(df)
        self.date = datetime.now() - timedelta(days=1)
        self.interval = self.date.strftime('%M de %Y')
        self.reports = self._filter_df()


    def send():
        pass        


    # ----------------------------- #
        

    def generate_title(self, league):
        
        
        
        

        message += REPORT_TITLE.format(
            interval = interval,
            league = league,
            ev_tipe = 'Todas as Apostas',
            period_type = 'Dia'
        )

    def generate_body(self, df):
        
        for line in df:
            self.message += REPORT_BODY.format(
                period = line['date'],
                profit = line['profit'],
                emoji = self.get_emoji(float(line['profit']))
            )

    def generate_total(self, df):
        pass


    # ----------------------------- #

    def _filter_df(self):
    
        """Quais dfs vamos retornar:
        
        1- O Mensal (TOTAL: Hot + NHot)
        2- Hot Tips
        3- Um Mensal (Total) para cada liga presente no Original
        """
        self.df = pd.DataFrame
        
        reports = []

        leagues = self.df['league'].drop_duplicates().tolist
        
        month_df = self.df[
            (self.df[self.date_column].dt.month == self.date.month) & 
            (self.df[self.date_column].dt.year == self.date.year)
        ]
        hot_tips_df = month_df[(month_df['hot_ev'] > 0)]
        
        reports.append(month_df)
        reports.append(hot_tips_df)

        if len(leagues) > 1:
            for league in leagues:
                reports.append(league)
        
        return reports

    def _get_emoji(self, profit):
        if profit > 0:
            return '✅✅✅'
        
        if profit < 0:
            return '❌'
        
        if profit == 0:
            return '🔁'

    def _get_player_df(self, 
            df: pd.DataFrame,
        ) -> pd.DataFrame:
        
        """
        Retorna um dataframe ordenado com os jogadores presentes no df
        Rankeados de acordo com o profit
        """

        home_df = (
            df.groupby(['home_player', 'bet_type'])['profit']
            .sum()
            .reset_index()
            .rename(columns={'home_player': 'player'})
        )


        away_df = (
            df.groupby(['away_player', 'bet_type'])['profit']
            .sum()
            .reset_index()
            .rename(columns={'away_player': 'player'})
        )

        combined_df = pd.concat(
            [home_df, away_df],
            ignore_index=True
            )

        final_df = (
            combined_df.groupby(['player', 'bet_type'])['profit']
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )


        final_df['total_profit'] = (final_df['over'] +
            final_df['under']
        )

        final_df = final_df.sort_values(
            by='final_df', ascending=False)
        
        return final_df

    def _get_profit_data(self, df: pd.DataFrame) -> list[dict]:
        reports = []

        bet_types = [
            {"bet_type": "total"}, 
            {"bet_type": "over"}, 
            {"bet_type": "under"}
        ]
        
        for bt in bet_types:
            filtered_df = df if bt["type"] == "all" else df[
                df["bet_type"] == bt["type"]]
            
            profit = filtered_df["profit"].sum()
            vol = filtered_df["profit"].count()
            roi = profit / vol if vol != 0 else 0
            emoji = self._get_emoji(profit)

            
            reports.append({
                "bet_type": bt["label"],
                "profit": profit,
                "total_emoji": emoji,
                "vol": vol,
                "roi": roi
            })
        
        return reports

class CustomReport(Report):
    def __init__(self, df):
        super().__init__(df)
       
        
        
        



    # ----------------------------------------- #

class PlayerReport(CustomReport):
    pass



