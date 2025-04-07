EV_THRESHOLD = 0.05 #  Minimum +EV to make a bet
HOT_THRESHOLD = 0.1 #  Minimum +EV to show "⚠️ EV:"
HOT_TIPS_STEP = 0.05 # for each step, adds a "🔥"
MAX_HOT = 4 # Maximum number of "🔥" to show

AJUSTE_FUSO = 3

TIME_RANGES = {
    '00:00 - 03:59': (0, 3),
    '04:00 - 07:59': (4, 7),
    '08:00 - 11:59': (8, 11),
    '12:00 - 15:59': (12, 15),
    '16:00 - 19:59': (16, 19),
    '20:00 - 23:59': (20, 23)
}
