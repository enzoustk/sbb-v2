import numpy as np
from scipy import stats
from scipy.stats import poisson
from xgboost import XGBRegressor
from sklearn.metrics import make_scorer
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, RandomizedSearchCV

def poisson_log_loss(y_true, y_pred):

    prob = np.array([poisson.pmf(k, y_pred) for k in y_true])
    return -np.mean(np.log(prob + 1e-10)) 


custom_scorer = make_scorer(
    poisson_log_loss,
    greater_is_better=False
)

param_grid = {
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 4, 5],
    'subsample': [0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'n_estimators': [500, 1000],
    'reg_alpha': [0, 0.1, 0.5],  
    'reg_lambda': [0, 0.1, 0.5],
    'min_child_weight': [1, 5, 10]
}

param_dist = {
    'learning_rate': stats.loguniform(1e-3, 0.2),
    'max_depth': stats.randint(3, 8),
    'subsample': stats.uniform(0.6, 0.4),
    'colsample_bytree': stats.uniform(0.6, 0.4),
    'n_estimators': stats.randint(500, 1500),
    'reg_alpha': stats.expon(scale=50),
    'reg_lambda': stats.expon(scale=50),
    'gamma': stats.expon(scale=0.3),
    'min_child_weight': stats.randint(1, 15)
}

def avaliacao_temporal(modelo, X, y, janela=180):
    perdas = []
    for i in range(janela, len(y)):
        intervalo = slice(i-janela, i)
        preds = modelo.predict(X[intervalo])
        perdas.append(poisson_log_loss(y[intervalo], preds))
    return np.mean(perdas)

grid_model = XGBRegressor(
    objective='count:poisson',
    eval_metric='poisson-nloglik'
)

random_model = XGBRegressor(
    objective='count:poisson',
    eval_metric='poisson-nloglik',
    tree_method='hist',
    early_stopping_rounds=50,
    random_state=42
)

tscv =  TimeSeriesSplit(n_splits=5)

grid_search = GridSearchCV(
    estimator=grid_model,
    param_grid=param_grid,
    scoring=custom_scorer,
    cv=tscv,
    n_jobs=1,
    verbose=10
)

random_search = RandomizedSearchCV(
    estimator=random_model,
    param_distributions=param_dist,
    n_iter=50,
    scoring=custom_scorer,
    cv=tscv,
    n_jobs=-1,
    verbose=2,
    random_state=42
)

COLUMNS_DROP = [
    'event_id', 'date', 'away_team', 'away_player',
    'away_score', 'home_team', 'home_player', 'home_score', 'total_score',
    'home_pos', 'away_pos', 'score_home_pos', 'score_away_pos', 'matchup_key',
]