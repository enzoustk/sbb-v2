class Bet:
    
    """
    All Bet-related data, methods and attributes.
    TODO: Create a subset to bet exported in xlsx
    TODO: Create cancel method to cancel a made bet
    TODO: Create a way to delete Bet Objetcts that are no longer needed to be stored
    """

    def __init__(self, event: dict):
        # Starts Class - Needs event data to do so.
        
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

        self.message = None
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
    
    def get_odds(self, market: str='goals'):
        from api_requests import fetch, validate

        """
        Pulls betting odds and handicaps from API
        Params:
            Market: betting market
        TODO: Handle Different markets and variables, such as Asian Handicap or The Draw
        """
                
        betting_data = fetch.odds(self.event_id)
        
        (self.handicap,
         self.odd_over,
         self.odd_under
         ) = validate.odds(betting_data, self.event_id, market=market)
                                        
    def find_ev(self, lambda_pred: float):
        from model.config import EV_THRESHOLD
        from model import calculate

        """
        Calculate bet probabilities using calculate.poisson
        Calculate ev for possible bets using calculate.ev
        If ev > EV_THRESHOLD -> Return bet_type and bet_data;
        Else: return None;
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
        import json, threading
        from files.paths import NOT_ENDED

        try:
            with open(NOT_ENDED, 'r') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(self.__dict__)

        with open(NOT_ENDED, 'w') as file:
            json.dump(data, file, indent=4)
    
    def handle_not_ended_events(self):
        import json, logging, pandas as pd, threading
        from files.paths import ALL_DATA, NOT_ENDED, ERROR_EVENTS
       
        not_ended, ended, error_events = [], [], []

        try:
            with open(NOT_ENDED, 'r') as file:
                data = json.load(file)
                
                
                """
                Ver se acabou;
                Se acabou:
                     puxar resultado, e calcular tudo
                    Salvar em all_data.csv
                    Se bet_type != None, salvar em made_bets.xlsx usando as colunas corretas
                    Apagar de not_ended
                Se não acabou
                    Pular
                """
                for bet_data in data:
                    bet = Bet()
                    bet.__dict__.update(bet_data)
                    bet._get_end()

                    if  bet.ended:
                        bet.finish_processing()


                    if bet.totally_processed: 
                        ended.append(bet)
                    
                    elif not bet.totally_processed: 
                        error_events.append(bet)

                    elif bet.totally_processed is None:
                        not_ended.append(bet)

                    else: 
                        logging.warning(f'Tottaly Processing: Labeling Error for Event {bet.event_id}')

            with open(NOT_ENDED, 'w') as not_ended_file:
                not_ended_data = [bet.__dict__ for bet in not_ended]
                json.dump(not_ended_data, not_ended_file, indent=4)
            
            with open(ALL_DATA, 'a') as all_data_file:
                ended_data = [bet.__dict__ for bet in ended]
                json.dump(ended_data, all_data_file, indent=4)
            
            with open(ERROR_EVENTS, 'a') as error_events_file:
                error_events_data = [bet.__dict__ for bet in error_events]
                json.dump(error_events_data, error_events_file, indent=4)
    
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error(f"Error loading data from {NOT_ENDED}")
            
    def finish_processing(self):
                from model import calculate
                """
                Calcula tudo o que falta.
                Se alguma coisa der errado, marca totally_processed como false.
                TODO: Colocar try except em todos os métodos abaixo
                """
                if self.bet_type is not None:
                    self.profit, self.result = calculate.profit(self.bet_type, self.handicap, self.total_score, self.bet_odd)
                    self._edit_telegram_message()
                    self._save_made_bet()
                    self._mark_processed()
    
    def to_historic_file(self):
        from files.paths import HISTORIC_DATA
        
        '''
        Recieves data and exports it to csv file


        TODO: Finish it
        '''



        exclude_keys = self._remove_collumns_to_csv
        dte = {k: v for k, v in self.__dict__.items() if k not in exclude_keys} # dte = dictionary to export



    # ------------------------------------------- #


    def _edit_telegram_message(self):
        from constants.telegram_params import EDITED_MESSAGE
        from telegram.message import edit
        '''
        Recebe os dados da Aposta e Edita no Telegram
        '''

        self._get_bet_emojis()
        self.message += EDITED_MESSAGE.format(**self.__dict__)
        self._escape()
        self.edited = edit(self.message_id, self.message, self.chat_id)

    def _get_bet_type(self, bet_type: str | None):
        """
        Gets Bet Type Object.
        Possible Types: 'over', 'under', None
        """

        self.bet_type = bet_type

    def _escape(self):
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
        from constants.telegram_params import RESULT_EMOJIS, BET_TYPE_EMOJIS

        self.result_emoji = RESULT_EMOJIS.get(self.result, '')
        self.bet_type_emoji = BET_TYPE_EMOJIS.get(self.bet_type, '')
    
    def _get_end(self):
        from api_requests import fetch
        
        """
        Procura pelo fim do jogo
        Se não está mais ao vivo, procura pelo placar
        Se acha placar, Marca ended como True
        Se
        """

        live_events = fetch.live_events()

        live_ids = {str(event['id']) for event in live_events}

        if self.event_id not in live_ids:
            if self._get_score() is not None:
                self.ended = True
  
    def _get_event_id(self) -> str:
        return self.event['id']

    def _get_str(self, type: str) -> str:
        return self.event.get(type, {}).get('name')
        
    def _get_players(self) -> tuple[str, str]:
        try:
            home = str(self.home_player).lower()
            away = str(self.away_player).lower()
            return tuple(sorted([home, away]))
        except:
            return ('', '')

    def _get_name(
                self, 
                side: str | None = None,
                type: str | None = None,
                ) -> str | None:
    
        if side is None:
            import logging
            logging.error("Error: side is None")
            return None
        
        if type is None:
            import logging
            logging.error("Error: you must provide a name")
            return None
        
        """
        Gets team_str: 'Barcelona (Player_Name) Esports'
        if type=team, Returns: 'Barcelona'
        if type=player, Returns: 'Player_Name'
        """

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
        from api_requests.fetch import event_for_id
        """
        Pull result data from API,
        If raw_score = None, breaks out
        If raw_score != None, gets home, away and total scores
        """


        event_data = event_for_id(self.event_id)

        self.raw_score = event_data.get('ss', None)
        
        if self.raw_score is None:
            return
        
        self.home_score, self.away_score = map(int, self.raw_score.split('-'))
        self.total_score = self.home_score + self.away_score

    def _get_hot_tip(self):
        from model.config import (HOT_THRESHOLD, HOT_TIPS_STEP, MAX_HOT)
        
        if self.bet_ev >= HOT_THRESHOLD:
            _ev = self.bet_ev
            self.hot_ev = 0
            
            while True:

                if self.hot_ev == MAX_HOT:
                    break 

                if _ev >= HOT_THRESHOLD:
                    self.hot_emoji += "🔥"
                    _ev -= HOT_TIPS_STEP
                    self.hot_ev += 1

    def _get_time_atributes(self):
        import pandas as pd
        from model.config import TIME_RANGES, AJUSTE_FUSO

        self.time_sent = pd.Timestamp.now() - pd.Timedelta(hours=AJUSTE_FUSO)
        self.month = self.time_sent.strftime("%m/%Y")
        hour = self.time_sent.hour

        for range, (start, end) in TIME_RANGES.items():
            if start <= hour <= end:
                self.time_range = range

    def _get_league(self) -> str:
        return self.event.get('league', {}).get('name', 'Unknown League')
    
    def _get_excel_columns(self):
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

    def _remove_collumns_to_csv(self):
        return {'event', 'hot_emoji', 'message', 'bet_type_emoji'}
    
    def _get_lambda_pred(self, lambda_pred: float):
        self.lambda_pred = lambda_pred
     
    def _get_bet_type(self, bet_type: str | None = None):
        
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
        """
        Print the event data;
        Print Betting data, such as EV, Probabilities and Bet.
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
        from model import calculate
        self.minimum_line, self.minimum_odd = calculate.min_goal_line(self.handicap, self.bet_type, self.bet_prob)

    def _generate_message(self):
        
        from constants.telegram_params import TELEGRAM_MESSAGE, MIN_LINE_MESSAGE, MIN_ODD_MESSAGE, HOT_TIPS_MESSAGE
        
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

        from telegram import message
        
        self.message_id, self.chat_id = message.send(self.message)
        self._get_time_atributes()
        if self.message_id is None: self.sent = False
        
    def _mark_processed(self):
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
      
    def _save_made_bet(self):
        from files.paths import MADE_BETS
        import pandas as pd

        if self.bet_type is None:
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
    
    def cancel(self):
        pass