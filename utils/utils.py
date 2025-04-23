import pandas as pd

def print_separator(size: int = 60):
    print('\n' + '-' * size + '\n')

def print_features(features: pd.DataFrame):
    chunk = 3
    i = 0 
    output = [f'\n']
    for key, value in features.iloc[0].items():
            output.append(f'{key}: {value:.2f}')
            i += 1
            if i % chunk == 0:
                output.append('\n')
            else:
                output.append(', ')
    return ''.join(output).strip()