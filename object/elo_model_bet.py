from bet import Bet

class EloModelBet(Bet):
    def __init__(self, event:dict):
        super().__init__()

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

        self.odd_home = None 
        self.odd_away = None
        self.odd_draw = None
        
        self.prob_home = None
        self.prob_away = None
        self.prob_draw = None

        self.ev_home = None
        self.ev_away = None
        self.ev_draw = None

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