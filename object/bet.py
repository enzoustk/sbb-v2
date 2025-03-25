class Bet:
    """
    All Bet-related data, methods and attributes.
    TODO: Create a subset to bet exported in xlsx
    TODO: Create a way to delete Bets that are no longer needed to be stored
    """

    def __init__(self, event: dict):
        # Starts Class - Needs event data to do so.
        
        self.event = event

        self.home_str = self._get_str('home')
        self.away_str = self._get_str('away')

        self.home_team = self._get_name('home', 'team')
        self.home_player = self._get_name('home', 'player')
        self.away_team = self._get_name('away', 'team')
        self.away_player = self._get_name('away', 'player')

        self.players = self._get_players()

        self.odd_over = float(event['over_od'])
        self.odd_under = float(event['under_od'])

        self.handicap = self._handle_handicap()
        self.league = self._get_league()
        self.event_id = self._get_event_id()

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
        self.canceled = False

        self.sent = False
        self.message_id = None
        self.chat_id = None
        self.edited = False
        self.result_emoji = None
        self.bet_type_emoji = None
        self.time_interval = None

        self.saved_on_excel = False
        self.totally_processed = None
      
    def print_event_data(self) -> None:
        """
        Print the event data
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
            print(f'Aposta: {self.bet_type} {self.handicap} @{self.bet_odd}')
            print(f'Minimum Line: {self.minimum_line} @{self.minimum_odd}')
            print(f'Hot Tip: {self.hot_ev}')
        if self.bet_type is None: 
            print('Não há EV+ nessa partida')

    def validate(self, bet_type: str | None) -> bool:
        self.bet_type = bet_type
        
    def get_lambda_pred(self, lambda_pred: float):
        self.lambda_pred = lambda_pred
        
    def calculate_probabilities(self) -> tuple[str, float, float, float] | None:
        from model.config import EV_THRESHOLD

        """
        Calcular probabilidades e EV;
        Retornar probabilidades e EV caso seja maior que o threshold;
        Retornar None caso não seja maior que o threshold;
        Imprimir dados do evento;
        """
        

        self.prob_over, self.prob_under = self.poisson(self.lambda_pred, self.handicap)
        self.ev_over = self.odd_over * self.prob_over - 1
        self.ev_under = self.odd_under * self.prob_under -1

        self.print_event_data()

        if self.ev_over >= EV_THRESHOLD:
            self.bet_type = 'over'
            self.bet_odd = self.odd_over
            self.bet_prob = self.prob_over
            self.bet_ev = self.ev_over
        
        elif self.ev_under >= EV_THRESHOLD:
            self.bet_type = 'under'
            self.bet_odd = self.odd_under
            self.bet_prob = self.prob_under
            self.bet_ev = self.ev_under
        
        else:
            print('No EV+ Bet Found')
            return None

    def poisson(self) -> tuple[float, float]:

        from scipy.stats import poisson

        """
        Calcula a probabilidade dado um handicap.
        TODO: Ajustar para possibilitar uso de outros mercados.
        """
        
        if self.handicap % 1 == 0.5:  # Handicap terminado em 0.5
            self.prob_over = 1 - poisson.cdf(int(self.handicap), self.lambda_pred)
            self.prob_under = poisson.cdf(int(self.handicap), self.lambda_pred)

        elif self.handicap % 1 == 0.0:  # Handicap inteiro
            prob_over_raw = 1 - poisson.cdf(int(self.handicap), self.lambda_pred)
            prob_under_raw = poisson.cdf(int(self.handicap) - 1, self.lambda_pred)
            total = prob_over_raw + prob_under_raw
            self.prob_over = prob_over_raw / total
            self.prob_under = prob_under_raw / total

        elif self.handicap % 1 in [0.25, 0.75]:  # Handicap terminado em 0.25 ou 0.75
            lower = self.handicap - 0.25
            upper = self.handicap + 0.25
            prob_over_lower, prob_under_lower = poisson(self.lambda_pred, lower)
            prob_over_upper, prob_under_upper = poisson(self.lambda_pred, upper)
            self.prob_over = (prob_over_lower + prob_over_upper) / 2
            self.prob_under = (prob_under_lower + prob_under_upper) / 2

        else:
            raise ValueError(f"Handicap inválido: {self.handicap}")
        
        return self.prob_over, self.prob_under

    def calculate_minimum(self) -> tuple[float, float]:
        
        """
        Calcular a odd EV == threshold para a linha atual,
        Se a odd mínima for inferior a 1.75, 'piorar' a linha em 0.25
        Repetir até que a odd mínima seja superior a 1.75
        """

        self.minimum_line = self.handicap

        if self.bet_type.lower() == 'over': 
            step = 0.25
        elif self.bet_type.lower() == 'under': 
            step = -0.25
        else: 
            raise ValueError(f"Tipo de aposta inválido: {self.bet_type}")

        while True:
            from model.config import EV_THRESHOLD
            self.prob_over, self.prob_under = self.poisson()

            if self.bet_type.lower() == 'over': self.prob = self.prob_over
            elif self.bet_type.lower() == 'under': self.prob = self.prob_under
            else: raise ValueError(f"Tipo de aposta inválido: {self.bet_type}")

            self.minimum_odd = ((1.0 + EV_THRESHOLD) / self.bet_prob).round(2)

            if self.minimum_odd >= 1.75:
                return self.minimum_line, self.minimum_odd

            elif self.minimum_odd < 1.75: self.minimum_line += step

            else: raise ValueError(f"Odd mínima inválida: {self.minimum_odd}")

    def calculate_profit(self) -> float:
        
        """
        Calcular o PL dado um tipo de aposta, handicap, odd e resultado.
        TODO: Permitir outros mercados.
        TODO: Permitir stake variável.
        """

        if self.bet_type.lower() == 'over': outcome = self.total_score - self.handicap
        elif self.bet_type.lower() == 'under': outcome = self.handicap - self.total_score
        
        else:
            raise ValueError("Tipo de aposta deve ser 'over' ou 'under'")

        if outcome >= 0.5: 
            self.profit = (self.bet_odd - 1)
            self.result = 'win' 
        elif outcome == 0.25: 
            self.profit = (self.bet_odd - 1) / 2
            self.result = 'half_win'
        elif outcome == 0: 
            self.profit = 0
            self.result = 'push'
        elif outcome == -0.25:
            self.profit = -0.5 
            self.result = 'half_loss'
        elif outcome <= -0.5: 
            self.profit -1
            self.result = 'loss'
        
        else: 
            raise ValueError(f"Ajuste de resultado inválido: {outcome}")
    
    def generate_and_send_message(self):
        from constants.telegram_params import TELEGRAM_MESSAGE
        from telegram import message
        
        self.message = TELEGRAM_MESSAGE.format(**self.__dict__)
        self.implement_minimum_in_message()
        self.implement_hot_tips()

        if self.bet_type is not None:
            self.message_id, self.chat_id = message.send(self.message)
        
        if self.message_id is not None:
            self.sent = True
            self._get_time_atributes()
  
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

    def process_not_ended(self):
        import json, logging, pandas as pd, threading
        from files.paths import MADE_BETS, ALL_DATA, NOT_ENDED
       
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
                for bet_entry in data:
                    bet = Bet()
                    bet.__dict__.update(bet)
                    bet._get_end()

                    if  bet.ended:
                        bet.finish_processing()
                        bet.save_made_bet()
                        bet.process()

                    if bet.totally_processed == True: ended.append(bet)
                    elif bet.totally_processed == False: error_events.append(bet)
                    elif bet.totally_processed == None: not_ended.append(bet)
                    else: logging.warning(f'Tottaly Processing: Labeling Error for Event {bet.event_id}')

            with open(NOT_ENDED, 'w') as not_ended_file:
                not_ended_data = [bet.__dict__ for bet in not_ended]
                json.dump(not_ended_data, not_ended_file, indent=4)
            
            with open(ALL_DATA, 'a') as all_data_file:
                ended_data = [bet.__dict__ for bet in ended]
                json.dump(ended_data, all_data_file, indent=4)
    
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error(f"Error loading data from {NOT_ENDED}")
        
    def save_made_bet(self):
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
                
        except FileNotFoundError:
            new_data = pd.DataFrame([self._get_excel_columns()])
            with pd.ExcelWriter(MADE_BETS, engine='openpyxl') as writer:
                new_data.to_excel(writer, sheet_name=str(self.month), index=False)
                
    def finish_processing(self):
                """
                Calcula tudo o que falta.
                Se alguma coisa der errado, marca totally_processed como false.
                TODO: Colocar try except em todos os métodos abaixo
                """
                if self.bet_type is not None:
                    self.calculate_profit()
                    self.edit_telegram_message()

    def process(self):
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
                                
    def edit_telegram_message(self):
        from constants.telegram_params import EDITED_MESSAGE
        from telegram.message import edit
        '''
        Recebe os dados da Aposta e Edita no Telegram
        '''

        self._get_bet_emojis()
        self.message += EDITED_MESSAGE.format(**self.__dict__)
        self._escape()
        self.edited = edit(self.message_id, self.message, self.chat_id)

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
        
    def _handle_handicap(self) -> float | None:
        
        import logging
    
        """
        Gets the handicap from the API and solves type errors,
        Also, converts it to a float and returns the current handicap if successful.
        """
        handicap = self.event['handicap']

        try:
            if isinstance(handicap, float): return handicap
            
            if isinstance(handicap, str):
                if ',' in handicap:
                    handicap_vals = [float(h.strip()) for h in handicap.split(',')]
                    current_handicap = sum(handicap_vals) / len(handicap_vals)
                else:
                    current_handicap = float(handicap.strip())
                return current_handicap
            
            else:
                logging.error(f"Invalid Handicap or Handicap type: {type(handicap)} - Value: {handicap}")
                return None
        
        except ValueError as ve:
            logging.error(f"Error converting handicap '{handicap}': {ve}")
            return None
    
    def _get_players(self) -> tuple[str, str]:
        try:
            home = str(self.home_player).lower()
            away = str(self.away_player).lower()
            return tuple(sorted([home, away]))
        except:
            return ('', '')

    def _get_name(
                self, 
                side: str,
                type: str,
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
    
    def _implement_minimum_in_message(self):
        from constants.telegram_params import MIN_LINE_MESSAGE,MIN_ODD_MESSAGE

        if self.minimum_line == self.handicap and self.minimum_odd != self.bet_odd:
            self.message += MIN_ODD_MESSAGE.format(**self.__dict__)
        
        elif self.minimum_line != self.handicap:
            self.message += MIN_LINE_MESSAGE.format(**self.__dict__)

    def _implement_hot_tips(self):
        from model.config import (HOT_THRESHOLD, HOT_TIPS_STEP, MAX_HOT, HOT_TIPS_MESSAGE)
        
        _ev = self.bet_ev
        self.hot_ev = 0
        
        if _ev >= HOT_THRESHOLD: 
            while True:
                if _ev >= HOT_THRESHOLD:
                    self.hot_emoji += "🔥"
                    _ev -= HOT_TIPS_STEP
                    self.hot_ev += 1
                
                if self.hot_ev == MAX_HOT: 
                    self.message += HOT_TIPS_MESSAGE.format(**self.__dict__)
                    break
                
                else:
                    self.message += HOT_TIPS_MESSAGE.format(**self.__dict__)
                    break

    def _get_time_atributes(self):
        import pandas as pd
        from model.config import TIME_RANGES

        self.time_sent = pd.Timestamp.now() - pd.Timedelta(hours=3)
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
            'Linha': f'{self.line:2f}',
            'Resultado' : self.result.replace('_', ' ').capitalize(),
            'Odd': f'{self.odds:2f}',
            'Lucro': f'{self.profit:2f}',
            'Intervalo': self.time_range,
        }

    def cancel(self):
        pass