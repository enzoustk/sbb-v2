import locale
import pandas as pd
from data import load
from datetime import datetime, timedelta
from files.paths import HISTORIC_DATA
from model.config import TIME_RANGES
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
    def __init__(
        self, 
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent'
    ):
        
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
        self.df = self._get_df(date_column, df)
        self.date_column = df[date_column]
        self.month_in_date = True
        self.message = []
    
    # ----------------------------------- #

    def generate_title(self,
        df: pd.DataFrame,
        ) -> str:
        title = {}
        title['interval'] = self.interval
        title['league'] = self._get_league(df)
        title['ev_type'] = self._get_ev_type(df)
        title['period_type'] = self._get_period_type(df)

        self.message += REPORT_TITLE.format(**title)
        
    def generate_body(self,
        df: pd.DataFrame,
        ) -> str:
    
        dates = df.groupby(df[self.date_column].dt.date)
        report_body= ''
        
        for period, dataframe in dates:
            profit = dataframe['profit'].sum()
            emoji = self._get_emoji(profit=profit)
            formatted_period = period.strftime('%d')
            
            if self.month_in_date:
                formatted_period += period.strftime('-%m')
        
        REPORT_BODY.format(
            period=formatted_period,
            emoji=emoji,
            profit=f"{profit:,.2f}"
        )

            
                

    def generate_time_range(self,
        df: pd.DataFrame,
        message: str = ''
        ) -> str:
        
        grouped = df.groupby(
            'time_range', observed=True
            )['profit'].sum()
        
        ordered_profits = grouped.reindex(
            TIME_RANGES.keys(), fill_value=0
        )
        
        for time_range in TIME_RANGES:
            profit = ordered_profits[time_range]
            emoji = self._get_emoji(profit=profit)
            message += REPORT_TIME_RANGE_BODY.format(
                    time_range=time_range,
                    emoji=emoji,
                    profit=f"{profit:,.2f}"
                )
        
        return message

        

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

    def _get_league(self, df: pd.DataFrame):
        """
        Se só tem uma liga, retorna essa liga.
        Se tem mais de uma, retorna um str: 'Liga 1,
        Liga 2, Liga 3, ...
        """
        
        leagues = df['league'].drop_duplicates().tolist()
        if not leagues:
            return ''
        if len(leagues) == 1:
            return leagues[0]
        
        return ", ".join(leagues[:-1]) + " e " + leagues[-1]
            
    def _get_ev_type(self, df: pd.DataFrame):
        ev_types = df['hot_ev'].drop_duplicates().tolist
        
        if all(x > 0 for x in ev_types):
            return "Hot Tips 🔥"
        elif all(x == 0 for x in ev_types):
            return "Sem Hot Tips"
        else:
            if 0 in ev_types and any(x > 0 for x in ev_types):
                return "Todas as Apostas"
            else: 
                return ""
        
    def _get_period_type(self, df: pd.DataFrame) -> str:

        dates = pd.to_datetime(
            df[self.date_column]
            ).dt.normalize()
        
        unique_dates = dates.drop_duplicates().tolist()
        

        if len(unique_dates) > 60:
            return 'Mês'
        

        month_years = dates.dt.to_period('M').unique()
        self.month_in_date = len(month_years) > 1
        
        return 'Dia'

    def _get_emoji(self, profit):
        if profit > 0:
            return '✅✅✅'
        
        if profit < 0:
            return '❌'
        
        if profit == 0:
            return '🔁'


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

    # ----------------------------- #

    def _filter_df(self):
    
        """Quais dfs vamos retornar:
        
        1- O Mensal (TOTAL: Hot + NHot)
        2- Hot Tips
        3- Um Mensal (Total) para cada liga presente no Original
        """
        self.df = pd.DataFrame
        
        reports = []

        leagues = self.df['league'].drop_duplicates().tolist()
        
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



