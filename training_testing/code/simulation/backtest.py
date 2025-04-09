import pandas as pd
from tqdm import tqdm
from .betting import run_simulation
from .bankroll import BankrollManager
from data.feature.constants import MODEL_FEATURES, ODDS_DATABASE, ORIGIN_FEATURES

def run_full_backtest(test_data, models, initial_capital=1000):
    all_results = []
    
    for model_name, model in models.items():
        print(f"\nExecutando backtest para: {model_name}")
        
        # Configurar bankroll e executar simulação
        bankroll = BankrollManager(initial_capital=initial_capital)
        simulation_results = run_simulation(
            test_data=test_data,
            model=model,
            bankroll=bankroll
        )
        
        # Processar resultados
        results_df = process_simulation_results(simulation_results, model_name)
        all_results.append(results_df)
    
    return pd.concat(all_results, ignore_index=True)

def process_simulation_results(simulation_results, model_name):
    processed = []
    
    # Definir colunas essenciais no escopo geral
    essential_cols = [
        'date', 'time_casa', 'time_fora', 'gols_totais', 
        'gols_previstos', 'prob_over', 'prob_under',
        'tipo_aposta', 'ev_bet', 'stake', 'profit',
        'bankroll_antes', 'bankroll_depois'
    ]
    
    print(f"Processando resultados para o modelo {model_name}. Dados recebidos: {len(simulation_results)} dias.")
    
    for day_df in simulation_results:
        try:
            # Adicionar coluna de modelo
            day_df['model'] = model_name
            
            # Verificar formato do dataframe
            print(f"Formato do dia: {day_df.shape}, colunas: {day_df.columns[:5].tolist()}...")
            
            # MODIFICAÇÃO CRUCIAL: Não filtrar por tipo_aposta não nulos
            # Apenas adicionar o dataframe completo aos processados
            processed.append(day_df)
            print(f"Dia processado com sucesso: {day_df['date'].iloc[0]}, {day_df.shape} registros")
            
        except Exception as e:
            print(f"Erro em {day_df['date'].iloc[0] if 'date' in day_df else 'DATA DESCONHECIDA'}: {str(e)}")
            continue
    
    if processed:
        try:
            # Tentar concatenar todos os resultados
            result = pd.concat(processed, ignore_index=True)
            
            # Garantir que temos colunas numéricas para odds
            if '1_3_over_od' in result.columns and not pd.api.types.is_numeric_dtype(result['1_3_over_od']):
                result['1_3_over_od'] = pd.to_numeric(result['1_3_over_od'], errors='coerce')
            
            if '1_3_under_od' in result.columns and not pd.api.types.is_numeric_dtype(result['1_3_under_od']):
                result['1_3_under_od'] = pd.to_numeric(result['1_3_under_od'], errors='coerce')
            
            # Ordenar colunas para melhor visualização
            final_cols = [col for col in essential_cols if col in result.columns]
            final_cols += [col for col in result.columns if col not in essential_cols]
            
            # Filtrar apenas colunas que existem
            final_cols = [col for col in final_cols if col in result.columns]
            
            return result[final_cols]
        except Exception as e:
            print(f"Erro ao concatenar resultados: {str(e)}")
            # Tentar retornar apenas o primeiro resultado como fallback
            if processed:
                return processed[0]
            return pd.DataFrame(columns=essential_cols)
    else:
        print(f"AVISO: Nenhum resultado processado para o modelo {model_name}!")
        return pd.DataFrame(columns=essential_cols)

def calculate_sharpe(returns):
    # Implemente a lógica para calcular o Sharpe Ratio
    pass

def calculate_max_drawdown(returns):
    # Implemente a lógica para calcular o Max Drawdown
    pass 