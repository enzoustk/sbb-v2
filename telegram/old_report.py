from datetime import datetime
import logging
import pandas as pd
from constants import FILE_PATH_APOSTAS_FEITAS, BOT_TOKEN, CHAT_ID
from telegram import enviar_mensagem_telegram

def enviar_relatorios():
    from utils import gerar_relatorio

    try:
        df_apostas = pd.read_excel(FILE_PATH_APOSTAS_FEITAS)

        agora = datetime.now()
        mes_atual = agora.month
        ano_atual = agora.year
        df_apostas['data'] = pd.to_datetime(df_apostas['Horário Envio'])
        df_mes_atual = df_apostas[(df_apostas['data'].dt.month == mes_atual) & (df_apostas['data'].dt.year == ano_atual)]

        df_mes_atual.loc[df_mes_atual['Anulada'] == 'sim', 'P/L'] = 0

        df_mes_atual['jogador_casa'] = df_mes_atual['Time Casa'].str.extract(r'\(([^)]+)\)')
        df_mes_atual['jogador_fora'] = df_mes_atual['Time Fora'].str.extract(r'\(([^)]+)\)')

        mensagem_total = gerar_relatorio(df_mes_atual, "Total", "Battle 8min")
        df_hot_tips = df_mes_atual[df_mes_atual['Fogo EV'] >= 1]
        mensagem_hot_tips = gerar_relatorio(df_hot_tips, "Hot Tips 🔥", "Battle 8min")

        for mensagem in [mensagem_total, mensagem_hot_tips]:
            message_id = enviar_mensagem_telegram(BOT_TOKEN, CHAT_ID, mensagem)
            if message_id:
                logging.info(f"Relatório enviado com sucesso: {message_id}")
            else:
                logging.error("Falha ao enviar relatório")
    except Exception as e:
        logging.error(f"Erro ao enviar relatórios: {e}")


def gerar_relatorio(df, nome_relatorio, liga):
    jogadores = pd.concat([df['jogador_casa'], df['jogador_fora']]).unique()
    
    df.loc[:, 'hora'] = pd.to_datetime(df['Horário Envio']).dt.hour
    faixas = {
        "00:00 até 03:59": df[(df['hora'] >= 0) & (df['hora'] < 4)]['P/L'].sum(),
        "04:00 até 07:59": df[(df['hora'] >= 4) & (df['hora'] < 8)]['P/L'].sum(),
        "08:00 até 11:59": df[(df['hora'] >= 8) & (df['hora'] < 12)]['P/L'].sum(),
        "12:00 até 15:59": df[(df['hora'] >= 12) & (df['hora'] < 16)]['P/L'].sum(),
        "16:00 até 19:59": df[(df['hora'] >= 16) & (df['hora'] < 20)]['P/L'].sum(),
        "20:00 até 23:59": df[(df['hora'] >= 20) & (df['hora'] < 24)]['P/L'].sum(),
    }

    df.loc[:, 'data'] = pd.to_datetime(df['Horário Envio'])
    primeiro_dia_do_mes = df['data'].min().replace(day=1)
    ultimo_dia_com_apostas = df['data'].max()
    todas_as_datas = pd.date_range(primeiro_dia_do_mes, ultimo_dia_com_apostas).date

    saldo_por_data = df.groupby(df['data'].dt.date)['P/L'].sum().reindex(todas_as_datas, fill_value=0)

    saldo_por_data_mensagens = "\n".join([
        f"{data.day:02}: {'✅' if saldo > 0 else '❌' if saldo < 0 else '🔄'} {saldo:+.2f}u"
        for data, saldo in saldo_por_data.items()
        if data.month == primeiro_dia_do_mes.month
    ])

    soma_total = df['P/L'].sum()
    entradas = df['P/L'].notnull().sum()
    roi = (soma_total / entradas) * 100 if entradas > 0 else 0
    emoji_total = "🔄" if soma_total == 0 else ("✅" if soma_total > 0 else "❌")
    sinal_total = "+" if soma_total > 0 else ""

    df_over = df[df['Tipo Aposta'].str.contains('Over', case=False)]
    df_under = df[df['Tipo Aposta'].str.contains('Under', case=False)]

    total_over = df_over['P/L'].sum()
    total_under = df_under['P/L'].sum()
    roi_over = (total_over / len(df_over)) * 100 if len(df_over) > 0 else 0
    roi_under = (total_under / len(df_under)) * 100 if len(df_under) > 0 else 0

    # Saldo de jogadores para Over e Under
    saldo_jogadores_over = {
        jogador: df_over[(df_over['jogador_casa'] == jogador) | (df_over['jogador_fora'] == jogador)]['P/L'].sum()
        for jogador in jogadores
    }
    saldo_jogadores_under = {
        jogador: df_under[(df_under['jogador_casa'] == jogador) | (df_under['jogador_fora'] == jogador)]['P/L'].sum()
        for jogador in jogadores
    }

    # Melhor e pior jogador para Over e Under
    melhor_jogador_over = max(saldo_jogadores_over.items(), key=lambda x: x[1])
    pior_jogador_over = min(saldo_jogadores_over.items(), key=lambda x: x[1])
    melhor_jogador_under = max(saldo_jogadores_under.items(), key=lambda x: x[1])
    pior_jogador_under = min(saldo_jogadores_under.items(), key=lambda x: x[1])

    faixa_mensagens = "\n".join([f"{faixa}: {'✅' if pl > 0 else '❌' if pl < 0 else '🔄'} {pl:.2f}u" for faixa, pl in faixas.items()])
    mes_nome = datetime.now().strftime('%B').capitalize()

    mensagem = (
        f"Relatório Mensal: {mes_nome}\n\n"
        f"Tipo: {nome_relatorio}\n"
        f"Liga: {liga}\n\n"
        f"Por Dia 🗓️:\n\n"
        f"{saldo_por_data_mensagens}\n\n"
        f"{emoji_total} Total: {sinal_total}{soma_total:.2f}u | {entradas} Tips | {roi:.2f}% ROI\n\n"
        f"Por Horário ⏰\n\n"
        f"{faixa_mensagens}\n\n"
        f"Por Aposta 🎯:\n\n"
        f"⬆️ Over ⬆️:\n"
        f"Total: {'✅' if total_over > 0 else '❌' if total_over < 0 else '🔄'} {total_over:.2f}u | {len(df_over)} Tips | {roi_over:.2f}% ROI\n"
        f"Melhor jogador: {melhor_jogador_over[0]} ({'✅' if melhor_jogador_over[1] > 0 else '❌'} {melhor_jogador_over[1]:.2f})\n"
        f"Pior jogador: {pior_jogador_over[0]} ({'✅' if pior_jogador_over[1] > 0 else '❌'} {pior_jogador_over[1]:.2f})\n\n"
        f"⬇️ Under ⬇️:\n"
        f"Total: {'✅' if total_under > 0 else '❌' if total_under < 0 else '🔄'} {total_under:.2f}u | {len(df_under)} Tips | {roi_under:.2f}% ROI\n"
        f"Melhor jogador: {melhor_jogador_under[0]} ({'✅' if melhor_jogador_under[1] > 0 else '❌'} {melhor_jogador_under[1]:.2f})\n"
        f"Pior jogador: {pior_jogador_under[0]} ({'✅' if pior_jogador_under[1] > 0 else '❌'} {pior_jogador_under[1]:.2f})"
    )

    return mensagem