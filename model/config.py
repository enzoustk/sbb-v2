from model import calculate
from xgboost import XGBRegressor
from sklearn.metrics import make_scorer
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

custom_scorer = make_scorer(
    calculate.poisson_log_loss,
    greater_is_better=False
)

param_grid = {
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 4, 5],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'n_estimators': [500, 1000],
    'reg_alpha': [0, 0.1, 0.5],  
    'reg_lambda': [0, 0.1, 0.5],
    'min_child_weight': [1, 5, 10]
}

model = XGBRegressor(
    objective='count:poisson',
    eval_metric='poisson-nloglik',
)

tscv =  TimeSeriesSplit(n_splits=5)

grid_search = GridSearchCV(
    estimator=model,
    param_grid=param_grid,
    scoring=custom_scorer,
    cv=tscv,
    n_jobs=-1,
    verbose=2
)