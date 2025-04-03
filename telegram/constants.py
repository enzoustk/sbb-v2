# pyright: reportUndefinedVariable=false

TELEGRAM_BOT_TOKEN = "7694829289:AAF3xDQ0qXQHy5Zbf-QD_Zv5K4RnT2lyx8Q"
TELEGRAM_CHAT_ID = -1002305899864

"""
Chat Individual do Telegram - Enzo  = 6045850973
Chat ID Grupo Teste (Privado) = -1002305899864
Chat ID Telegram STK = -1001563465125
"""


TELEGRAM_MESSAGE = (
    f"🔗 Link: https://www.bet365.com/#/IP/B151\n"
    f"⚽ Times: {home_player} ({home_team}) x {away_player} ({away_team})\n" 
    f"🏆 Liga: {league_text}\n" 
    f"🎯 Aposta: {bet_type} {handicap} {bet_emoji}\n" 
    f"📈 Odd: {odd}\n" 
)

MIN_LINE_MESSAGE =  (
    f"➖ Mínima: {minimum_line} @{minimum_odd}\n"
)

MIN_ODD_MESSAGE =   (
    f"➖ Odd Mín.: {minimum_odd}\n"
)

HOT_TIPS_MESSAGE =  (
    f"\n{'⚠️ EV:'} {hot_emoji}\n"
)

EDITED_MESSAGE =    (
    f'\n{result_emoji}\n'
    f'\n➡ Resultado:{raw_score}\n'
    f'\n{LINKS_MESSAGE}'
)

LINKS_MESSAGE =     (
    f"[Instagram]({INSTAGRAM_LINK}) | "
    f"[Resultados]({RESULTS_LINK}) | "
    f"[Suporte]({SUPPORT_LINK})"
)

INSTAGRAM_LINK = 'https://www.instagram.com/striker.betting/'
RESULTS_LINK = 'https://t.me/StrikerSuporteBot'
SUPPORT_LINK = 'https://linktr.ee/strikerbetting'

RESULT_EMOJIS =     {
    'win': '✅✅✅',
    'half_win': '🔁✅',
    'push': '🔁',
    'half_loss': '🔁❌',
    'loss': '❌',
}

BET_TYPE_EMOJIS =   {
    'over': '⬆️',
    'under': '⬇️',
}
  
REPORT_TITLE = (
    f"Relatório: Striker Betting\n"
    f"Intervalo: {interval}\n"
    f"Liga: {league}\n"
    f"Tipo: {ev_type}\n"
    f"\nSaldo por {period_type} 📅\n"
)

REPORT_BODY = (
    f"{period}: {emoji} {profit}\n"
)

REPORT_TOTAL = (
    f"{bet_type}:\n"
    f"{profit} {total_emoji}\n"
    f"{vol} Tips, {roi:.2%} ROI\n"
    f"Melhor Jogador: {best_player} ({bp_emoji} {bp_profit})\n"
    f"Pior Jogador: {worst_player} ({wp_emoji} {wp_profit})\n"
)

REPORT_TIME_RANGE_TITLE = (
    f"Por Faixa de Horário:\n\n"
)

REPORT_TIME_RANGE_BODY = (
    f"{time_range}: {emoji} {profit}\n"
)