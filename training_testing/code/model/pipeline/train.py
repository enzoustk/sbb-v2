from typing import Dict, Any
from utils import print_gap
from sklearn.base import BaseEstimator
from model.pipeline.params import MODEL_CONFIG
from data.feature.constants import MODEL_FEATURES, TARGET_COL

def _get_model_config(model_name: str, model_type: str = "models") -> Dict[str, Any]:
    config = MODEL_CONFIG[model_type].get(model_name)
    if not config:
        raise ValueError(f"Modelo {model_name} não encontrado em {model_type}")
    return config

def _prepare_data(train_split):
    return (
        train_split.filter(items=list(MODEL_FEATURES)),
        train_split[TARGET_COL]
    )

def train_model(model_name: str, train_split, model_type: str = "models") -> BaseEstimator:
    X, y = _prepare_data(train_split)
    config = _get_model_config(model_name, model_type)
    
    # Construção do modelo base
    model_args = config.get("fixed_params", {}).copy()
    model = config["constructor"](**model_args)
    
    # Verifica necessidade de busca de parâmetros
    search_strategy = config.get("search_strategy")
    
    if not search_strategy:
        print_gap(f"Treinando baseline {model_name}")
        model.fit(X, y)
        return model
    
    # Configurar busca de parâmetros
    searcher = search_strategy["strategy"](
        estimator=model,
        param_distributions=config["param_distributions"],
        **search_strategy["params"]  # Parâmetros já incluem 'cv'
    )
    
    print_gap(f"Iniciando busca para {model_name}")
    try:
        searcher.fit(X, y)
    except ValueError as e:
        print_gap(f"Erro: {str(e)}")
        return model
    
    print_gap(f"Melhores parâmetros: {searcher.best_params_}")
    
    # Treino final com todos os dados
    best_model = searcher.best_estimator_.fit(X, y)
    
    return best_model

def train_baseline(baseline_name: str, train_split) -> BaseEstimator:
    return train_model(baseline_name, train_split, "baseline")