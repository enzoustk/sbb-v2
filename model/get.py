from xgboost import XGBRegressor
from files.paths import MODEL_PATH

def get_model():
    model = XGBRegressor()
    model.load_model(MODEL_PATH)

    return model