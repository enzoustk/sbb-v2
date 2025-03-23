import requests
import time
import logging
import numpy as np
import pandas as pd
from config import planilha_lock
from datetime import datetime, timedelta
from config import data_lock, csv_atualizado_event
from data_fetch.api_requests import fetch_events_for_date, fetch_live_events
from utils.constants import FILE_PATH, FILE_PATH_APOSTAS_FEITAS, TOKEN, FILE_PATH_CONFRONTOS_IDX, FILE_PATH_JOGADORES_IDX, FILE_PATH_TIMES_IDX

def salvar_aposta_em_xlsx(
    id_evento,
    horario_envio,
    liga,
    time_casa,
    time_fora,
    tipo_aposta,
    handicap_formatado,
    odds,
    ev_percentual,
    message_id,
    linha_minima=None,
    odd_minima=None
):
    
    import pandas as pd, logging
    from config import planilha_lock
    from utils.constants import FILE_PATH_APOSTAS_FEITAS

    with planilha_lock:
        ev_fogo = 0
        if 10 <= ev_percentual < 20:
            ev_fogo = 1
        elif 20 <= ev_percentual < 25:
            ev_fogo = 2
        elif 25 <= ev_percentual < 30:
            ev_fogo = 3
        elif ev_percentual > 30:
            ev_fogo = 4

        # Ajusta o horário para reduzir 3 horas
        horario_envio_ajustado = pd.to_datetime(horario_envio) - pd.Timedelta(hours=3)

        nova_aposta = {
            'ID Evento': [id_evento],
            'Horário Envio': [horario_envio_ajustado],
            'Liga': [liga],
            'Time Casa': [time_casa],
            'Time Fora': [time_fora],
            'Tipo Aposta': [tipo_aposta],
            'Linha': [handicap_formatado],
            'Odd': [odds],
            'EV Percentual': [ev_percentual],
            'Fogo EV': [ev_fogo],
            'ID Mensagem': [message_id],
            'Anulada': None,
            'Placar Final': None,
            'P/L': None,
            'Mensagem Editada': None,

            'Linha Minima': [linha_minima],
            'Odd Minima': [odd_minima],
        }

        try:
            df_existente = pd.read_excel(FILE_PATH_APOSTAS_FEITAS)
            df_nova_aposta = pd.DataFrame(nova_aposta)

            # Remove colunas completamente vazias ou contendo apenas valores NA
            df_existente = df_existente.dropna(how='all', axis=1)
            df_nova_aposta = df_nova_aposta.dropna(how='all', axis=1)

            # Concatena os DataFrames
            df_atualizado = pd.concat([df_existente, df_nova_aposta], ignore_index=True)
        
        except FileNotFoundError:
            logging.warning(f"Arquivo não encontrado: {FILE_PATH_APOSTAS_FEITAS}. Criando um novo arquivo.")
            df_atualizado = pd.DataFrame(nova_aposta)

        df_atualizado.to_excel(FILE_PATH_APOSTAS_FEITAS, index=False)
        logging.info(f"Nova aposta salva em: {FILE_PATH_APOSTAS_FEITAS}")

