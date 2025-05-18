import pandas as pd
import numpy as np
from typing import Dict, Any, List, Set

class FeatureEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.sort_values(by='date').reset_index(drop=True)

class IndvEngineer(FeatureEngineer):
    def __init__(self, df):
        super().__init__(df=df)
        self.player_stats: Dict[str, List[Dict]] = {}  # Histórico de partidas por jogador
    
    def calculate_features(self):
        features = []
        for _, row in self.df.iterrows():
            # Features para o jogador da posição "home"
            home_features = self._get_features(
                player=row['home_player'],
                current_date=row['date'],
                current_team=row['home_team'],
                prefix='home'
            )
            
            # Features para o jogador da posição "away"
            away_features = self._get_features(
                player=row['away_player'],
                current_date=row['date'],
                current_team=row['away_team'],
                prefix='away'
            )
            
            features.append({**home_features, **away_features})
            self._update_stats(row)  # Atualiza após calcular features (evita leakage)
        
        self.df = pd.concat([self.df, pd.DataFrame(features)], axis=1)
        return self.df
    
    def _get_features(
        self,
        player: str,
        current_date: pd.Timestamp,
        current_team: str,
        prefix: str
    ) -> Dict[str, float]:
        if player not in self.player_stats:
            return {
                f'{prefix}_avg_score': np.nan,
                f'{prefix}_avg_goals_conceded': np.nan,  # Nova feature
                f'{prefix}_win_rate': np.nan
            }
        
        # Filtrar TODOS os jogos anteriores e remover mesmo time
        past_matches = [m for m in self.player_stats[player] if m['date'] < current_date]
        valid_matches = [m for m in past_matches if m['team'] != current_team]
        valid_recent_matches = valid_matches[-8:] if valid_matches else []
        
        if not valid_recent_matches:
            return {
                f'{prefix}_avg_score': np.nan,
                f'{prefix}_avg_goals_conceded': np.nan,
                f'{prefix}_win_rate': np.nan
            }
        
        # Calcular todas as estatísticas
        avg_score = sum(m['score'] for m in valid_recent_matches) / len(valid_recent_matches)
        avg_conceded = sum(m['conceded'] for m in valid_recent_matches) / len(valid_recent_matches)  # Nova métrica
        win_rate = sum(m['is_win'] for m in valid_recent_matches) / len(valid_recent_matches)
        
        return {
            f'{prefix}_avg_score': avg_score,
            f'{prefix}_avg_goals_conceded': avg_conceded,
            f'{prefix}_win_rate': win_rate
        }
    
    def _update_stats(self, row: pd.Series):
        # Atualizar home_player
        home_player = row['home_player']
        if home_player not in self.player_stats:
            self.player_stats[home_player] = []
        self.player_stats[home_player].append({
            'date': row['date'],
            'team': row['home_team'],
            'score': row['home_score'],
            'conceded': row['away_score'],  # Gols sofridos = gols do oponente
            'is_win': 1 if row['home_score'] > row['away_score'] else 0
        })
        
        # Atualizar away_player
        away_player = row['away_player']
        if away_player not in self.player_stats:
            self.player_stats[away_player] = []
        self.player_stats[away_player].append({
            'date': row['date'],
            'team': row['away_team'],
            'score': row['away_score'],
            'conceded': row['home_score'],  # Gols sofridos = gols do oponente
            'is_win': 1 if row['away_score'] > row['home_score'] else 0
        })

class H2HEngineer(FeatureEngineer):
    def __init__(self, df):
        super().__init__(df=df)
        # Estrutura: {frozenset({player_a, player_b}): [lista de partidas]}
        self.h2h_matches: Dict[Set, List[Dict]] = {}

    def calculate_features(self):
        features = []
        for _, row in self.df.iterrows():
            current_home = row['home_player']
            current_away = row['away_player']
            current_date = row['date']
            
            # Chave para buscar confrontos diretos (independente da ordem)
            player_pair = frozenset({current_home, current_away})
            
            # Recuperar todas as partidas H2H anteriores
            past_matches = [
                m for m in self.h2h_matches.get(player_pair, []) 
                if m['date'] < current_date
            ]
            
            # Calcular estatísticas para o jogador home atual
            home_goals = []
            home_wins = 0
            away_goals = []
            
            for match in past_matches:
                # Verificar se o current_home era home ou away na partida anterior
                if match['home_player'] == current_home:
                    home_goals.append(match['home_score'])
                    home_wins += 1 if match['home_score'] > match['away_score'] else 0
                else:
                    home_goals.append(match['away_score'])
                    home_wins += 1 if match['away_score'] > match['home_score'] else 0
                
                # Coletar gols do jogador away atual
                if match['home_player'] == current_away:
                    away_goals.append(match['home_score'])
                else:
                    away_goals.append(match['away_score'])
            
            # Calcular médias e win rate
            avg_goals_home = np.mean(home_goals) if home_goals else np.nan
            avg_goals_away = np.mean(away_goals) if away_goals else np.nan
            win_rate_home = (home_wins / len(past_matches)) if past_matches else np.nan
            
            features.append({
                'h2h_avg_goals_home': avg_goals_home,
                'h2h_avg_goals_away': avg_goals_away,
                'h2h_win_rate_home': win_rate_home
            })
            
            # Atualizar histórico APÓS calcular as features
            self._update_h2h_matches(row)
        
        self.df = pd.concat([self.df, pd.DataFrame(features)], axis=1)
        return self.df

    def _update_h2h_matches(self, row: pd.Series):
        home_player = row['home_player']
        away_player = row['away_player']
        pair_key = frozenset({home_player, away_player})
        
        if pair_key not in self.h2h_matches:
            self.h2h_matches[pair_key] = []
        
        self.h2h_matches[pair_key].append({
            'date': row['date'],
            'home_player': home_player,
            'away_player': away_player,
            'home_score': row['home_score'],
            'away_score': row['away_score']
        })

df = pd.read_csv('data/training_data.csv')
indv = IndvEngineer(df=df)
indv_df = indv.calculate_features()
h2h = H2HEngineer(df=indv_df)
featured_df = h2h.calculate_features()
featured_df.to_csv('featured.csv', index=False)