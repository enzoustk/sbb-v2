from filelock import FileLock

# Data used to calculate features and train model
HISTORIC_DATA = r'files\sheets\game_data.csv'

#All matches we betted on
MADE_BETS = r'files\sheets\bets.xlsx'

# All analised matches
NOT_ENDED = r'files\sheets\not_ended.csv'
ERROR_EVENTS = r'files\sheets\error_events.csv'

LOCK = FileLock('files\sheets\.lock')

MODEL_PATH = r'files\model\sbb_model.json'
