import os
import pandas as pd

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from files.paths import MADE_BETS, MADE_BETS_MD, LOCK

def save_markdown(file: str = MADE_BETS_MD):
    """Saves the made bets xlsx to a model-readable markdown file."""
    with LOCK:
        df = pd.read_excel(MADE_BETS)
        with open(file, "w", encoding="utf-8") as f:
            f.write(df.to_markdown(index=False))

def get_markdown(file: str = MADE_BETS_MD) -> str:
    """Loads Markdown data (Creates it if needed)"""
    if not os.path.exists(file):
        save_markdown(file=file)
    
    with open(file, "r", encoding="utf-8") as f:
        return f.read()
    

