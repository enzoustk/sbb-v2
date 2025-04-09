from utils import H2HAccessor
import pandas as pd, numpy as np
from data.feature.constants import INDICES_PATH, INDICES_DATABASE

#Ajustar path_arquivo para poder vir de outra pasta.

def gerar_liga(data):
    dummies = pd.get_dummies(data['league'], prefix='league', dtype=float)
    data = pd.concat([data.drop('league', axis=1), dummies], axis=1)
    return data

def criar_indices(data, indices_database):
    import os
    import pandas as pd
    
    for arquivo in indices_database:
        config = indices_database[arquivo]
        col1 = config['col1']
        col2 = config['col2']
        par = config['par']

        def carregar_dados(caminho):
            if os.path.exists(caminho):
                return pd.read_csv(caminho).set_index('valor')['indice'].to_dict()
            return {}

        def salvar_dados(mapping, caminho):
            pd.DataFrame({
                'valor': list(mapping.keys()),
                'indice': list(mapping.values())
            }).to_csv(caminho, index=False)

        # Processamento principal para cada arquivo
        arquivo_path = os.path.join(INDICES_PATH, f"{arquivo}_idx.csv")
        mapping = carregar_dados(arquivo_path)
        
        if not par:
            # Processamento individual para colunas
            for col in [col1, col2]:
                lower_col = data[col].str.lower()
                novos_valores = lower_col[~lower_col.isin(mapping)]
                
                if not novos_valores.empty:
                    max_idx = max(mapping.values()) if mapping else 0
                    novos_indices = {v: max_idx + i + 1 for i, v in enumerate(novos_valores.unique())}
                    mapping.update(novos_indices)
                    salvar_dados(mapping, arquivo_path)
                
                data[f'{col}_idx'] = lower_col.map(mapping)
                
        else:
            # Processamento de pares
            pares = [
                tuple(sorted(pair)) 
                for pair in zip(
                    data[col1].str.lower(), 
                    data[col2].str.lower()
                )
            ]
            
            novos_pares = [p for p in pares if str(p) not in mapping]
            if novos_pares:
                max_idx = max(mapping.values()) if mapping else 0
                mapping.update({str(p): max_idx + i + 1 for i, p in enumerate(novos_pares)})
                salvar_dados(mapping, arquivo_path)
            
            data[f'{arquivo}_idx'] = [mapping[str(p)] for p in pares]
            data[f'{arquivo}_count'] = data.groupby(f'{arquivo}_idx').cumcount().astype(float)

    return data

def coletar_indices(data, indices_database):
    import os
    import pandas as pd

    for arquivo in indices_database:
        # 1. Validação do arquivo na configuração
        if arquivo not in indices_database:
            raise ValueError(f'Arquivo {arquivo} não está na lista de índices')

        config = indices_database[arquivo]
        col1 = config['col1']
        col2 = config['col2']
        par = config['par']

        # 2. Caminho do arquivo de índice
        arquivo_path = os.path.join(INDICES_PATH, f"{arquivo}_idx.csv")

        # 3. Se o arquivo não existe, cria os índices e recarrega
        if not os.path.exists(arquivo_path):
            print(f"Arquivo {arquivo}_idx.csv não encontrado. Criando...")
            data = criar_indices(data, {arquivo: config})  # Passa apenas o índice atual
            continue

        # 4. Carregar mapeamento existente
        mapeamento_dados = pd.read_csv(arquivo_path)
        mapping = dict(zip(mapeamento_dados['valor'], mapeamento_dados['indice']))

        # 5. Processar índices individuais ou pares
        if not par:
            # Para cada coluna individual
            for col in [col1, col2]:
                lower_col = data[col].str.lower()
                
                # Verificar se há valores não mapeados
                missing = lower_col[~lower_col.isin(mapping)]
                if not missing.empty:
                    print(f"Valores faltantes em {arquivo}_{col}. Atualizando...")
                    data = criar_indices(data, {arquivo: config})  # Atualiza apenas este índice
                    mapeamento_dados = pd.read_csv(arquivo_path)  # Recarrega o mapeamento
                    mapping = dict(zip(mapeamento_dados['valor'], mapeamento_dados['indice']))
                
                data[f'{col}_idx'] = lower_col.map(mapping)
        
        else:
            # Para pares, usar formato consistente (ex: "a|b")
            pairs = [
                "|".join(sorted([str(a).lower(), str(b).lower()])) 
                for a, b in zip(data[col1], data[col2])
            ]
            
            # Verificar pares faltantes
            missing_pairs = [p for p in pairs if p not in mapping]
            if missing_pairs:
                print(f"Pares faltantes em {arquivo}. Atualizando...")
                data = criar_indices(data, {arquivo: config})  # Atualiza apenas este índice
                mapeamento_dados = pd.read_csv(arquivo_path)
                mapping = dict(zip(mapeamento_dados['valor'], mapeamento_dados['indice']))
            
            data[f'{arquivo}_idx'] = [mapping[p] for p in pairs]
            data[f'{arquivo}_count'] = data.groupby(f'{arquivo}_idx').cumcount().astype(float)

    return data

