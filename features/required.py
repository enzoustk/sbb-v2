REQUIRED_COLUMNS = {'home_player', 'away_player', 'total_goals', 'league'}

REQUIRED_FEATURES = [
    
    # Time-based features
    'h2h_count', 'last_h2h', 'time_since_start',
    'day_angle', 'hour_angle',

    # Goal-based features
    'l1', 'l2', 'l3', 
    'median', 'std', 'avg'
    'median_3', 'std_3', 'avg_3',
    'ewma_total_15', 'ewma_total_3',
    'max_5', 'min_5', 'delta_5'
]