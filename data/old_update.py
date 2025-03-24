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