def criar_temporais(data):
    
    data['date'] = pd.to_datetime(data['date'])
    data['last_h2h'] = data.h2h.date.transform(lambda x: x.diff().dt.total_seconds() / 3600)
    data['time_since_start'] = (data['date'] - data['date'].min()).dt.days.astype(float)
    data['day_of_week'] = data['date'].dt.weekday.astype(float)
    data['hour_of_day'] = data['date'].dt.hour.astype(float)

    # Adicionar cálculo das componentes cíclicas
    data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
    data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
    data['hour_sin'] = np.sin(2 * np.pi * data['hour_of_day'] / 24)
    data['hour_cos'] = np.cos(2 * np.pi * data['hour_of_day'] / 24) 

    #Agora então geramos as arctangentes
    data['day_angle'] = np.arctan2(data['day_sin'], data['day_cos'])
    data['hour_angle'] = np.arctan2(data['hour_sin'], data['hour_cos'])

    data = data.drop(['day_sin','day_cos','hour_sin','hour_cos'], axis = 1)
    return data

def criar_gols(data, normalizar, live, tempo): 

    # Validação inicial
    required_columns = {'jogador_casa', 'jogador_fora', 'gols_totais', 'league'}
    if not required_columns.issubset(data.columns):
        raise ValueError(f"DataFrame deve conter as colunas: {required_columns}") 

    data = data.copy()

    # 1. Normalização
    if normalizar:
        data['gols_totais'] = data['gols_totais'] / data['league'].map(tempo)

    if not live:
        data['gols_totais'] = data.groupby('matchup_key')['gols_totais'].shift()

    # 2. Features Lag (Live Mode Safe)
    def criar_lags(data) -> pd.DataFrame:
        max_lags = 3
        for lag in range(1, max_lags + 1):
            if live:
                data[f'l{lag}'] = data.groupby('matchup_key')['gols_totais'].shift(lag)
            else:
                data[f'l{lag}'] = data.groupby('matchup_key')['gols_totais'].transform(lambda x: x.shift(lag))
        return data

    # 3. Rolling Statistics (Otimizado)
    def criar_rolling_stats(data, window: int = 3) -> pd.DataFrame:
        stats = {
            'median_3': lambda x: x.rolling(window).median(),
            'std_3': lambda x: x.rolling(window).std(ddof=0),
            'avg_3': lambda x: x.rolling(window).mean(),
        }

        for name, func in stats.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(func)
        
        return data

    # 4. EWMA (Versão Vetorizada)
    def criar_ewma(data) -> pd.DataFrame:
        alpha_config = {
            'ewma_15': 0.15,
            'ewma_3': 0.03
        }

        for name, alpha in alpha_config.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(
                lambda x: x.ewm(alpha=alpha, adjust=False).mean()
            )
        
        return data
    

    # 5. Cumulative Statistics (Performance)
    def criar_cumulative_stats(data) -> pd.DataFrame:
        stats = {
            'median': lambda x: x.expanding().median(),
            'std': lambda x: x.expanding().std(ddof=0),
            'avg': lambda x: x.expanding().mean(),
        }

        for name, func in stats.items():
            data[name] = data.groupby('matchup_key')['gols_totais'].transform(func)
        
        return data
    

    # Pipeline de execução
    data = (data
        .pipe(criar_lags)
        .pipe(criar_rolling_stats)
        .pipe(criar_ewma)
        .pipe(criar_cumulative_stats)
    )

    return data   

def calcular_features(
    data: pd.DataFrame,
    lookback_data: pd.DataFrame | None = None,
    live: bool = False,
    normalizar: bool = True,
    tempo: bool = True
    ) -> pd.DataFrame:
    
    #Marcar dados pertencetes ao 'data' original
    original_data = data.copy()
    original_data['__original__'] = True

    #Fazer uso de dados de treino, caso existentes 
    if lookback_data is not None:
        lookback_data = lookback_data.copy()
        lookback_data['__original__'] = False
        data = pd.concat([original_data, lookback_data], ignore_index=True)
    else:
        data = original_data

    #Garantir datetime e ordenação cronológica 
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date').reset_index(drop=True)

    data['matchup_key'] = data.apply(lambda row: tuple(sorted([
        str(row['jogador_casa']).lower(),
        str(row['jogador_fora']).lower()])),
        axis=1)
    
    # Geração de features propriamente dita:
    
    """
    # Índices:
    if live:
        data = coletar_indices(data,INDICES_DATABASE)
    elif not live:
        data = criar_indices(data, INDICES_DATABASE)
    """

    # Temporais
    data = criar_temporais(data)

    # Lags
    data = criar_gols(
        data,
        normalizar = normalizar,
        live = live,
        tempo = tempo
        )
    
    # Ligas no dummy encoding
    data = gerar_liga(data)
    
    # Filtro final e limpeza de dados externos
    data = data[data['__original__']].drop(columns=['__original__'])
    data = data.reset_index(drop=True)
    return data