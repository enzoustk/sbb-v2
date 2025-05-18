import numpy as np
import pandas as pd
from config import *
import seaborn as sns
import logging
import matplotlib.pyplot as plt
from xgboost import XGBRegressor, plot_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error

from features import features


df = pd.read_csv('22614/model/database.csv')
df['date'] = pd.to_datetime(df['date'])
print(df.head())
# df = df.drop_duplicates()
# df = df.dropna()

df = df.sort_values(by='date')

df_featured = features(data=df,live=False)
print(df_featured.head())

"""
df = df[df['date'] >= '2025-03-01']

train_size = int(0.6 * len(df))
val_size = int(0.2 * len(df))

train_df = df.iloc[:train_size]
val_df = df.iloc[train_size:train_size + val_size]
test_df = df.iloc[train_size + val_size:]

lookback_val = train_df
lookback_test = df.iloc[:len(test_df)]

#--------------------------------------------------#

train_featured = features(
    data=train_df,live=False
    ).dropna()

val_featured = features(
    data=val_df, live=False, 
    lookback_data=train_df
    ).dropna()

test_featured = features(
    data=test_df, live=False, 
    lookback_data=lookback_test
    ).dropna()

#--------------------------------------------------#

train_X = train_featured.drop(columns=COLUMNS_DROP)
train_y = train_featured['total_score']

val_X = test_featured.drop(columns=COLUMNS_DROP)
val_y = test_featured['total_score']

test_X = val_featured.drop(columns=COLUMNS_DROP)
test_y = val_featured['total_score']

val_X_1, val_X_2 = val_X[:len(val_X)//2], val_X[len(val_X)//2:]
val_y_1, val_y_2 = val_y[:len(val_y)//2], val_y[len(val_y)//2:]

final_train_X = pd.concat([train_X, val_X_1])
final_train_y = pd.concat([train_y, val_y_1])

#--------------------------------------------------#

corr_matrix = train_featured.drop(columns=["event_id", "date"]).select_dtypes(include=np.number).corr(method="pearson")

plt.figure(figsize=(9, 5))
sns.heatmap(
    corr_matrix, 
    annot=False, 
    cmap="coolwarm", 
    vmin=-1, 
    vmax=1,
    mask=np.triu(np.ones_like(corr_matrix, dtype=bool))
)
plt.title("Correlation Matrix")
plt.show()

#--------------------------------------------------#

random_search.fit(
    train_X, train_y,
    #sample_weight=pesos_treinamento,
    eval_set=[(val_X_1, val_y_1)],
    verbose=2
)

best_random_model = random_search.best_estimator_
best_random_params = random_search.best_params_

final_random_model = XGBRegressor(
    **best_random_params,
    objective='count:poisson',
    eval_metric='poisson-nloglik',
    tree_method='hist',
    early_stopping_rounds=50,
    random_state=42
)


final_random_model.fit(
    final_train_X, final_train_y,
    eval_set=[(val_X_2,val_y_2)],
    verbose=10
)

test_pred_random_model = final_random_model.predict(test_X)


print(60 * '-')
print('Teste:')
print(f"MAE: {mean_absolute_error(test_y, test_pred_random_model):.4f}")
print(f"RMSE: {np.sqrt(mean_squared_error(test_y, test_pred_random_model)):.4f}")
print(f"Log Loss: {poisson_log_loss(test_y, test_pred_random_model):.4f}")

plot_importance(final_random_model,max_num_features=50)
plt.show()

from pprint import pprint

print(60 * '-')
print('Parametros Escolhidos:')
pprint(best_random_params)
print(60 * '-')
"""
