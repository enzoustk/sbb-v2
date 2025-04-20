import logging
import sys
from xgboost import XGBRegressor
from files.paths import MODEL_PATH

logger = logging.getLogger(__name__)

def model():
    try:
        model = XGBRegressor()
        model.load_model(MODEL_PATH)
        logger.info(f'Model loaded sucessfully from {MODEL_PATH}')
        return model
    except:
        logger.info('Error loading model. Breaking Code.')
        sys.exit()