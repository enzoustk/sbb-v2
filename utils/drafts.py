import pandas as pd
from files.paths import MADE_BETS
from data import load
from model import calculate
from bet_bot import escape
from bet_bot import message
from bet_bot.constants import TELEGRAM_MESSAGE, MIN_ODD_MESSAGE, MIN_LINE_MESSAGE, HOT_TIPS_MESSAGE, EDITED_MESSAGE, CANCELED_MESSAGE, LINKS_MESSAGE
    
    

# TODO: Adicionar LOCK nos méotodos
# TODO: Resolver como vamos declarar a aposta no comando do bot

def _find_xlsx_line(self):
    return (
        self._format_data(pd.to_datetime(self.time_sent)) +
        self.home_str + ' vs. ' + self.away_str
    )

def cancel(self):
    """
    Objetivo: Mexer no CSV, no XLSX, e no Telegram
    """

    historic = load.data('historic')
    bets = pd.read_excel(MADE_BETS)

    csv_filter = (historic['event_id'] == self.event_id)
    historic.loc[csv_filter, 'profit'] = 0
    historic.loc[csv_filter, 'canceled'] = 'True'

    xlsx_filter = (bets['Horário Envio'] + bets['Partida'] == self._find_xlsx_line())
    bets.loc[xlsx_filter, 'Resultado'] = f'Anulada (Seria {self.result}'
    bets.loc[xlsx_filter, 'Lucro'] = 0

    self.profit = 0
    self.result_emoji = '🔁'
    self.result = 'Anulada'
    self.canceled = True

    self.message = self._generate_message()
    self._cancel_telegram_bet()

def _cancel_telegram_bet(self):
    escaped_dict = {
            key: escape.markdown(value)
            for key, value 
            in self.__dict__.items()
            }
    self.message = escape.markdown(self.message)
    self.message += CANCELED_MESSAGE.format(**escaped_dict, LINKS_MESSAGE=LINKS_MESSAGE)
    self.edited = message.edit(self.message_id, self.message, self.chat_id)

def swap_score(self, home_score, away_score):
    historic = load.data('historic')
    bets = pd.read_excel(MADE_BETS)

    csv_filter = (historic['event_id'] == self.event_id)
    historic.loc[csv_filter, 'home_score'] = self.home_score = home_score
    historic.loc[csv_filter, 'away_score'] = self.away_score = away_score
    historic.loc[csv_filter, 'total_score'] = self.total_score = home_score + away_score

    self.profit, self.result = calculate.profit(
        bet_type=historic.loc[csv_filter, 'bet_type'],
        handicap=historic.loc[csv_filter, 'handicap'],
        total_score= (home_score+away_score),
        bet_odd=historic.loc[csv_filter, 'bet_odd']
        )
    
    historic.loc[csv_filter, 'profit'] = self.profit
    historic.loc[csv_filter, 'result'] = self.result
    self._get_result_emoji()

    xlsx_filter = (bets['Horário Envio'] + bets['Partida'] == self._find_xlsx_line())
    bets.loc[xlsx_filter, 'Resultado'] = self.result
    bets.loc[xlsx_filter, 'Lucro'] = self.profit
    self._swap_telegram_score()

def _swap_telegram_score(self):
    formated_dict = {
        key: self._format_data(value)
        for key, value 
        in self.__dict__.items()
        }

    self.message = TELEGRAM_MESSAGE.format(**formated_dict)

    if self.minimum_line == self.handicap and self.minimum_odd != self.bet_odd:
        self.message += MIN_ODD_MESSAGE.format(**formated_dict)
    
    elif self.minimum_line != self.handicap:
        self.message += MIN_LINE_MESSAGE.format(**formated_dict)
    
    if self.hot_ev is not None:
        if self.hot_ev == 0: return
        self.message += HOT_TIPS_MESSAGE.format(**formated_dict)

    escaped_dict = {
        key: escape.markdown(value)
        for key, value 
        in self.__dict__.items()
        }
    
    self.message = escape.markdown(self.message)
    self.message += EDITED_MESSAGE.format(**escaped_dict, LINKS_MESSAGE=LINKS_MESSAGE)
    self.edited = message.edit(self.message_id, self.message, self.chat_id)