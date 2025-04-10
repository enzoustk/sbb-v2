import pandas as pd

@pd.api.extensions.register_dataframe_accessor("h2h")
class H2HAccessor:
    def __init__(self, df):
        self._df = df
        self._grouped = df.groupby('matchup_key', group_keys=False)

    def __getattr__(self, attr):
        # Verifica se é uma coluna do DataFrame e retorna o groupby correspondente
        if attr in self._df.columns:
            return self._grouped[attr]
        # Se não for uma coluna, levanta AttributeError
        raise AttributeError(f"'{self.__class__.__name__}' não possui o atributo '{attr}'")
    
    def cumcount(self):
        return self._grouped.cumcount()