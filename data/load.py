
def csv():
    import pandas as pd
    from files.paths import HISTORIC_DATA
    try:
        csv_data = pd.read_csv(HISTORIC_DATA)
    
    except FileNotFoundError:
        csv_data = pd.DataFrame()
    
    if isinstance(csv_data, str):
        csv_data = pd.DataFrame()

    return csv_data

def json():
    import pandas as pd
    from files.paths import ALL_DATA
    try:
        json_data = pd.read_json(ALL_DATA)
    
    except FileNotFoundError:
        json_data = pd.DataFrame()

    return json_data
