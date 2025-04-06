from filelock import FileLock

# Data used to calculate features and train model
HISTORIC_DATA = r'files\sheets\game_data.csv'

#All matches we betted on
MADE_BETS = r'files\sheets\bets.xlsx'

# All analised matches
ALL_DATA = r'files\sheets\all_data.csv'
NOT_ENDED = r'files\sheets\not_ended.csv'
ERROR_EVENTS = r'files\sheets\error_events.csv'

LOCK = r'files\sheets.lock'