def calcular_parametros():
    global df_existing
    first_run = True
    while True:
        try:
            with data_lock:
                df_existing = pd.read_csv(FILE_PATH)

                if 'data' in df_existing.columns:
                    df_existing['data'] = pd.to_datetime(df_existing['data'], errors='coerce')
                else:
                    logging.error("'data' column is missing in the DataFrame")
                    continue

                df_existing = df_existing.dropna(subset=['data'])
                latest_game_date = df_existing['data'].max().date()
                now = pd.to_datetime(datetime.now() + timedelta(hours=3))

                all_events = []
                for single_date in pd.date_range(start=latest_game_date, end=now.date()):
                    events = fetch_events_for_date(single_date)
                    all_events.extend(events)

                df_new_events = pd.DataFrame([{
                    'data': datetime.fromtimestamp(int(event['time'])).strftime('%Y-%m-%d %H:%M:%S'),
                    'jogador_fora': event['away']['name'].split('(')[1].split(')')[0].lower() if '(' in event['away']['name'] else '',
                    'gols_fora': event.get('scores', {}).get('2', {}).get('away', np.nan),
                    'jogador_casa': event['home']['name'].split('(')[1].split(')')[0].lower() if '(' in event['home']['name'] else '',
                    'gols_casa': event.get('scores', {}).get('2', {}).get('home', np.nan),
                    'time_casa': event['home']['name'].split('(')[0].strip().lower(),
                    'time_fora': event['away']['name'].split('(')[0].strip().lower()
                } for event in all_events])

                df_new_events['data'] = pd.to_datetime(df_new_events['data'], errors='coerce')
                df_new_events['gols_casa'] = pd.to_numeric(df_new_events['gols_casa'].replace('N/A', np.nan), errors='coerce')
                df_new_events['gols_fora'] = pd.to_numeric(df_new_events['gols_fora'].replace('N/A', np.nan), errors='coerce')
                df_new_events['gols_totais'] = df_new_events['gols_casa'] + df_new_events['gols_fora']

                required_columns = ['data', 'jogador_casa', 'gols_casa', 'jogador_fora', 'gols_fora', 'time_casa', 'time_fora', 'gols_totais']
                for col in required_columns:
                    if col not in df_new_events.columns:
                        df_new_events[col] = np.nan

                df_new_events['identificador_unico'] = (
                    df_new_events['data'].astype(str) + '_' +
                    df_new_events['time_fora'].astype(str) + '_' +
                    df_new_events['jogador_fora'].astype(str) + '_' +
                    df_new_events['gols_fora'].astype(str) + '_' +
                    df_new_events['time_casa'].astype(str) + '_' +
                    df_new_events['jogador_casa'].astype(str) + '_' +
                    df_new_events['gols_casa'].astype(str) + '_' +
                    df_new_events['gols_totais'].astype(str)
                )
                df_new_events = df_new_events.drop_duplicates(subset=['identificador_unico']).reset_index(drop=True)
                df_new_events = df_new_events.drop(columns=['identificador_unico'])

                df_combined = pd.concat([df_existing, df_new_events]).reset_index(drop=True)

                df_combined['jogador_casa'] = df_combined['jogador_casa'].str.lower()
                df_combined['jogador_fora'] = df_combined['jogador_fora'].str.lower()
                df_combined['time_casa'] = df_combined['time_casa'].str.lower()
                df_combined['time_fora'] = df_combined['time_fora'].str.lower()

                jogadores = sorted(list(set(df_combined['jogador_casa'].tolist() + df_combined['jogador_fora'].tolist())))
                times = sorted(list(set(df_combined['time_casa'].tolist() + df_combined['time_fora'].tolist())))
                jogador_index = {jogador: idx for idx, jogador in enumerate(jogadores)}
                time_index = {time: idx for idx, time in enumerate(times)}

                df_combined['idx_jogador_casa'] = df_combined['jogador_casa'].map(jogador_index)
                df_combined['idx_jogador_fora'] = df_combined['jogador_fora'].map(jogador_index)
                df_combined['idx_time_casa'] = df_combined['time_casa'].map(time_index)
                df_combined['idx_time_fora'] = df_combined['time_fora'].map(time_index)

                jogador_df = pd.DataFrame(list(jogador_index.items()), columns=['jogador', 'idx_jogador'])
                time_df = pd.DataFrame(list(time_index.items()), columns=['time', 'idx_time'])

                jogador_df.to_csv(FILE_PATH_JOGADORES_IDX, index=False)
                time_df.to_csv(FILE_PATH_TIMES_IDX, index=False)

                logging.info("Índices de jogadores e times atualizados.")

                df_combined['confronto_key'] = df_combined.apply(
                    lambda row: '_'.join(sorted([row['jogador_casa'], row['jogador_fora']])), axis=1
                )
                confronto_index = {confronto: idx for idx, confronto in enumerate(df_combined['confronto_key'].unique())}

                df_combined['confronto_id'] = df_combined['confronto_key'].map(confronto_index)

                confronto_df = pd.DataFrame(list(confronto_index.items()), columns=['confronto', 'confronto_id'])
                confronto_df.to_csv(FILE_PATH_CONFRONTOS_IDX, index=False)

                logging.info("Índices de confrontos atualizados.")

                df_combined['identificador_unico'] = (
                    df_combined['data'].astype(str) + '_' +
                    df_combined['time_fora'].astype(str) + '_' +
                    df_combined['jogador_fora'].astype(str) + '_' +
                    df_combined['gols_fora'].astype(str) + '_' +
                    df_combined['time_casa'].astype(str) + '_' +
                    df_combined['jogador_casa'].astype(str) + '_' +
                    df_combined['gols_casa'].astype(str) + '_' +
                    df_combined['gols_totais'].astype(str) + '_' +
                    df_combined['idx_jogador_casa'].astype(str) + '_' +
                    df_combined['idx_jogador_fora'].astype(str) + '_' +
                    df_combined['idx_time_casa'].astype(str) + '_' +
                    df_combined['idx_time_fora'].astype(str) + '_' +
                    df_combined['confronto_id'].astype(str)
                )
                df_combined = df_combined.drop_duplicates(subset=['identificador_unico']).reset_index(drop=True)
                df_combined = df_combined.drop(columns=['identificador_unico'])

                df_combined = df_combined.sort_values(by='data').reset_index(drop=True)

                eventos_adicionados = len(df_combined) - len(df_existing)
                print(f"{eventos_adicionados} novos eventos adicionados ao dataframe.")

                df_existing = df_combined
                df_combined.to_csv(FILE_PATH, index=False)
                logging.info("Dataframe atualizado e salvo com sucesso.")

                if first_run:
                    csv_atualizado_event.set()
                    first_run = False

        except Exception as e:
            logging.error(f"Erro ao calcular parâmetros: {e}")
        time.sleep(1800)  # 30 minutos

