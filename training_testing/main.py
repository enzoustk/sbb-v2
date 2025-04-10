import numpy as np
import pandas as pd
from features import create
from model import calculate
from model.config import grid_search
from utils.utils import print_separator
from features.required import REQUIRED_FEATURES
from sklearn.metrics import mean_absolute_error, mean_squared_error


df = pd.read_csv(r'training_testing\dados\dados_eventos.csv')
df = df.sort_values(by='date')

train_size = int(0.7 * len(df))
test_size = int(0.2 * len(df))
train_df = df.iloc[:train_size]
test_df = df.iloc[train_size:train_size + test_size]
val_df = df.iloc[train_size + test_size:]

train_featured = create.features(
    data=train_df,live=False
    ).dropna()

test_featured = create.features(
    data=test_df, live=False, 
    lookback_data=train_df
    ).dropna()

val_featured = create.features(
    data=val_df, live=False, 
    lookback_data=pd.concat(
        [train_df, test_df])
        ).dropna()


# --------------------------------------------------------------- #

train_X = train_featured[REQUIRED_FEATURES]
train_y = train_featured['gols_totais']

test_X = test_featured[REQUIRED_FEATURES]
test_y = test_featured['gols_totais']

val_X = val_featured[REQUIRED_FEATURES]
val_y = val_featured['gols_totais']

# --------------------------------------------------------------- #


grid_search.fit(train_X, train_y)
best_model = grid_search.best_estimator_

# Avaliação
test_pred = best_model.predict(test_X)
val_pred = best_model.predict(val_X)

print_separator()
print('Teste:')
print(f"MAE: {mean_absolute_error(test_y, test_pred):.4f}")
print(f"RMSE: {np.sqrt(mean_squared_error(test_y, test_pred)):.4f}")
print(f"Log Loss: {calculate.poisson_log_loss(test_y, test_pred):.4f}")

print_separator()
print('Validação:')
print(f"MAE: {mean_absolute_error(val_y, val_pred):.4f}")
print(f"RMSE: {np.sqrt(mean_squared_error(val_y, val_pred)):.4f}")
print(f"Log Loss: {calculate.poisson_log_loss(val_y, val_pred):.4f}")