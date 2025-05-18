import pandas as pd
import numpy as np


""" 
Vamos mudar nossa intenção.
Agora faremos:


ordenamos por data;
descartarmos todos os jogos que são 'após' a data/hora atual ('date');
descartamos dos últimos 8 jogos, todos os jogos em que == player_team atual.
ou seja, ficaríamos somente com os jogos que ocorreram antes do atual e 'fora da streak'.

E aí então, para os dados que sobram, vamos calcular as estatísticas abaixo:


1- Para todos os dados;
'player_off_avg': média de gols feitos, ou seja, de player_score
'player_def_avg': média de gols sofridos, ou seja, de visitor_score 
'player_delta_score': player_off_avg - player_def_avg

2- Usando somente os últimos 8 dados:
(para valores nan, fillaremos os valores 'globais' -- calculados acima)
'player_off_avg_l8': média de gols feitos, ou seja, de player_score
'player_def_avg_l8': média de gols sofridos, ou seja, de visitor_score 
'player_delta_score_l8': hp_off_avg - hp_def_avg

3- Usando somente os dados do dataframe em que player_team == player_team atual:
(para valores nan, usamos: 0.5 nos uppers, 0 no hp_team_delta_score, e hp_def_avg e hp_off_avg 'globais')
'player_team_off_avg': média de gols feitos,
'player_team_def_avg' média de gols sofridos, 
'player_team_delta_score': hp_off_avg - hp_def_avg
'player_team_def_upper': (jogos com ap_score acima de hp_team_def_avg) / contagem de jogos
'player_team_off_upper': o mesmo de cima, só que usando hp_score ao invés de ap_score
"""

""" 
Vamos mudar, vamos criar uma função chamada generate_player_df.

qual é o problema que eu enfrento:

um mesmo jogador, pode vir tanto em 'hp' quanto em 'ap', quero que:

vamos receber um string como variável.

vamos filtrar o dataframe para usarmos somente linhas em que: ou hp ou ap sejam == string

após isso, vamos ter um df em que em algumas linhas, o valor de ap == string e em outras hp == string.

precisamos criar então duas novas colunas: 'player' e 'visitor':
vamos colocar o string como valor de 'player' e visitor vai ser o valor do outro valor da linha, que não o string.

aí então, temos que ajustar 
"""

def preprocess_dataframe(
        data: pd.DataFrame,
        live: bool = True
        ):
    """Creates a column with the matchup key for the two players"""

    data['matchup_key'] = data.apply(
        lambda row:
        tuple(sorted([
        str(row['home_player']).lower(),
        str(row['away_player']).lower()
        ])), axis=1)
    
    data = data.sort_values(
        ['matchup_key', 'date']
        ).reset_index(drop=True)
    
    if live == False:
        data['total_score'] = data.groupby(
            'matchup_key')['total_score'].shift()
    
    data['hp'] = data['matchup_key'].str[0]
    data['position_inplace'] = np.where(
        data['hp'] == data['home_player'
        ].str.lower(),
        1, 0
        )
    
    mask = data['position_inplace'] == 1

    data['hp_score'] = np.where(mask, data['home_score'], data['away_score'])
    data['hp_team'] = np.where(mask, data['home_team'], data['away_team'])
    data['ap_score'] = np.where(mask, data['away_score'], data['home_score'])
    data['ap_team'] = np.where(mask, data['away_team'], data['home_team'])

    data['hp'] = np.where(mask, data['home_player'], data['away_player'])
    data['ap'] = np.where(mask, data['away_player'], data['home_player'])

    return data

