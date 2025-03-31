import pandas as pd
from data import load
from datetime import datetime
from telegram.constants import (
    REPORT_TITLE, REPORT_BODY, REPORT_TOTAL,
    REPORT_TIME_RANGE_TITLE, REPORT_TIME_RANGE_BODY
)

class Report():
    def __init__(self, 
            df: pd.DataFrame | None,
            start_date: str | None = None,
            end_date: str | None = None,
            ev_type: str | None = None,
            league: str | None = None,
            ):
        

        if df is None:
            self.df = load.xlsx(
                start_date=start_date,
                end_date=end_date,
                ev_type=ev_type,
                league=league
            )

        self.report_type = None
        self.message = ''

        
    def build_daily(self):
        self.report_type = 'daily'



        




    def _get_title(self):
        if self.report_type == 'daily':
            
            self.message += REPORT_TITLE.format()
       

    def _get_body(self):
        pass

    def _get_info(self):
        pass