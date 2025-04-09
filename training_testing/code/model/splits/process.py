"""
Para cada conjunto treino e teste, calcula suas devidas features usando o lookback apropriado.
Retorna os mesmos splits, sendo que com suas features devidamente calculadas.
"""

def process_splits(raw_splits):
    from data.process import preprocess
    splits = []
    
    for train_raw, test_raw in raw_splits:
        train_split = preprocess(data = train_raw, lookback_data = None)
        test_split = preprocess(data = test_raw, lookback_data = train_raw)
        splits.append((train_split, test_split))
    
    return splits