def add_player_stats(data: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona estatísticas para 'hp_player' e 'ap_player' baseadas em jogos anteriores,
    excluindo jogos recentes com o mesmo time e calculando métricas específicas.
    """
    
    def calculate_stats(player_df: pd.DataFrame, current_idx: int, current_team: str, player_type: str) -> dict:
        """Calcula todas as estatísticas para uma linha específica."""
        stats = {}
        
        # Dados históricos até o momento atual (excluindo a linha atual)
        historical = player_df.iloc[:current_idx]
        historical = historical[historical['date'] < player_df.iloc[current_idx]['date']]
        
        # Últimos 8 jogos, excluindo os que têm o mesmo time atual
        last_8 = historical.tail(8)
        last_8_filtered = last_8[last_8['player_team'] != current_team]
        
        # 1. Estatísticas globais (todos os dados válidos)
        if not historical.empty:
            stats[f'{player_type}_off_avg'] = historical['player_score'].mean()
            stats[f'{player_type}_def_avg'] = historical['visitor_score'].mean()
            stats[f'{player_type}_delta_score'] = stats[f'{player_type}_off_avg'] - stats[f'{player_type}_def_avg']
        else:
            stats.update({f'{player_type}_{k}': 0.0 for k in ['off_avg', 'def_avg', 'delta_score']})
        
        # 2. Estatísticas dos últimos 8 jogos filtrados
        if not last_8_filtered.empty:
            stats[f'{player_type}_off_avg_l8'] = last_8_filtered['player_score'].mean()
            stats[f'{player_type}_def_avg_l8'] = last_8_filtered['visitor_score'].mean()
            stats[f'{player_type}_delta_score_l8'] = stats[f'{player_type}_off_avg_l8'] - stats[f'{player_type}_def_avg_l8']
        else:
            # Usa valores globais se não houver dados
            stats[f'{player_type}_off_avg_l8'] = stats[f'{player_type}_off_avg']
            stats[f'{player_type}_def_avg_l8'] = stats[f'{player_type}_def_avg']
            stats[f'{player_type}_delta_score_l8'] = stats[f'{player_type}_delta_score']
        
        # 3. Estatísticas específicas do time atual
        team_historical = historical[historical['player_team'] == current_team]
        if not team_historical.empty:
            stats[f'{player_type}_team_off_avg'] = team_historical['player_score'].mean()
            stats[f'{player_type}_team_def_avg'] = team_historical['visitor_score'].mean()
            stats[f'{player_type}_team_delta_score'] = stats[f'{player_type}_team_off_avg'] - stats[f'{player_type}_team_def_avg']
            stats[f'{player_type}_team_off_upper'] = (team_historical['player_score'] > stats[f'{player_type}_team_off_avg']).mean()
            stats[f'{player_type}_team_def_upper'] = (team_historical['visitor_score'] > stats[f'{player_type}_team_def_avg']).mean()
        else:
            stats[f'{player_type}_team_off_avg'] = stats[f'{player_type}_off_avg']
            stats[f'{player_type}_team_def_avg'] = stats[f'{player_type}_def_avg']
            stats[f'{player_type}_team_delta_score'] = 0.0
            stats[f'{player_type}_team_off_upper'] = 0.5
            stats[f'{player_type}_team_def_upper'] = 0.5
        
        return stats
    
    # Processa hp_player e ap_player separadamente
    for player_type in ['hp', 'ap']:
        # Cria um DataFrame centrado no jogador
        temp_df = data.copy()
        temp_df['player'] = temp_df[f'{player_type}_player']
        temp_df['player_team'] = temp_df[f'{player_type}_team']
        temp_df['player_score'] = temp_df[f'{player_type}_score']
        temp_df['visitor_score'] = temp_df[f'ap_score' if player_type == 'hp' else 'hp_score']
        
        # Ordena e agrupa por jogador
        temp_df = temp_df.sort_values(['player', 'date'])
        grouped = temp_df.groupby('player', group_keys=False)
        
        # Calcula estatísticas para cada linha
        stats_list = []
        for name, group in grouped:
            for i in range(len(group)):
                current_row = group.iloc[i]
                stats = calculate_stats(
                    player_df=group,
                    current_idx=i,
                    current_team=current_row['player_team'],
                    player_type=player_type
                )
                stats_list.append(stats)
        
        # Adiciona as estatísticas ao DataFrame original
        stats_df = pd.DataFrame(stats_list)
        stats_df.index = group.index
        data = data.merge(stats_df, left_index=True, right_index=True, how='left')
    
    return data