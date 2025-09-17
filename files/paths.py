import os
from filelock import FileLock

# All matches we betted on
MADE_BETS = os.path.join("files", "sheets", "bets.xlsx")
MADE_BETS_MD = os.path.join("files", "sheets", "bets_md.md")
MAIN_CONTEXT_TXT = os.path.join("files", "context", "main_context.txt")

# All analysed matches
NOT_ENDED = os.path.join("files", "sheets", "not_ended.csv")
ERROR_EVENTS = os.path.join("files", "sheets", "error_events.csv")

LOCK = FileLock(os.path.join("files", "sheets", ".lock"))

MODELS = {
    '22614': {
        'model': os.path.join("files", "model", "model_22614.json"),
        'scaler': os.path.join("files", "scaler", "scaler_22614.pkl"),
        'historic_data': os.path.join("files", "sheets", "data_22614.csv"),
    },
}
