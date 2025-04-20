import os
import logging
import pandas as pd

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from files.paths import MADE_BETS, MADE_BETS_MD, LOCK, MAIN_CONTEXT_TXT

def save_markdown(file: str = MADE_BETS_MD):
    """Saves the made bets xlsx to a model-readable markdown file."""

    try:
        df = pd.read_excel(MADE_BETS)
        print('Tentando Ler df ', df)
        df.to_markdown(MADE_BETS_MD)
    except Exception as e:
        print('Error Loading File', e)

def get_markdown(file: str = MADE_BETS_MD):
    """Loads Markdown data (Creates MD file if needed)"""
    if not os.path.exists(file):
        save_markdown(file=file)
    
    with open(file, "r", encoding="utf-8") as f:
        return f.read()
    
def get_txt(file: str = MAIN_CONTEXT_TXT):
    try:
        with open(file, "r",) as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f'Error getting txt: File {file} not found')
    

