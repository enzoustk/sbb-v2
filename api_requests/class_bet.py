class Bet:
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

        self.bet_type = None
        self.odd = None
        self.prob = None
        self.ev = None
        self.minimum_line = None
        self.minimum_odd = None
        self.time_sent = None
        self.lambda_pred = None

    def _get_league(self) -> str:
        return self.event.get('league', {}).get('name', 'Unknown League')

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
    
    def print_data(self) -> None:
        """
        Print the event data
        """
        print(f"League: {self.league}")
        print(f"{self.home_player} ({self.home_team}) vs {self.away_player} ({self.away_team})")
        print('-' * 20)
        print(f"Line: {self.handicap}")

    def validate(self, bet_type: str | None) -> bool:
        self.bet_type = bet_type
        
    
    def lambda_pred(self, lambda_pred: float):
        self.lambda_pred = lambda_pred
        

    def calculate_probabilities(self, lambda_pred: float) -> tuple[str, float, float, float] | None:
        from model.calculate import poisson
        from model.config import EV_THRESHOLD

        """
        Calcular probabilidades e EV;
        Retornar probabilidades e EV caso seja maior que o threshold;
        Retornar None caso não seja maior que o threshold;
        Imprimir dados do evento;
        """

        self.prob_over, self.prob_under = poisson(lambda_pred, self.handicap)
        self.ev_over = self.odd_over * self.prob_over - 1
        self.ev_under = self.odd_under * self.prob_under -1
        
        print(f"Lambda: {lambda_pred}")
        print('-' * 20)
        print(f"Probabilidade Over: {self.prob_over*100:.2f}%")
        print(f"Probabilidade Under: {self.prob_over*100:.2f}%")
        print(f"EV Over: {self.ev_over*100:.2f}%")
        print(f"EV Under: {self.ev_under*100:.2f}%")
        print('-' * 60)

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
            print('Não há EV')
            return None

    def poisson(self, lambda_pred: float) -> tuple[float, float]:

        from scipy.stats import poisson

        """
        Calcula a probabilidade dado um handicap.
        TODO: Ajustar para possibilitar uso de outros mercados.
        """
        
        if self.handicap % 1 == 0.5:  # Handicap terminado em 0.5
            self.prob_over = 1 - poisson.cdf(int(self.handicap), lambda_pred)
            self.prob_under = poisson.cdf(int(self.handicap), lambda_pred)

        elif self.handicap % 1 == 0.0:  # Handicap inteiro
            prob_over_raw = 1 - poisson.cdf(int(self.handicap), lambda_pred)
            prob_under_raw = poisson.cdf(int(self.handicap) - 1, lambda_pred)
            total = prob_over_raw + prob_under_raw
            self.prob_over = prob_over_raw / total
            self.prob_under = prob_under_raw / total

        elif self.handicap % 1 in [0.25, 0.75]:  # Handicap terminado em 0.25 ou 0.75
            lower = self.handicap - 0.25
            upper = self.handicap + 0.25
            prob_over_lower, prob_under_lower = poisson(lambda_pred, lower)
            prob_over_upper, prob_under_upper = poisson(lambda_pred, upper)
            self.prob_over = (prob_over_lower + prob_over_upper) / 2
            self.prob_under = (prob_under_lower + prob_under_upper) / 2

        else:
            raise ValueError(f"Handicap inválido: {self.handicap}")
        
        return self.prob_over, self.prob_under

           



            