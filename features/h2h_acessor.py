"""Class Method to create a custom accessor for the DataFrame class."""

import pandas as pd

@pd.api.extensions.register_dataframe_accessor("h2h")
class H2HAccessor:
    def __init__(self, df):
        self._df = df
        self._grouped = df.groupby('matchup_key', group_keys=False)

    def __getattr__(self, attr):
        if attr in self._df.columns:
            return self._grouped[attr]
        raise AttributeError(f"'{self.__class__.__name__}' não possui o atributo '{attr}'")