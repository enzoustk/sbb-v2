from object.daily_report import Report
from datetime import timedelta, date
import pandas as pd
import logging

"""
Estrutura:
1- Filtar e gerar uma lista de DFs para cada mensagem que for enviada
2- Construir uma lista de strings para todas as mensagens juntas
3- Splitar a mensagem usando 'end'
Enviar todas as mensagens

"""



class CustomReport(Report):
    
    def __init__(self,
        df: pd.Dataframe | None = None,
        date_column: str = 'time_sent',
        ):
        
        super().__init__(df, date_column)
        
        self.today = date.today()
        self.reports = self._filter_df()
        self.filtered_df = pd.DataFrame
        self.leagues = self._get_leagues()

    def send(self):

        self._filter_df()

        for report in self.reports:
            super().generate_title(report)
            super().generate_body(report)
            super().generate_time_range(report)
            super().generate_total(report)
            self.message.append('end')
        
        messages = super().split_list_on_separator()
        for telegram_message in messages:
            super().send_message(self, telegram_message)


                    
    # ------------------------------------------- #

    def _get_league_list(self):
        self.leagues = self.df['league'].drop_duplicates().tolist()

    def _filter_df(self, 
        league: str = 'all',
        ev_type: str = 'all',
        start_date: str = None,
        end_date: str = None
        ):
        

        self._filter_date(start_date, end_date)
        self._filter_league(league)
        self._filter_ev_type(ev_type)
    
    def _filter_league(self, league: str | None = None):
        self._get_league_list()
       
        if league is None:
           self.league_str = 'Todas'
        
        elif league in self.leagues:
            self.league_str = league
            self.filtered_df = self.filtered_df[self.filtered_df['league'] == league]
        else:
            logging.error(f"League '{league}' not found in the league list.")

    def _filter_date(self,
        start_date: str | None = None,
        end_date: str | None = None
        ):

        start_date = pd.to_datetime(
            start_date).normalize() if start_date else None
        end_date = pd.to_datetime(
            end_date).normalize() + timedelta(days=1) if end_date else None


        filtered_df = self.df.copy()

        if start_date is not None:
            filtered_df = filtered_df[filtered_df[self.date_column] >= start_date]


        if end_date is not None:
            filtered_df = filtered_df[filtered_df[self.date_column] < end_date]

        self.filtered_df = filtered_df

    def _filter_ev_type(self,
        hot: bool = False,
        not_hot: bool = False,
        ):
        
        self.reports = []

        if hot:
            self.hot_df = self.filtered_df[self.filtered_df['ev_hot'] > 0]
            self.reports.append(self.hot_df)

        if not_hot:
            self.not_hot_df = self.filtered_df[self.filtered_df['ev_hot'] == 0]
            self.reports.append(self.hot_df)

        if hot and not_hot:
            self.reports.append(self.filtered_df)






class Yesterday(CustomReport):
    ...

class Today(CustomReport):
    ...

class Last7(CustomReport):
    ...

class ThisMonth(CustomReport):
    ...

class LastMonth(CustomReport):
    ...