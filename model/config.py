EV_THRESHOLD = 0.05 # EV mínimo para enviar uma aposta
HOT_THRESHOLD = 0.1 # EV mínimo para exibir "⚠️ EV:"
HOT_TIPS_STEP = 0.05 # A cada 0.05, adiciona um "🔥"
MAX_HOT = 4 #Quantidade de "🔥"


TIME_RANGES = {
    '00:00 - 03:59': (0, 3),
    '04:00 - 07:59': (4, 7),
    '08:00 - 11:59': (8, 11),
    '12:00 - 15:59': (12, 15),
    '16:00 - 19:59': (16, 19),
    '20:00 - 23:59': (20, 23)
}
