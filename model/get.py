import logging
import sys
from xgboost import XGBRegressor
from files.paths import MODEL_PATH

def get_model():
    try:
        model = XGBRegressor()
        model.load_model(MODEL_PATH)
        logging.info(f'Model loaded sucessfully from {MODEL_PATH}')
        return model
    except:
        logging.info('Error loading model. Breaking Code.')
        sys.exit()