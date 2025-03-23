import logging
from datetime import datetime
import pandas as pd
from constants.telegram_params import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.helpers import extrair_nome_jogador, tratar_handicap
from bets.betting_logic import salvar_aposta_em_xlsx
from telegram_message.telegram_bot import enviar_TELEGRAM_MESSAGE
from config import csv_atualizado_event
from features.feature_engineering import calcular_features_ao_vivo
from model.bets import calculate_poisson, find_minimum_line

eventos_com_erro = set()

def predict(evento, model, df_dados):
    global eventos_com_erro

    if not csv_atualizado_event.is_set():
        logging.info("Aguardando a atualização inicial do CSV para iniciar as previsões...")
        csv_atualizado_event.wait()

    # Evita repetir se o evento já falhou
    if evento['id'] in eventos_com_erro:
        return []

    recomendacoes = []
    try:
        hora_identificacao = datetime.now().strftime('%H:%M:%S')
        print(f"Jogo identificado às {hora_identificacao}")

        # Extração dos nomes originais
        time_casa_nome = evento.get('home', {}).get('name')
        time_fora_nome = evento.get('away', {}).get('name')
        odds_reais_over = float(evento['over_od'])
        odds_reais_under = float(evento['under_od'])
        handicap = tratar_handicap(evento.get('handicap', '0'))

        # Nomes em minúsculas para cálculos
        jogador_casa = extrair_nome_jogador(time_casa_nome)
        time_casa_str = time_casa_nome.split('(')[0].strip().lower()
        jogador_fora = extrair_nome_jogador(time_fora_nome)
        time_fora_str = time_fora_nome.split('(')[0].strip().lower()

        #Extração da liga
        liga = evento.get('league', {}).get('name', 'Liga desconhecida')


        # Calcula as features ao vivo usando df_dados, já carregado no scanner
        features = calcular_features_ao_vivo(
            jogador_casa.lower(),
            jogador_fora.lower(),
            time_casa_str,
            time_fora_str,
            df_dados
        )
        if features is None:
            logging.warning("As features calculadas foram insuficientes para prever o evento atual.")
            return recomendacoes

        X_ao_vivo = pd.DataFrame([features])
        required_features = [
            'h2h_count', 'l1', 'l2', 'l3',
            'mediana_3', 'std_3', 'media_3', 'moda_3',
            'ewma_total_15', 'ewma_total_3',
            'mediana_total', 'std_total', 'media_total', 'moda_total',
            'day_of_week', 'hour_of_day', 'day_sin', 'day_cos', 'hour_sin', 'hour_cos',
            'tempo_dia_zero'
        ]
        X_ao_vivo = X_ao_vivo[required_features]

        print('\n' + '-' * 60)
        print("Dados reais usados para previsão (X_ao_vivo):")
        print(X_ao_vivo.to_string(index=False))
        print('-' * 60 + '\n')

        # Faz a previsão
        gols_previstos = model.predict(X_ao_vivo)[0]

        # Probabilidades via distribuição de Poisson
        prob_over, prob_under = calculate_poisson(gols_previstos, handicap)

        # Cálculo de EV
        ev_over = odds_reais_over * prob_over - 1
        ev_under = odds_reais_under * prob_under - 1

        # Logs
        print(f"Liga: {liga}")
        print(f"{jogador_casa} ({time_casa_str}) vs {jogador_fora} ({time_fora_str})")
        print('-' * 20)
        print(f"Lambda: {gols_previstos}")
        print(f"Linha: {handicap}")
        print('-' * 20)
        print(f"Probabilidade Over: {prob_over*100:.2f}%")
        print(f"Probabilidade Under: {prob_under*100:.2f}%")
        print(f"EV Over: {ev_over*100:.2f}%")
        print(f"EV Under: {ev_under*100:.2f}%")
        print('-' * 60)

        # Condições de aposta
        lm_over_ev005 = None
        lm_under_ev005 = None

        # Over ≥5%
        if ev_over >= 0.05:
            recomendacoes.append(("Over", f"{handicap}", ev_over, odds_reais_over))
            # Calcula linha mínima (EV=0.05) para Over
            lm_over_ev005 = find_minimum_line(
                lambda_pred=gols_previstos,
                handicap_inicial=handicap,
                ev_alvo=0.05,
                tipo_aposta="over",
                max_steps=10
            )

        # Under ≥5%
        if ev_under >= 0.05:
            recomendacoes.append(("Under", f"{handicap}", ev_under, odds_reais_under))
            # Calcula linha mínima (EV=0.05) para Under
            lm_under_ev005 = find_minimum_line(
                lambda_pred=gols_previstos,
                handicap_inicial=handicap,
                ev_alvo=0.05,
                tipo_aposta="under",
                max_steps=10
            )

        if not recomendacoes:
            print("Sem apostas no Evento")
            return recomendacoes

        # Montar mensagem Telegram
        jogador_casa_original = (
            time_casa_nome.split('(')[1].split(')')[0] if '(' in time_casa_nome else jogador_casa
        )
        jogador_fora_original = (
            time_fora_nome.split('(')[1].split(')')[0] if '(' in time_fora_nome else jogador_fora
        )

        mensagem = (
            f"🔗 Link: https://www.bet365.com/#/IP/B151\n"
            f"⚽ Times: {jogador_casa_original} ({time_casa_nome.split('(')[0].strip()}) "
            f"x {jogador_fora_original} ({time_fora_nome.split('(')[0].strip()})\n"
            f"🏆 Liga: {liga}\n"
        )

        horario_envio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for tipo_aposta, linha, ev, odd in recomendacoes:
            ev_percentual = ev * 100
            direcao_aposta = "⬆" if "Over" in tipo_aposta else "⬇"

            # Descobrir se existe uma linha mínima correspondente
            linha_minima = None
            odd_minima = None

            if tipo_aposta == "Over" and lm_over_ev005:
                linha_minima = lm_over_ev005['linha']
                odd_minima = lm_over_ev005['odd']
            elif tipo_aposta == "Under" and lm_under_ev005:
                linha_minima = lm_under_ev005['linha']
                odd_minima = lm_under_ev005['odd']

            # Montagem do texto de "Odd: x (Min: ...)"
            # Se não existe linha_minima, só mostramos a odd
            if linha_minima is None or odd_minima is None:
                # Sem linha mínima
                odd_str = f"{odd}"
            else:
                # Se a linha principal == linha_minima, ex.: "📈 Odd: 1.925 (Min: 1.89)"
                # Se diferentes, ex.: "📈 Odd: 1.925 (Min: 4.0 @1.89)"
                if float(linha) == float(linha_minima):
                    odd_str = f"{odd} (Min: {odd_minima})"
                else:
                    odd_str = f"{odd} (Min: {linha_minima} @{odd_minima})"

            # Exemplo final:
            # 🎯 Aposta: Under 4.0 ⬇
            # 📈 Odd: 1.925 (Min: 1.89)
            mensagem += (
                f"🎯 Aposta: {tipo_aposta} {linha} {direcao_aposta}\n"
                f"📈 Odd: {odd_str}\n"
            )

            # Se EV ≥10%, exibimos "chamas"
            ev_message = ""
            if 10 <= ev_percentual < 20:
                ev_message = "🔥"
            elif 20 <= ev_percentual < 25:
                ev_message = "🔥🔥"
            elif 25 <= ev_percentual < 30:
                ev_message = "🔥🔥🔥"
            elif ev_percentual > 30:
                ev_message = "🔥🔥🔥🔥"

            if ev_percentual >= 10:
                mensagem += f"\n⚠️ EV: {ev_message}\n"

            mensagem += "\n"

        # Envio ao Telegram
        message_id = enviar_TELEGRAM_MESSAGE(BOT_TOKEN, CHAT_ID, mensagem)

        # Salvar apostas no XLSX (armazenando linha_minima e odd_minima)
        for tipo_aposta, linha, ev, odd in recomendacoes:
            ev_percentual = ev * 100

            # Descobre a linha mínima novamente
            linha_minima = None
            odd_minima = None
            if tipo_aposta == "Over" and lm_over_ev005:
                linha_minima = lm_over_ev005['linha']
                odd_minima = lm_over_ev005['odd']
            elif tipo_aposta == "Under" and lm_under_ev005:
                linha_minima = lm_under_ev005['linha']
                odd_minima = lm_under_ev005['odd']

            # Salva no Excel apenas a aposta principal (linha == handicap)
            if float(linha) == float(handicap):
                salvar_aposta_em_xlsx(
                    id_evento=evento['id'],
                    horario_envio=horario_envio,
                    liga=liga,
                    time_casa=time_casa_nome,
                    time_fora=time_fora_nome,
                    tipo_aposta=tipo_aposta,
                    handicap_formatado=linha,
                    odds=odd,
                    ev_percentual=ev_percentual,
                    message_id=message_id,
                    linha_minima=linha_minima,
                    odd_minima=odd_minima
                )

    except Exception as e:
        eventos_com_erro.add(evento['id'])
        logging.error(
            f"Erro ao fazer previsão para o evento {evento['id']}: {e}. "
            f"Jogador Casa: {jogador_casa} ({time_casa_str}), Jogador Fora: {jogador_fora} ({time_fora_str})"
        )

    return recomendacoes