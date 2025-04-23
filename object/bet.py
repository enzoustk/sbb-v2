
import logging
import pandas as pd
from data import load
from model import calculate
from zoneinfo import ZoneInfo
from api import fetch, validate
from bet_bot import message, escape
from datetime import datetime, timezone, timedelta
from model.betting_config import (EV_THRESHOLD, TIME_RANGES,
    AJUSTE_FUSO, HOT_TIPS_STEP, MAX_HOT, HOT_THRESHOLD)
from api.constants import LEAGUE_IDS
from files.paths import NOT_ENDED, MADE_BETS
from bet_bot.constants import (TELEGRAM_MESSAGE, MIN_LINE_MESSAGE,
    MIN_ODD_MESSAGE, HOT_TIPS_MESSAGE, EDITED_MESSAGE, CANCELED_MESSAGE,
    RESULT_EMOJIS, BET_TYPE_EMOJIS, LINKS_MESSAGE)

logger = logging.getLogger(__name__)
bet_logger = logging.getLogger('bet')


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
    TODO: Create Class EndedBet as child class to __init__ with all data in its method
    """

    def __init__(self, event: dict):
        """Initializes Bet instance with raw event data.
    
        Parses essential identifiers and names from event dictionary.
        Initializes all tracking attributes to default None/False values.
        """
        self._init_defaults()
        self._update_from_event(event)

    def _init_defaults(self):
        """Initialize all trackable attributes with safe defaults"""

        self.event_id = None
        self.league = None
        self.date = None

        self.home_str = ""
        self.away_str = ""
        self.home_team = ""
        self.home_player = ""
        self.away_team = ""
        self.away_player = ""
        self.players = ()

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
        self.time_range = ''

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
        self._get_hot_tip()
        print_hot_ev = self.hot_ev if self.hot_ev is not None else 0

        if self.bet_type is not None:
            message = f"""
            Bet: {self.bet_type} {self.handicap} @{self.bet_odd}
            Minimum Line: {self.minimum_line} @{self.minimum_odd}
            Hot Tip: {print_hot_ev}
        """
        bet_logger.bet(message)
        self._generate_message()
        self._send_message()

    def save_bet(self):
        """Adds the current bet to the NOT_ENDED file."""
        
        existing_df = load.data('not_ended')
        existing_df = existing_df.dropna(axis=1, how='all')

        new_data = pd.DataFrame([self.__dict__])
        new_data = new_data.dropna(axis=1, how='all')

        if not existing_df.empty or all(existing_df.isna().all()):
            updated_df: pd.DataFrame = pd.concat([existing_df, new_data], ignore_index=True)
            updated_df.to_csv(NOT_ENDED, index=False)
        else:
            new_data.to_csv(NOT_ENDED, index=False)
    
    def handle_ended_bet(self):

        '''
        If the bet has a bet_type:
            Calculates Profit,
            Edits the telegram message
            Saves the bet on excel
        '''

        if self.bet_type is None: return
        self.profit, self.result = calculate.profit(
            self.bet_type, self.handicap, self.total_score, self.bet_odd)
        self._edit_telegram_message()
        self._save_made_bet()
    
    def mark_processed(self):
        """Marca o processamento completo e identifica razões específicas de falha."""
        self.totally_processed = True
        reasons = []

        if self.bet_type is not None:
            # Verificar cada condição individualmente
            if not self.sent: 
                reasons.append("não foi enviado")
            if not self.edited:
                reasons.append("não foi editado")
            if not self.ended:
                reasons.append("não foi finalizado")
            if not self.saved_on_excel:
                reasons.append("não foi salvo no Excel")
            if self.profit is None:
                reasons.append("lucro não calculado")
            if self.result is None:
                reasons.append("resultado indefinido")
            if self.raw_score is None:
                reasons.append("placar bruto ausente")
        else:
            # Caso sem tipo de aposta
            if self.raw_score is None:
                reasons.append("placar bruto ausente")

        # Atualizar status e mostrar razões se houver falhas
        if reasons:
            self.totally_processed = False
            logger.error(f'Bet {self.home_str} vs {self.away_str} não processado. Motivos:')
            for i, reason in enumerate(reasons, 1):
                logger.error(f'{i}. {reason.capitalize()}')
        else:
            self.totally_processed = True

    def _update_from_event(self, event: dict):
        """Parse and clean event data with NaN handling"""
        cleaned_event = self._clean_data(event)
        self.event = cleaned_event
        
        # Parse dos dados do evento
        self.event_id = self._get_event_id()
        self.league_id = self._get_league_id()
        self.league = self._get_league()
        self.date = self._get_date()
        
        self.home_str = self._get_str('home')
        self.away_str = self._get_str('away')
        self.home_team = self._get_name('home', 'team')
        self.home_player = self._get_name('home', 'player')
        self.away_team = self._get_name('away', 'team')
        self.away_player = self._get_name('away', 'player')
        self.players = self._get_players()
 
    def update_from_dict(self, data: dict):
        """Safe update from dictionary with NaN cleaning"""
        cleaned_data = self._clean_data(data)
        for key, value in cleaned_data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _clean_data(self, data):
        """Recursively convert NaN/NaT/None to appropriate Python nulls"""
        if isinstance(data, dict):
            return {k: self._clean_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data(item) for item in data]
        elif pd.isna(data):
            return None if isinstance(data, float) else ''
        return data
    
    # ------------------------------------------- #

    def _edit_telegram_message(self):

        '''
        Updates Bet object with the new data
        Edits telegram message
        '''
        self._get_result_emoji()

        escaped_dict = {
            key: escape.markdown(value)
            for key, value 
            in self.__dict__.items()
            }
        
        self.message = escape.markdown(self.message)
        self.message += EDITED_MESSAGE.format(**escaped_dict, LINKS_MESSAGE=LINKS_MESSAGE)
        self.edited = message.edit(self.message_id, self.message, self.chat_id)

    def _get_bet_type(self, bet_type: str | None):
        
        """
        Gets Bet Type Object.
        Args:
            bet_type (str): Type of bet ('over'/'under'/'None')
        """

        self.bet_type = bet_type

    def _get_result_emoji(self):
        """Gets emoji for the result and bet type
        Assings it to object attributes"""
        self.result_emoji = RESULT_EMOJIS.get(self.result, '')

    def _get_bet_type_emoji(self):
        self.bet_type_emoji = BET_TYPE_EMOJIS.get(self.bet_type, '')
        
    def _get_date(self):
        timestamp = self.event.get('time')
        
        if timestamp:
            return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
 
    def _get_end(self):
        
        """
        Checks if the event has ended.
        If the event is not in live events, sets ended to True
        and calls _get_score() to fetch the final score.
        """

        live_events = fetch.live_events()

        live_ids = {str(event['id']) for event in live_events}
        
        if str(self.event_id) not in live_ids:
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
            logger.error("Error: Failed to get players for "
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
            logger.error("side or type is None while trying to get name")
            return None

        team_str = self.event.get(side, {}).get('name')
        
        if type == 'team':
            try:
                return team_str.split('(')[0].strip().lower()
            
            except Exception as e:
                logger.error(f"Error: {e}")
                return None
        
        if type == 'player':
            try:
                start = team_str.find('(') + 1
                end = team_str.find(')')
                return team_str[start:end].lower()
            
            except Exception as e:
                logger.error(f"Error: {e}")
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
        return self.total_score

    def _get_hot_tip(self) -> None:
        """Calculates 'hotness' level based on Expected Value."""

        if self.bet_ev < HOT_THRESHOLD:
            return

        above_th = self.bet_ev - HOT_THRESHOLD
        steps = int(above_th // HOT_TIPS_STEP)
        
        self.hot_ev = min(steps, MAX_HOT)
        self.hot_emoji = "🔥" * self.hot_ev

    def _get_time_attributes(self):
        """Sets all time-related atributes
        based on the current time"""

        current_tz = datetime.now().astimezone().tzinfo
        brasil_tz = ZoneInfo("America/Sao_Paulo")

        self.time_sent = pd.Timestamp.now()
        if current_tz != brasil_tz:
            self.time_sent -= pd.Timedelta(hours=AJUSTE_FUSO)

        self.month = self.time_sent.strftime("%m-%Y")
        hour = self.time_sent.hour

        for string_range, (start, end) in TIME_RANGES.items():
            if start <= hour <= end:
                self.time_range = string_range

    def _get_league(self) -> str:
        """Fetches league name from event data.
        If it fails, returns 'Unknown League'.
        """
        
        return LEAGUE_IDS[self.league_id]
    
    def _get_league_id(self) -> str:
        """Fetches league id from event data.
        If it fails, returns 'Unknown League Id'.
        """
        return self.event.get('league', {}).get('id', 'Unknow League Id')
    
    def _format_data(self, data) -> str:

        if isinstance(data, (datetime, pd.Timestamp)):
            return data.replace(second=0, microsecond=0)
        
        elif isinstance(data, float):
            return f'{data:.2f}'.replace('.', ',')
        
        elif isinstance(data, str):
            return f'{data}'.title().replace('_', ' ')

    def _get_excel_columns(self):
        """Returns a dcit with the columns and values
        To the Made Bets Excel file
        """
        return{
            'Horário Envio': self._format_data(pd.to_datetime(self.time_sent)),
            'Liga': self.league,
            'Partida': self.home_str + ' vs. ' + self.away_str,
            'Tipo Aposta': self._format_data(self.bet_type),
            'Hot Tips': self._format_data(self.hot_emoji),
            'Linha': self._format_data(self.handicap),
            'Resultado' : self._format_data(self.result),
            'Odd': self.bet_odd,
            'Lucro': self.profit,
            'Intervalo': self._format_data(self.time_range),
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

        if self.bet_type == 'over':
            self.bet_odd = self.odd_over
            self.bet_prob = self.prob_over
            self.bet_ev = self.ev_over
        
        elif self.bet_type == 'under':
            self.bet_odd = self.odd_under
            self.bet_prob = self.prob_under
            self.bet_ev = self.ev_under
    
    def _print_bet_data(self):
        """Log all bet data using the bet logger."""
        bet_logger = logging.getLogger('bet')
        
        
        log_message = f"""
        === New Bet ===
        Event ID: {self.event_id}
        Home: {self.home_player} ({self.home_team})
        Away: {self.away_player} ({self.away_team})
        League: {self.league}
        ---
        Line: {self.handicap}
        Lambda: {self.lambda_pred}
        ---
        Over Odd: {self.odd_over}
        Under Odd: {self.odd_under}
        Over Probability: {self.prob_over*100:.2f}%
        Under Probability: {self.prob_under*100:.2f}%
        ---
        Over EV: {self.ev_over*100:.2f}%
        Under EV: {self.ev_under*100:.2f}%
        """

        bet_logger.bet(log_message)
        if self.bet_type is None:
            bet_logger.bet('No +EV Bet Found')   

    def _find_min_line(self):
        """Finds and sets the minimum line and odd for the current bet type."""
        (self.minimum_line,
        self.minimum_odd) = calculate.min_goal_line(
            self.lambda_pred,
            self.handicap,
            self.bet_type,
            self.bet_prob
            )

    def _generate_message(self):
        
        """"
        If bet_type is none, breaks
        Creates and formats telegram message based
        on current object bet data
            if bet_type == None, break
        Looks at minimum line and hot tips data.
        If it exists, appends to the message.
        """
        self._get_bet_type_emoji()

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

    def _send_message(self):
        
        '''
        If bet time is not None, gets called
        Sends the message on telegram using message.send
        Marks self.sent as True or False, depending if it sent sucessfully
        Gets all time-related class objects
        '''
        
        self.message_id, self.chat_id = message.send(self.message)
        self._get_time_attributes()
        if self.message_id is None: self.sent = False
        else: self.sent = True

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
            logger.warning("Attempted to save match we didn't bet on. Skipped Sucessfully")
            return
        
        try:
            sheet_name = str(self.month).replace('/', '-')

            with pd.ExcelWriter(MADE_BETS, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                
                if str(self.month) in writer.book.sheetnames:
                    df_existing = pd.read_excel(MADE_BETS, sheet_name=sheet_name)
                
                else:
                    df_existing = pd.DataFrame(columns=self._get_excel_columns().keys())
                
                
                new_data = pd.DataFrame([self._get_excel_columns()])
                df_updated = pd.concat([df_existing, new_data], ignore_index=True)
                df_updated.to_excel(writer, sheet_name=sheet_name, index=False)

                logger.info(f"Saved bet {self.home_str + ' vs. ' + self.away_str} in xlsx.\nProfit: {self.profit}")

                self.saved_on_excel = True
                
        except FileNotFoundError:
            new_data = pd.DataFrame([self._get_excel_columns()])
            with pd.ExcelWriter(MADE_BETS, engine='openpyxl') as writer:
                new_data.to_excel(writer, sheet_name=sheet_name, index=False)
            self.saved_on_excel = True    

    # ---------------------------------------------------------------------------

