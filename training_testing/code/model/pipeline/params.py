from xgboost import XGBRegressor
from sklearn.linear_model import PoissonRegressor
from scipy.stats import uniform, randint
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

MODEL_CONFIG = {
    "baseline": {
        "PoissonRegressor": {
            "constructor": PoissonRegressor,
            "params": {"alpha": 0.1, "max_iter": 1000},
            "search_strategy": None
        }
    },
    "models": {
        "XGBRegressor": {
            "constructor": XGBRegressor,
            "fixed_params": {
                "objective": "reg:squarederror",
                "random_state": 42,
                "n_jobs": -1
            },
            "param_distributions": {
                'n_estimators': randint(100, 400),
                'max_depth': randint(3, 7),
                'learning_rate': uniform(0.01, 0.2),
                'subsample': uniform(0.6, 0.4)
            },
            "search_strategy": {
                "strategy": RandomizedSearchCV,
                "params": {
                    "n_iter": 20,
                    "scoring": "neg_mean_squared_error",
                    "cv": TimeSeriesSplit(n_splits=3),
                    "verbose": 1,
                    "n_jobs": -1,
                    "random_state": 42
                }
            }
        }
    }
}