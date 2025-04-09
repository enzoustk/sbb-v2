def preprocess(data, lookback_data):
    #Importações
    from utils import print_gap
    from data.feature.engineering import calcular_features
    from data.feature.constants import TEMPO, ORIGIN_FEATURES, MODEL_FEATURES, ODDS_DATABASE

    #Carrega o CSV com dados e calcula features 

    data = calcular_features(
        data = data,
        lookback_data = lookback_data,
        live = False,
        normalizar = True,
        tempo = TEMPO
    )

    #Remover colunas desnecessárias
    data = data.filter(items=ORIGIN_FEATURES + MODEL_FEATURES + ODDS_DATABASE['1_3'])

    #Limpar linhas com Nan
    data = data.dropna(subset=[col for col in data.columns if col not in ODDS_DATABASE['1_3']])
    
    print_gap("Features calculadas.")
    return data

def load():
    from utils import print_gap
    import pandas as pd
    from data.feature.constants import DATA_PATH
    
    all_data = pd.read_csv(DATA_PATH)
    all_data['date'] = pd.to_datetime(all_data['date'], errors='coerce')
    all_data = all_data.sort_values(by = 'date')
    
    print_gap("Dataframe importado.")
    return all_data