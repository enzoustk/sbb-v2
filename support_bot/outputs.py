from object.daily_report import Report
from datetime import timedelta, date, datetime
import pandas as pd
import logging
from bet_bot import message

"""
Estrutura:
1- Filtar e gerar uma lista de DFs para cada mensagem que for enviada
2- Construir uma lista de strings para todas as mensagens juntas
3- Splitar a mensagem usando 'end'
Enviar todas as mensagens

"""


class CustomReport(Report):
    
    def __init__(self,
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent',
        start_date: str | None = None,
        end_date: str | None = None
        ):
        
            super().__init__(df, date_column)
        
        
            self.interval = self._set_custom_interval()
            self._set_custom_dates(start_date, end_date)
       



    def _set_custom_dates(self, start_date, end_date):
        
        self.start_date = self.df[self.date_column].min()
        self.end_date = self.df[self.date_column].max()
        
        if start_date:
            self.start_date = pd.to_datetime(start_date).normalize()
        if end_date:   
            self.end_date = pd.to_datetime(end_date).normalize()

    def _set_custom_interval(self):
        current_year = self.today.year
        if all(self.start_date.year == current_year,
            self.end_date.year == current_year):
            format_str = "%d/%m"
        else: 
            format_str = "%d/%m/%Y"
        
        interval = f'{self.start_date.strftime(format_str)} - {self.end_date.strftime(format_str)}'
        
        return interval


class YesterdayReport(Report):
    def __init__(self,
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent'
    ):

        super().__init__(df, date_column)

        self.interval = 'Ontem'
        self.start_date = self.today - timedelta(days=1)
        self.end_date = self.today - timedelta(days=1)


class TodayReport(Report):
    def __init__(self,
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent'
    ):

        super().__init__(df, date_column)

        self.interval = 'Hoje - Parcial'
        self.start_date = self.today
        self.end_date = self.today


class LastSevenDaysReport(Report):
    def __init__(self,
            df: pd.DataFrame | None = None,
            date_column: str = 'time_sent'
        ):

            super().__init__(df, date_column)


            self.interval = 'Últimos 7 Dias'
            self.start_date = self.today - timedelta(days=6)
            self.end_date = self.today


class ThisMonthReport(Report):
    def __init__(self,
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent'
    ):

        super().__init__(df, date_column)


        self.interval = 'Mês Atual'
        self.start_date = date(self.today.year, self.today.month, 1)
        self.end_date = self.today


class LastMonthReport(Report):
    def __init__(self,
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent'
    ):

        super().__init__(df, date_column)


        self.interval = 'Mês Atual'
        self.start_date = (
            self.today.replace(day=1) - 
            timedelta(days=1)).replace(day=1)
        self.end_date = self.today


class YearToDateReport(Report):
    def __init__(self,
        df: pd.DataFrame | None = None,
        date_column: str = 'time_sent'
    ):

        super().__init__(df, date_column)


        self.interval = 'Mês Atual'
        self.start_date = date(self.today.year, 1, 1 )
        self.end_date = self.today