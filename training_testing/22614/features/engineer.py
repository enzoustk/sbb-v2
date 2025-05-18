import pandas as pd
import numpy as np

class FeatureEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        