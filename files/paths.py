from filelock import FileLock

#All matches we betted on
MADE_BETS = r'files\sheets\bets.xlsx'
MADE_BETS_MD = r'files\sheets\bets_md.md'
MAIN_CONTEXT_TXT = r'files\context\main_context.txt'

# All analised matches
NOT_ENDED = r'files\sheets\not_ended.csv'
ERROR_EVENTS = r'files\sheets\error_events.csv'

LOCK = FileLock(r'files\sheets\.lock')

MODELS = {
    '22614': {
        'model': r'files\model\model_22614.json',
        'historic_data': r'files\sheets\data_22614.csv'
    },
    '23114': {
        'model': r'files\model\model_23114.json',
        'historic_data': r'files\sheets\data_23114.csv'
    },
    '38439': {
        'model': r'files\model\model_38439.json',
        'historic_data': r'files\sheets\data_38439.csv'
    },
    '37298': {
        'model': r'files\model\model_37298.json',
        'historic_data': r'files\sheets\data_37298.csv'
    },
}