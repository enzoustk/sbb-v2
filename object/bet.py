import json
import logging
import threading
import pandas as pd
from data import load
from api import fetch, validate
from model import calculate
from telegram import message
from model.config import EV_THRESHOLD, TIME_RANGES, AJUSTE_FUSO
from files.paths import ALL_DATA, NOT_ENDED, ERROR_EVENTS, MADE_BETS
from constants.telegram_params import (TELEGRAM_MESSAGE, MIN_LINE_MESSAGE,
    MIN_ODD_MESSAGE, HOT_TIPS_MESSAGE, EDITED_MESSAGE,RESULT_EMOJIS, BET_TYPE_EMOJIS,
    HOT_TIPS_STEP, MAX_HOT, HOT_THRESHOLD)


class Bet:
    """Represents a betting opportunity and manages its lifecycle.

    Handles data storage, probability calculations, EV analysis, 
    external communication (Telegram), and persistence.

    Args:
        event (dict): Raw event data from scanning system with:
            - 'id': Unique event identifier
            - 'home'/'away': Team/player names
            - 'league': League information

    Attributes:
        event_id (str): Unique event identifier
        odds (tuple): (over_odd, under_odd, handicap)
        probabilities (tuple): (prob_over, prob_under)
        ev_values (tuple): (ev_over, ev_under)
        bet_type (str): Final bet decision ('over'/'under'/None)

    Notes:
        Maintains state through entire bet lifecycle:
        1. Identification -> 2. Analysis -> 3. Execution -> 4. Settlement
    """

    """
    TODO: Create a subset to bet exported in xlsx
    TODO: Create cancel method to cancel a made bet
    TODO: Create a way to delete Bet Objetcts that are no longer needed to be stored
    """

    def __init__(self, event: dict):
        """Initializes Bet instance with raw event data.
    
        Parses essential identifiers and names from event dictionary.
        Initializes all tracking attributes to default None/False values.
        """

        self.event = event

        self.event_id = self._get_event_id()
        self.league = self._get_league()

        self.home_str = self._get_str('home')
        self.away_str = self._get_str('away')
        
        self.home_team = self._get_name('home', 'team')
        self.home_player = self._get_name('home', 'player')
        self.away_team = self._get_name('away', 'team')
        self.away_player = self._get_name('away', 'player')
        self.players = self._get_players()
  
        self.odd_over = None 
        self.odd_under = None
        self.handicap = None

        self.prob_over = None
        self.prob_under = None
        self.ev_over = None
        self.ev_under = None

        self.bet_type = None
        self.bet_odd = None
        self.bet_prob = None
        self.bet_ev = None

        self.hot_ev = None
        self.hot_emoji = None
        
        self.minimum_line = None
        self.minimum_odd = None
        self.time_sent = None
        self.lambda_pred = None

        self.ended = False
        self.home_score = None
        self.away_score = None
        self.total_score = None
        self.raw_score = None

        self.profit = None
        self.result = None
        self.canceled = None

        self.message = ""
        self.sent = None
        self.message_id = None
        self.chat_id = None
        self.edited = False
        self.result_emoji = None
        self.bet_type_emoji = None
        self.time_interval = None

        self.saved_on_excel = False
        self.month = None
        self.totally_processed = None

    def get_odds(
        self,
        market: str='goals'
        ):

        """Fetches and validates betting odds from external API.

        Args:
            market: Betting market to analyze (default: 'goals')

        Updates:
            handicap (float): Line for over/under bet
            odd_over (float): Odds for over bet
            odd_under (float): Odds for under bet

        TODO: Add support for Asian Handicap and other markets
        """
                
        betting_data = fetch.odds(self.event_id)
        
        (self.handicap,
         self.odd_over,
         self.odd_under
        ) = validate.odds(
            betting_data,
            self.event_id,
            market=market
        )
                                        
    def find_ev(self, lambda_pred: float):

        """Calculates expected value for potential bets.

        Args:
            lambda_pred: Model's predicted goal expectation

        Uses:
            calculate.poisson_goals: Converts lambda to probabilities
            calculate.ev: Computes expected value for each outcome

        Sets:
            bet_type: 'over'/'under' if EV > EV_THRESHOLD, else None
        """

        self.lambda_pred = lambda_pred
        
        self.prob_over, self.prob_under = calculate.poisson_goals(self.lambda_pred, self.handicap)
        self.ev_over = calculate.ev(self.odd_over, self.prob_over)
        self.ev_under = calculate.ev(self.odd_under, self.prob_under)

        if self.ev_over >= EV_THRESHOLD:
            self._get_bet_type('over')
        
        elif self.ev_under >= EV_THRESHOLD:
            self._get_bet_type('under')
        
        self._print_bet_data()

    def handle_made_bet(self):
        self._find_min_line()
        self._generate_message()
        self._send_message

    def save_bet(self):
        """Adds the current bet to the NOT_ENDED file."""
        
        existing_df = load.data('not_ended')

        new_data = pd.DataFrame([self.__dict__])
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        updated_df.to_csv(NOT_ENDED, index=False)
    
    def handle_ended_bet(self):

        '''
        If the bet has a bet_type:
            Calculates Profit,
            Edits the telegram message
            Saves the bet on excel
        '''

        if self.bet_type is None: return
        self.profit, self.result = calculate.profit(self.bet_type, self.handicap, self.total_score, self.bet_odd)
        self._edit_telegram_message()
        self._save_made_bet()
        
    def mark_processed(self):
        """Gets all the attributes that are needed to be processed
        If all of them were processed successfully, marks self.totally_processed as True
        """
        
        if self.bet_type is not None:
            self.totally_processed = all([
                self.sent,
                self.edited,
                self.ended,
                self.saved_on_excel,
                self.profit is not None,
                self.result is not None,
                self.raw_score is not None
                ])
        else: 
            if self.raw_score is not None:
                self.totally_processed = True
 
    # ------------------------------------------- #

    def _edit_telegram_message(self):

        '''
        Updates Bet object with the new data
        Edits telegram message
        '''

        self._get_bet_emojis()
        self.message += EDITED_MESSAGE.format(**self.__dict__)
        self._escape()
        self.edited = message.edit(self.message_id, self.message, self.chat_id)

    def _get_bet_type(self, bet_type: str | None):
        
        """
        Gets Bet Type Object.
        Args:
            bet_type (str): Type of bet ('over'/'under'/'None')
        """

        self.bet_type = bet_type

    def _escape(self):
        """Escapes all problematic characters in the message."""
        self.message = (
            self.message.replace('.', r'\.')
                                .replace('-', r'\-')
                                .replace('(', r'\(')
                                .replace(')', r'\)')
                                .replace('|', r'\|')
                                .replace('#', r'\#')
                                .replace('_', r'\_')
        )
    
    def _get_bet_emojis(self):
        """Gets emoji for the result and bet type
        Assings it to object attributes"""

        self.result_emoji = RESULT_EMOJIS.get(self.result, '')
        self.bet_type_emoji = BET_TYPE_EMOJIS.get(self.bet_type, '')
    
    def _get_end(self):
        
        """
        Checks if the event has ended.
        If the event is not in live events, sets ended to True
        and calls _get_score() to fetch the final score.
        """

        live_events = fetch.live_events()

        live_ids = {str(event['id']) for event in live_events}

        if self.event_id not in live_ids:
            if self._get_score() is not None:
                self.ended = True
  
    def _get_event_id(self) -> str:
        return self.event['id']

    def _get_str(self,
        type: str
        ) -> str:
        """Gets and sets self.home_str and self.away_str
        Args:
            type (str): 'home' or 'away'
        Returns:
            {type}_str: Full name of the team/player. 
            Example: 'Barcelona (Player_Name) Esports'
        """
        return self.event.get(type, {}).get('name')
        
    def _get_players(self) -> tuple[str, str]:
        """Tries to  generate a tuple containing sorted and
        lowercased names of the players.

        Returns:
            tuple[str, str]: Tuple containing the names of the players
            Example: ('boulevard', 'meltosik')

            if it fails, returns an empty tuple
        """
        
        try:
            home = str(self.home_player).lower()
            away = str(self.away_player).lower()
            return tuple(sorted([home, away]))
        except:
            logging.error("Error: Failed to get players for "
                f"Event ID: {self.event_id}")
            return ('', '')

    def _get_name(
        self, 
        side: str | None = None,
        type: str | None = None,
        ) -> str | None:
    
        """
        Gets team_str: 'Barcelona (Player_Name) Esports'
        if type=team, Returns: 'Barcelona'
        if type=player, Returns: 'Player_Name'
        """


        if side is None or type is None:
            logging.error("side or type is None while trying to get name")
            return None

        team_str = self.event.get(side, {}).get('name')
        
        if type == 'team':
            try:
                return team_str.split('(')[0].strip().lower()
            
            except Exception as e:
                logging.error(f"Error: {e}")
                return None
        
        if type == 'player':
            try:
                start = team_str.find('(') + 1
                end = team_str.find(')')
                return team_str[start:end].lower()
            
            except Exception as e:
                logging.error(f"Error: {e}")
                return None
    
    def _get_score(self):

        """Fetches and parses final score from event API.
        
        Updates Instance Attributes:
            home_score (int): Goals from home team
            away_score (int): Goals from away team
            total_score (int): Combined goals
            raw_score (str): Raw score string from API

        Note:
            Sets `ended=True` if score is successfully retrieved
        """

        event_data = fetch.event_for_id(self.event_id)

        self.raw_score = event_data.get('ss', None)
        
        if self.raw_score is None:
            return
        
        self.home_score, self.away_score = map(int, self.raw_score.split('-'))
        self.total_score = self.home_score + self.away_score

    def _get_hot_tip(self) -> None:
        """Calculates 'hotness' level based on Expected Value."""

        if self.bet_ev < HOT_THRESHOLD:
            return

        ev_over_threshold = self.bet_ev - HOT_THRESHOLD
        steps = int(ev_over_threshold // HOT_TIPS_STEP)
        self.hot_ev = min(steps, MAX_HOT)
        self.hot_emoji = "🔥" * self.hot_ev

    def _get_time_atributes(self):
        """Sets all time-related atributes
        based on the current time"""
        self.time_sent = pd.Timestamp.now() - pd.Timedelta(hours=AJUSTE_FUSO)
        self.month = self.time_sent.strftime("%m/%Y")
        hour = self.time_sent.hour

        for range, (start, end) in TIME_RANGES.items():
            if start <= hour <= end:
                self.time_range = range

    def _get_league(self) -> str:
        """Fetches league name from event data.
        If it fails, returns 'Unknown League'.
        """
        
        return self.event.get('league', {}).get('name', 'Unknown League')
    
    def _get_excel_columns(self):
        """Returns a dcit with the columns and values
        To the Made Bets Excel file
        """
        return{
            'Horário Envio': self.time_sent.strftime("%H:%M"),
            'Liga': self.league,
            'Partida': self.home_str + 'vs. ' + self.away_str,
            'Tipo Aposta': self.bet_type.capitalize(),
            'Hot Tips': self.hot_emoji,
            'Linha': f'{self.handicap:2f}',
            'Resultado' : self.result.replace('_', ' ').capitalize(),
            'Odd': f'{self.bet_odd:2f}',
            'Lucro': f'{self.profit:2f}',
            'Intervalo': self.time_range,
        }

    def _get_lambda_pred(self,
        lambda_pred: float
        ):
        """Sets lambda_pred to the current object"""

        self.lambda_pred = lambda_pred
     
    def _get_bet_type(self, bet_type: str | None = None):
        """Creates all MADE bet realted features

        Args:
            bet_type (str | None, optional): Sets bet atributes
            to be over or under data, depending on the bet_type.
            Defaults to None.
        """

        self.bet_type = bet_type

        if self.bet_type is 'over':
            self.bet_odd = self.odd_over
            self.bet_prob = self.prob_over
            self.bet_ev = self.ev_over
        
        elif self.bet_type is 'under':
            self.bet_odd = self.odd_under
            self.bet_prob = self.prob_under
            self.bet_ev = self.ev_under
    
    def _print_bet_data(self):
        
        """Print all bet data to the console.
        """

        print(f"League: {self.league}")
        print(f"{self.home_player} ({self.home_team}) vs {self.away_player} ({self.away_team})")
        print('-' * 20)
        print(f"Line: {self.handicap}")
        print(f"Lambda: {self.lambda_pred}")
        print('-' * 20)
        print(f"Over Probability: {self.prob_over*100:.2f}%")
        print(f'Over Odd: {self.odd_over}')
        print(f"Under Probability: {self.prob_over*100:.2f}%")
        print(f'Under Odd: {self.odd_under}')
        print('-' * 20)
        print(f"Over EV: {self.ev_over*100:.2f}%")
        print(f"Under EV: {self.ev_under*100:.2f}%")
        print('-' * 60)
        
        if self.bet_type is not None: 
            print(f'Bet: {self.bet_type} {self.handicap} @{self.bet_odd}')
            print(f'Minimum Line: {self.minimum_line} @{self.minimum_odd}')
            print(f'Hot Tip: {self.hot_ev}')
        
        if self.bet_type is None: 
            print('No EV+ Bet Found')
  
    def _find_min_line(self):
        """Finds and sets the minimum line and odd for the current bet type.
        self.minimum_line, self.minimum_odd = calculate.min_goal_line(
            self.handicap, self.bet_type, self.bet_prob)
        """

    def _generate_message(self):
        
        """"
        If bet_type is none, breaks
        Creates and formats telegram message based
        on current object bet data
            if bet_type == None, break
        Looks at minimum line and hot tips data.
        If it exists, appends to the message.
        """
        
        self.message = TELEGRAM_MESSAGE.format(**self.__dict__)

        if self.minimum_line == self.handicap and self.minimum_odd != self.bet_odd:
            self.message += MIN_ODD_MESSAGE.format(**self.__dict__)
        
        elif self.minimum_line != self.handicap:
            self.message += MIN_LINE_MESSAGE.format(**self.__dict__)
        
        if self._get_hot_tip() is not None:
            self.message += HOT_TIPS_MESSAGE.format(**self.__dict__)

    def _send_message(self):
        
        '''
        If bet time is not None, gets called
        Sends the message on telegram using message.send
        Marks self.sent as True or False, depending if it sent sucessfully
        Gets all time-related class objects
        '''
        
        self.message_id, self.chat_id = message.send(self.message)
        self._get_time_atributes()
        if self.message_id is None: self.sent = False

    def _save_made_bet(self):
        """Saves successfully placed bets to a month-specific Excel sheet.

        Persists bet data to MADE_BETS Excel file with the following logic:
        - Creates new monthly sheet if none exists
        - Appends to existing sheet while preserving historical data
        - Maintains consistent column structure across entries

        Workflow:
            1. Validates bet_type exists (skips with warning otherwise)
            2. Creates/updates Excel file with openpyxl engine
            3. Maintains one sheet per month (MM/YYYY format)
            4. Preserves existing data when adding new entries

        Side Effects:
            - Sets saved_on_excel flag to True on success
            - Modifies MADE_BETS Excel file on disk

        Raises:
            PermissionError: If Excel file is locked/open in another program
            ValueError: If DataFrame columns mismatch existing sheet structure

        Notes:
            - Uses _get_excel_columns() for column mapping standardization
            - Implements exception handling for missing file scenarios
            - Requires openpyxl package for Excel manipulation
        """

        if self.bet_type is None:
            logging.warning("Attempted to save match we didn't bet on. Skipped Sucessfully")
            return
        
        try:
            with pd.ExcelWriter(MADE_BETS, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                
                if str(self.month) in writer.book.sheetnames:
                    df_existing = pd.read_excel(MADE_BETS, sheet_name=str(self.month))
                else:
                    df_existing = pd.DataFrame(columns=self._get_excel_columns().keys())
                
                
                new_data = pd.DataFrame([self._get_excel_columns()])
                df_updated = pd.concat([df_existing, new_data], ignore_index=True)
                df_updated.to_excel(writer, sheet_name=str(self.month), index=False)
                self.saved_on_excel = True
                
        except FileNotFoundError:
            new_data = pd.DataFrame([self._get_excel_columns()])
            with pd.ExcelWriter(MADE_BETS, engine='openpyxl') as writer:
                new_data.to_excel(writer, sheet_name=str(self.month), index=False)
            self.saved_on_excel = True