def adicionar_eventos_novos():
    with planilha_lock:
        try:
            # Carregar a planilha apostas_feitas.xlsx
            df_apostas_feitas = pd.read_excel(FILE_PATH_APOSTAS_FEITAS)

            # Garantir que as colunas necessárias existam
            if 'Placar Final' not in df_apostas_feitas.columns:
                df_apostas_feitas['Placar Final'] = None
            if 'P/L' not in df_apostas_feitas.columns:
                df_apostas_feitas['P/L'] = None
            if 'Anulada' not in df_apostas_feitas.columns:
                df_apostas_feitas['Anulada'] = ""

            # Copiar o DataFrame original para detectar alterações
            df_original = df_apostas_feitas.copy()

            # Converter o ID Evento para string para evitar problemas de tipo
            df_apostas_feitas['ID Evento'] = df_apostas_feitas['ID Evento'].astype(str)

            # Buscar eventos ao vivo
            eventos_ao_vivo = fetch_live_events(TOKEN, sport_id=1)

            # Converter os IDs de eventos ao vivo também para string
            eventos_ao_vivo_ids = {str(event['id']) for event in eventos_ao_vivo}

            eventos_novos = df_apostas_feitas[df_apostas_feitas['Placar Final'].isna()]
            eventos_novos = eventos_novos.drop_duplicates(subset=['ID Evento'])
            eventos_novos = eventos_novos[~eventos_novos['ID Evento'].isin(eventos_ao_vivo_ids)]


            for index, evento in eventos_novos.iterrows():
                try:
                    evento_id = evento['ID Evento']
                    requisitos_cumpridos = []

                    logging.info(f"Processando evento ID: {evento_id}")

                    # Verificar o tempo desde o horário de envio
                    horario_envio = pd.to_datetime(evento['Horário Envio'])
                    if datetime.now() - horario_envio > timedelta(minutes=8):
                        requisitos_cumpridos.append("Há mais de 8min")
                    else:
                        logging.info(f"Evento {evento_id} muito recente. Ignorando por enquanto.")
                        continue

                    # Buscar detalhes do evento na API
                    url_evento = f"https://api.b365api.com/v1/event/view?token={TOKEN}&event_id={evento_id}"
                    response = requests.get(url_evento)
                    response.raise_for_status()
                    data = response.json().get('results', [{}])[0]

                    # Usar o campo 'ss' para determinar o placar final
                    score_final = data.get('ss', None)

                    if score_final and "-" in score_final:
                        home_score, away_score = map(int, score_final.split("-"))
                        requisitos_cumpridos.append(f"Placar final obtido: {home_score}-{away_score}")
                        df_apostas_feitas.at[index, 'Placar Final'] = f"{home_score}-{away_score}"

                        # Determinar o tipo de aposta e calcular o P/L
                        aposta_tipo = 'over' if 'Over' in evento['Tipo Aposta'] else 'under'
                        from bets.betting_logic import calcular_pl
                        pl = calcular_pl(aposta_tipo, float(evento['Linha']), float(evento['Odd']), home_score, away_score)
                        requisitos_cumpridos.append(f"P/L calculado: {pl}")
                        df_apostas_feitas.at[index, 'P/L'] = pl
                    else:
                        logging.warning(f"Placar inválido ou ausente para o evento {evento_id}. "
                                        f"Dados retornados: {data}")
                        continue

                    # Listar os requisitos cumpridos para o evento
                    logging.info(f"Requisitos cumpridos para o evento {evento_id}: {', '.join(requisitos_cumpridos)}")

                except Exception as e:
                    logging.error(f"Erro ao processar evento {evento_id}: {e}")

            # Salvar alterações no arquivo Excel apenas se houver mudança
            if not df_apostas_feitas.equals(df_original):
                df_apostas_feitas.to_excel(FILE_PATH_APOSTAS_FEITAS, index=False)
                logging.info("Arquivo atualizado com novos eventos.")

        except Exception as e:
            logging.error(f"Erro ao adicionar eventos novos: {e}")  