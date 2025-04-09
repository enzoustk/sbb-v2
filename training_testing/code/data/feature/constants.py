INDICES_PATH = 'dados/database/indices/'
TARGET_COL = 'gols_totais'
DATA_PATH = "dados/database/dados_totais.csv"

TEMPO = {
    38439: 6,   #Battle Volta 6min
    22614: 8,   #Battle 8min
    37298: 8,   #H2H GG League 8min    
    23114: 12   #GT Leagues 12min
}

INDICES_DATABASE = {
    'players': {
        'col1': 'jogador_casa',
        'col2': 'jogador_fora',
        'par': False,
    },
    'teams': {
        'col1': 'time_casa',
        'col2': 'time_fora',
        'par': False,
    },
    'matchups': {
        'col1': 'jogador_casa',
        'col2': 'jogador_fora',
        'par': True,
    }
}

ORIGIN_FEATURES = [
    #Dados Numéricos
    'date', 'event_id', 'league',
    #Dados Categóricos
    'jogador_casa', 'jogador_fora', 'time_casa', 'time_fora', 
    #Dados de Gols
    'gols_casa', 'gols_fora', 'gols_totais'
]

MODEL_FEATURES = [
    # Features Temporais
    'last_h2h', 'time_since_start',
    'day_of_week', 'hour_of_day',
    'day_angle', 'hour_angle',

    # Features categóricas (Sem encoding)
    'jogador_casa_idx', 'jogador_fora_idx', 
    'time_casa_idx', 'time_fora_idx',
    'confronto_idx', 'confronto_count',

    # Features Categóricas (target encoding e one-hot para league)
    'te_confronto',
    'te_time_casa', 'te_time_fora',
    'te_jogador_casa', 'te_jogador_fora',
    'league_38439', 'league_22614', 'league_37298', 'league_23114',

    # Totais de Gols (lags, rolling, cumulativas, ewma, etc.)
    'l1', 'l2', 'l3',
    'median_3', 'std_3', 'avg_3',
    'ewma_15', 'ewma_3',
    'avg', 'std', 'median',
]

ODDS_DATABASE = {
    '1_3': ['1_3_handicap', '1_3_under_od', '1_3_over_od'],
    '1_2': ['1_2_handicap','1_2_home_od', '1_2_away_od'],
    '1_1': ['1_1_home_od', '1_1_draw_od', '1_1_away_od']
}