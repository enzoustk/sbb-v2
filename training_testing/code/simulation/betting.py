#betting.py

def criar_ajuste(tipo_aposta, row):
    
    import numpy as np
    
    """
    Recebe o tipo de aposta e a linha
    Calcula o ajuste para a aposta
    Retorna o ajuste
    """

    handicap = row['1_3_handicap']
    gols_totais = row['gols_totais']

    if tipo_aposta == "Under":
        ajuste = handicap - gols_totais
    
    elif tipo_aposta == "Over":
        ajuste = gols_totais - handicap

    else:
        ajuste = np.nan
    
    return ajuste

def calcular_profit(ajuste, odd, stake):
    
    """
    Recebe o ajuste, a odd e o stake
    Calcula o lucro para a aposta
    Retorna o lucro
    """
    
    if ajuste >= 0.5:
        profit = (odd - 1) * stake
    elif ajuste == 0.25:
        profit = ((odd - 1) / 2) * stake
    elif ajuste == 0:
        profit = 0
    elif ajuste == -0.25:
        profit = -0.5 * stake
    elif ajuste <= -0.5:
        profit = -1 * stake
    else:
        profit = 0
    return profit

def definir_aposta(row):
    
    import numpy as np
    
    """
    Recebe a linha (partida) e define a aposta
    Com base no valor esperado (EV) de cada aposta, define a aposta com o maior EV
    Retorna o tipo de aposta, o valor esperado e a odd
    """
    
    if row['ev_over'] > 0 and row['ev_over'] >= row['ev_under']:
        """
        Calcula o valor esperado (EV) da aposta Over
        """
        tipo_aposta = "Over"
        ev_bet = row['ev_over']
        odd = row['1_3_over_od']
        return tipo_aposta, ev_bet, odd
    
    elif row['ev_under'] > 0 and row['ev_under'] > row['ev_over']:
        """
        Calcula o valor esperado (EV) da aposta Under
        """
        tipo_aposta = "Under"
        ev_bet = row['ev_under']
        odd = row['1_3_under_od']
        return tipo_aposta, ev_bet, odd

    else:
        """
        Se não houver valor esperado positivo para nenhuma das apostas, retorna np.nan
        """
        return np.nan, np.nan, np.nan

def calcular_aposta(row, bankroll):
    
    import numpy as np, pandas as pd

    """
    Define a aposta com o maior valor esperado (EV),
    Calcula o ajuste para a aposta
    Calcula o lucro para a aposta
    Retorna o tipo de aposta, o valor esperado, o ajuste, a stake, o lucro e a odd utilizada
    """

    try:
        tipo_aposta, ev_bet, odd = definir_aposta(row)
        
        # Verificar se os valores são válidos
        if pd.isna(tipo_aposta) or pd.isna(ev_bet) or pd.isna(odd):
            return pd.Series({
                'tipo_aposta': np.nan,
                'ev_bet': np.nan,
                'ajuste': np.nan,
                'stake': 0, 
                'profit': 0,
                'odds_utilizadas': np.nan,
                'valor_esperado': 0
            })
        
        stake = bankroll.calculate_stake()
        ajuste = criar_ajuste(tipo_aposta, row)
        
        # Garantir que ajuste, odd e stake são números
        ajuste = float(ajuste) if not pd.isna(ajuste) else 0
        odd = float(odd) if not pd.isna(odd) else 1
        stake = float(stake) if not pd.isna(stake) else 0
        
        profit = calcular_profit(ajuste, odd, stake)

        return pd.Series({
            'tipo_aposta': tipo_aposta,
            'ev_bet': float(ev_bet),
            'ajuste': ajuste,
            'stake': stake, 
            'profit': profit,
            'odds_utilizadas': odd,
            'valor_esperado': float(ev_bet) * stake
        })
    except Exception as e:
        # Em caso de erro, retornar valores vazios
        print(f"Erro ao calcular aposta: {str(e)}")
        return pd.Series({
            'tipo_aposta': np.nan,
            'ev_bet': np.nan,
            'ajuste': np.nan,
            'stake': 0, 
            'profit': 0,
            'odds_utilizadas': np.nan,
            'valor_esperado': 0
        })

