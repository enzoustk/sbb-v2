import locale
import logging
import pandas as pd
from bet_bot import message
from datetime import datetime, timedelta, date
from files.paths import HISTORIC_DATA, LOCK, MADE_BETS
from model.betting_config import TIME_RANGES
from bet_bot.constants import (
    REPORT_TITLE, REPORT_BODY, REPORT_TOTAL,
    REPORT_TIME_RANGE_TITLE, REPORT_TIME_RANGE_BODY,
)

logger = logging.getLogger(__name__)

# TODO: Create CustomReport and PlayerReport classes

class Report:
    def __init__(
        self, 
        df: pd.DataFrame | None = None,
        date_column: str = 'date'
    ):
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        self.df = self._get_df(date_column, df)
        self.date_column = date_column
        self.month_in_date = True
        self.message = []
        self.today = date.today()

    
    def _filter_df(self, 
        league: str = 'all',
        ev_type: str = 'all',
        ):

        self._filter_date()
        self._filter_league(league)
        self._filter_ev_type(ev_type)

    
    def build_and_send(
            self,
            chat_id: str = -1002343941988,
            ):
        try:
            for report in self.reports:
                self.generate_title(report)
                self.generate_body(report)
                self.generate_time_range(report)
                self.generate_total(report)
                self.message.append('end')
            
            message_groups = self.split_list_on_separator()
            
            for group in message_groups:
                formatted_message = "\n".join(group)
                message.send(message=formatted_message, chat_id=chat_id) 
                
        except Exception as e:
            logger.error(f'Error mandando report: {e}')
    # ----------------------------------- #

    
    def _filter_date(self):

        filtered_df = self.df.copy()

        if self.start_date is not None:
            filtered_df = filtered_df[
                filtered_df[self.date_column] >= self.start_date]

        if self.end_date is not None:
            filtered_df = filtered_df[
                filtered_df[self.date_column] < (
                    self.end_date + timedelta(days=1))
            ]

        self.filtered_df = filtered_df

    def _filter_league(self, league: str | None = None):
        
        self.leagues = self.df['league'].drop_duplicates().tolist()
       
        if league is None:
           self.league_str = 'Todas'
        
        elif league in self.leagues:
            self.league_str = league
            self.filtered_df = self.filtered_df[self.filtered_df['league'] == league]
        else:
            logger.error(f"League '{league}' not found in the league list.")

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
                self.reports.append(self.not_hot_df)  # Corrigido: append not_hot_df
            if hot and not_hot:
                self.reports.append(self.filtered_df)


    # ----------------------------------- #

    def generate_title(self, df: pd.DataFrame):
        title = {}
        title['interval'] = self.interval
        title['league'] = self._get_league(df)
        title['ev_type'] = self._get_ev_type(df)
        title['period_type'] = self._get_period_type(df)

        self.message.append(REPORT_TITLE.format(**title))
            
    def generate_body(self, df: pd.DataFrame):
        report_body = []
        for period, dataframe in df.groupby(df[self.date_column].dt.date):
            profit = dataframe['profit'].sum()
            emoji = self._get_emoji(profit)
            formatted_period = period.strftime('%d')
            
            if self.month_in_date:
                formatted_period += period.strftime('-%m')
            
            report_body.append(
                REPORT_BODY.format(
                    period=formatted_period,
                    emoji=emoji,
                    profit=f"{profit:,.2f}"
                )
            )
        
        for line in report_body:
            self.message.append(line)

    def generate_time_range(self, df: pd.DataFrame):
        time_range_list = []
        grouped = df.groupby('time_range', observed=True)['profit'].sum()
        ordered_profits = grouped.reindex(TIME_RANGES.keys(), fill_value=0)
            
        for time_key in TIME_RANGES:
            profit = ordered_profits[time_key]
            emoji = self._get_emoji(profit)
            time_range_list.append(
                REPORT_TIME_RANGE_BODY.format(
                    time_range=time_key,
                    emoji=emoji,
                    profit=f"{profit:,.2f}"
                )
            )

        self.message.append(REPORT_TIME_RANGE_TITLE)
        for line in time_range_list:
            self.message.append(line)

    def generate_total(self, df: pd.DataFrame):
        message_lines = []
        sub_dfs = {'total': df}
        grouped = df[df['bet_type'].notna()].groupby('bet_type')
        
        for bet_type, group in grouped:
            sub_dfs[bet_type] = group
        
        self.message.append('')

        for bet_type_key, sub_df in sub_dfs.items():
            profit = sub_df['profit'].sum()
            vol = sub_df['profit'].count()
            roi = (profit / vol) if vol > 0 else 0
            total_emoji = self._get_emoji(profit)
            players_df = self._get_player_df(sub_df)
            notable_players = self._get_notable_players(players_df)

            message_lines.append(  
                REPORT_TOTAL.format(
                    bet_type=f'{bet_type_key.capitalize()}',
                    profit=f'{profit:.2f}',
                    total_emoji=total_emoji,
                    vol=vol,
                    roi=roi,
                    best_player=notable_players['best_player']['player'],
                    bp_emoji=notable_players['best_player']['emoji'],
                    bp_profit=f'{notable_players['best_player']['profit']:.2f}',
                    worst_player=notable_players['worst_player']['player'],
                    wp_emoji=notable_players['worst_player']['emoji'],
                    wp_profit=f'{notable_players['worst_player']['profit']:.2f}',
                )
            )

        # Adiciona todas as linhas de total
        for line in message_lines:
            self.message.append(line)

    def split_list_on_separator(self, separator: str = 'end') -> list[list]:

        separator_indices = [i for i, item in enumerate(self.message) if item == separator]
        
        sublists = []
        start = 0
        
        for sep_index in separator_indices:
            sublist = self.message[start:sep_index]  
            sublists.append(sublist)
            start = sep_index + 1
        
        return sublists


    # ----------------------------------- #

    def _get_df(self, date_column: str, df: pd.DataFrame | None = None):
        if df is None:
            try: 
                with LOCK:
                    df = pd.read_csv(HISTORIC_DATA)
                    df = df.dropna(subset='bet_type')
                    df[date_column] = pd.to_datetime(
                        df[date_column]
                    )
                    copied_df = df.copy()
                    print(f"Data loaded sucessfully: {len(copied_df)} lines")
                    return copied_df
            except Exception as e: 
                print(f"Error loading data: {e}")
                return pd.DataFrame()

        if df is not None: 
            print(f"Data loaded sucessfully with {len(df)} lines")
            return df

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
            .reindex(columns=['over', 'under'], fill_value=0)
            .reset_index()
        )


        final_df['total_profit'] = (final_df['over'] +
            final_df['under']
        )

        final_df = final_df.sort_values(
            by='total_profit', ascending=False  
        )
        return final_df

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
        ev_types = df['hot_ev'].drop_duplicates().tolist()
        
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

    def _get_notable_players(self, df: pd.DataFrame) -> dict:
        notable_players = {}
        
        if not df.empty and 'total_profit' in df.columns:  
            bp_row = df.loc[df['total_profit'].idxmax()] 
            notable_players['best_player'] = {
                'player': bp_row['player'],
                'profit': bp_row['total_profit'],
                'emoji': self._get_emoji(bp_row['total_profit'])
            }
            
            wp_row = df.loc[df['total_profit'].idxmin()]
            notable_players['worst_player'] = {
                'player': wp_row['player'],
                'profit': wp_row['total_profit'],
                'emoji': self._get_emoji(wp_row['total_profit'])
            }
        
        return notable_players

    def _get_emoji(self, profit):
        if profit > 0:
            return '✅'
        
        if profit < 0:
            return '❌'
        
        if profit == 0:
            return '🔁'


class NormalReport(Report):
    def __init__(self, 
            df: pd.DataFrame | None = None,
            ):
        
        """Carrega o dataframe df, 
        se não for especificado, usa o df HISTORIC_DATA
        filta os dados para só ter apostas.
        """

        super().__init__(df)
        self.date = datetime.now() - timedelta(days=1)
        self.interval = self.date.strftime('%m de %Y')
        self.reports = self._filter_df()

    def _filter_df(self):
    
        """Quais dfs vamos retornar:
        
        1- O Mensal (TOTAL: Hot + NHot)
        2- Hot Tips
        3- Um Mensal (Total) para cada liga presente no Original
        """

        
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
                league_df = month_df[
                    month_df['league'] == league
                ]
                reports.append(league_df)
        
        return reports
