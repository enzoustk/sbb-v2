# pyright: reportUndefinedVariable=false
from bet_bot import escape

TELEGRAM_BET_BOT_TOKEN = "7694829289:AAF3xDQ0qXQHy5Zbf-QD_Zv5K4RnT2lyx8Q"
TELEGRAM_CHAT_ID = -1002305899864

"""
Chat Individual do Telegram - Enzo  = <CHAT_ID>
Chat ID Grupo Teste (Privado) = -1002305899864
Chat ID Telegram STK = -1001563465125
"""


TELEGRAM_MESSAGE = (
    "🔗 Link: https://www.bet365.com/#/IP/B151\n"
    "⚽ Times: {home_player} ({home_team}) x {away_player} ({away_team})\n" 
    "🏆 Liga: {league}\n" 
    "🎯 Aposta: {bet_type} {handicap} {bet_type_emoji}\n" 
    "📈 Odd: {bet_odd}" 
)

MIN_LINE_MESSAGE = (
    "\n➖ Mínima: {minimum_line} @{minimum_odd}\n"
)

MIN_ODD_MESSAGE = (
    " (Mín @{minimum_odd})\n"
)

HOT_TIPS_MESSAGE = (
    "\n⚠️ EV: {hot_emoji}\n"
)

EDITED_MESSAGE = (
    '\n{result_emoji}\n'
    '\n➡ Resultado: {raw_score}\n'
    '\n{LINKS_MESSAGE}'
)

LINKS_DICT = {
    'instagram': 'https://www.instagram.com/striker.betting/',
    'instagram_text': escape.markdown('Instagram'), 
    
    'results': 'https://t.me/StrikerSuporteBot',
    'results_text': escape.markdown('Resultados'),

    'support': 'https://linktr.ee/strikerbetting',
    'support_text': escape.markdown('Suporte'),

    'sep': escape.markdown('|')
}

LINKS_MESSAGE = (
    "[{instagram_text}]({instagram}) {sep} "
    "[{results_text}]({results}) {sep} "
    "[{support_text}]({support})"
).format(**LINKS_DICT)


RESULT_EMOJIS = {
    'win': '✅✅✅',
    'half_win': '🔁✅',
    'push': '🔁',
    'half_loss': '🔁❌',
    'loss': '❌',
}

BET_TYPE_EMOJIS = {
    'over': '⬆️',
    'under': '⬇️',
}
  
REPORT_TITLE = (
    "Relatório: Striker Betting\n"
    "Intervalo: {interval}\n"
    "Liga: {league}\n"
    "Tipo: {ev_type}\n"
    "\nSaldo por {period_type} 📅\n"
)

REPORT_BODY = (
    "{period}: {emoji} {profit}\n"
)

REPORT_TOTAL = (
    "{bet_type}:\n"
    "{profit} {total_emoji}\n"
    "{vol} Tips, {roi:.2%} ROI\n"
    "Melhor Jogador: {best_player} ({bp_emoji} {bp_profit})\n"
    "Pior Jogador: {worst_player} ({wp_emoji} {wp_profit})\n"
)

REPORT_TIME_RANGE_TITLE = (
    "Por Faixa de Horário:\n\n"
)

REPORT_TIME_RANGE_BODY = (
    "{time_range}: {emoji} {profit}\n"
)