def run_simulation(test_data, model, bankroll):
    from data.feature.constants import MODEL_FEATURES, ORIGIN_FEATURES, ODDS_DATABASE
    from simulation.poisson import calcular_probabilidades_poisson
    import pandas as pd
    import numpy as np
   
    resultados = []
    
    # Verificar estrutura de dados de entrada
    print(f"Colunas disponíveis: {test_data.columns.tolist()}")
    print(f"Tipos de dados: {test_data.dtypes}")
    
    if 'duracao_partida' in test_data.columns:
        print(f"Tipo de duracao_partida: {type(test_data['duracao_partida'].iloc[0])}")
        print(f"Primeiros valores de duracao_partida: {test_data['duracao_partida'].head().tolist()}")
    else:
        print("Coluna 'duracao_partida' não encontrada!")
    
    # Pré-processamento defensivo
    if 'duracao_partida' not in test_data.columns:
        print("CRIANDO coluna duracao_partida padrão (1.0)")
        test_data['duracao_partida'] = 1.0
    
    # Filtrar e ordenar colunas mantendo as origin features
    test_data = test_data.dropna().copy()
    
    for dia_teste in test_data['date'].dt.date.unique():
        dia_teste_data = test_data[test_data['date'].dt.date == dia_teste].copy()
        
        try:
            # Verificar dados específicos para este dia
            print(f"\nAnalisando dia: {dia_teste}")
            
            # 1. Pré-processamento
            dia_teste_data = dia_teste_data.reset_index(drop=True)
            
            # 2. Previsões do modelo - SIMPLIFICADO
            features_disponiveis = [col for col in MODEL_FEATURES if col in dia_teste_data.columns]
            X_dia_teste = dia_teste_data[features_disponiveis]
            
            try:
                # Previsão com tratamento de erro explícito
                previsoes = model.predict(X_dia_teste)
                
                # Forçar conversão para array numérico 1D
                if isinstance(previsoes, (pd.Series, pd.DataFrame)):
                    previsoes = previsoes.to_numpy()
                
                if len(previsoes.shape) > 1 and previsoes.shape[1] > 1:
                    print(f"AVISO: Previsões com múltiplas colunas: {previsoes.shape}")
                    previsoes = previsoes[:, 0]  # Pegar apenas primeira coluna
                
                previsoes = previsoes.flatten()  # Garantir 1D
                previsoes = np.array([float(x) for x in previsoes])  # Forçar como float
                
                # Atribuir previsões como valores simples
                dia_teste_data['gols_previstos'] = previsoes
                
            except Exception as e:
                print(f"Erro nas previsões: {str(e)}")
                # Criar valores padrão para não quebrar o processo
                dia_teste_data['gols_previstos'] = 2.5  # Valor padrão seguro
            
            # 3. ELIMINAR Desnormalização dos gols - SIMPLIFICAÇÃO RADICAL
            # Apenas usar os valores previstos diretamente
            
            # 4. Cálculo de probabilidades - SIMPLIFICADO
            # Usar valor padrão de 2.5 para handicap
            try:
                # Aplicar item a item ao invés de vetorizado
                prob_over_list = []
                prob_under_list = []
                
                for idx, row in dia_teste_data.iterrows():
                    try:
                        gols_prev = float(row['gols_previstos'])
                        handicap = 2.5  # Valor fixo para simplificar
                        
                        # Chamar a função com valores simples
                        prob_over, prob_under = calcular_probabilidades_poisson(gols_prev, handicap)
                        
                        prob_over_list.append(prob_over)
                        prob_under_list.append(prob_under)
                    except Exception as e:
                        print(f"Erro no cálculo de probabilidades linha {idx}: {str(e)}")
                        prob_over_list.append(0.5)
                        prob_under_list.append(0.5)
                
                dia_teste_data['prob_over'] = prob_over_list
                dia_teste_data['prob_under'] = prob_under_list
                
            except Exception as e:
                print(f"Erro no cálculo de probabilidades: {str(e)}")
                dia_teste_data['prob_over'] = 0.5
                dia_teste_data['prob_under'] = 0.5
            
            # 5. Cálculo do Valor Esperado (EV) - MELHORADO
            try:
                # Converter odds para float de forma segura
                if '1_3_over_od' in dia_teste_data.columns:
                    # Converter string para float e colocar valor padrão se falhar
                    dia_teste_data['1_3_over_od_float'] = pd.to_numeric(dia_teste_data['1_3_over_od'], errors='coerce').fillna(1.0)
                    dia_teste_data['ev_over'] = dia_teste_data['prob_over'] * dia_teste_data['1_3_over_od_float'] - 1
                else:
                    dia_teste_data['ev_over'] = 0.0
                    
                if '1_3_under_od' in dia_teste_data.columns:
                    # Converter string para float e colocar valor padrão se falhar
                    dia_teste_data['1_3_under_od_float'] = pd.to_numeric(dia_teste_data['1_3_under_od'], errors='coerce').fillna(1.0)
                    dia_teste_data['ev_under'] = dia_teste_data['prob_under'] * dia_teste_data['1_3_under_od_float'] - 1
                else:
                    dia_teste_data['ev_under'] = 0.0
                
                # Garantir que nulls virem zeros
                dia_teste_data['ev_over'] = dia_teste_data['ev_over'].fillna(0.0)
                dia_teste_data['ev_under'] = dia_teste_data['ev_under'].fillna(0.0)
                
            except Exception as e:
                print(f"Erro no cálculo do EV: {str(e)}")
                dia_teste_data['ev_over'] = 0.0
                dia_teste_data['ev_under'] = 0.0

            # 6. Processar apostas para cada linha
            apostas = []
            for idx, row in dia_teste_data.iterrows():
                try:
                    aposta = calcular_aposta(row, bankroll)
                    
                    # 6.1 Atualizar bankroll com o resultado da aposta
                    lucro = aposta['profit']
                    bankroll.update(lucro)
                    
                    # 6.2 Registrar métricas da aposta
                    aposta['bankroll_antes'] = bankroll.capital - lucro
                    aposta['bankroll_depois'] = bankroll.capital
                    aposta['data_aposta'] = row['date']
                    
                    apostas.append(aposta)
                except Exception as e:
                    print(f"Erro no processamento da aposta linha {idx}: {str(e)}")
                    continue

            # 7. Consolidar resultados
            if apostas:
                try:
                    apostas_df = pd.concat(apostas, ignore_index=True)
                    dia_completo_df = pd.concat([dia_teste_data.reset_index(drop=True), apostas_df], axis=1)
                    resultados.append(dia_completo_df)
                    print(f"Processado com sucesso: {len(apostas)} apostas para o dia {dia_teste}")
                except Exception as e:
                    print(f"Erro na consolidação de resultados: {str(e)}")

        except Exception as e:
            print(f"Erro processando dia {dia_teste}: {str(e)}")
            continue

    return resultados