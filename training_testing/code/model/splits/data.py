from sklearn.model_selection import TimeSeriesSplit
import pandas as pd

def split_data(
    df: pd.DataFrame,
    date_col: str,
    test_size_frac: float,
    n_splits: int,
    gap: int,
    output: bool = True
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:

    df = df.sort_values(date_col).reset_index(drop=True)
    
    # Validação crítica
    if len(df) < 100:
        raise ValueError("Dataset muito pequeno para splits temporais (mínimo 100 registros)")
    
    test_size = max(int(len(df) * test_size_frac), 30)  # Mínimo 30 amostras
    tscv = TimeSeriesSplit(
        n_splits=min(n_splits, len(df) // test_size),  # Garante splits válidos
        test_size=test_size,
        gap=gap
    )
    
    splits = []
    
    for fold, (train_index, test_index) in enumerate(tscv.split(df)):
        train_data = df.iloc[train_index]
        
        # Ajusta dinamicamente o tamanho do teste para ser relativo ao treino
        test_size = max(1, int(len(train_data) * test_size_frac))
        test_data = df.iloc[test_index[:test_size]]  # Pega apenas a fração desejada

        # Logging das datas
        if output:
            dia_inicio_treino = train_data[date_col].min().strftime('%d/%m/%Y')
            dia_fim_treino = train_data[date_col].max().strftime('%d/%m/%Y')
            dia_inicio_teste = test_data[date_col].min().strftime('%d/%m/%Y')
            dia_fim_teste = test_data[date_col].max().strftime('%d/%m/%Y')
            
            from utils import print_gap
            print_gap(
                f"Fold {fold + 1}:",
                f"Treino: {dia_inicio_treino} a {dia_fim_treino} ({len(train_data)} linhas)",
                f"Teste: {dia_inicio_teste} a {dia_fim_teste} ({len(test_data)} linhas)",
                sep='\n'
            )
        
        splits.append((train_data, test_data))
    
    return splits