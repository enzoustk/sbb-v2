import argparse
from data import load
from object.bet import Bet


parser = argparse.ArgumentParser()
parser.add_argument('message_id', type=str)
parser.add_argument('home_score', type=int)
parser.add_argument('away_score', type=int)
args = parser.parse_args()


def swap_score(message_id, home_score, away_score):
    csv = load.data('historic')
    csv_filter = (csv['message_id'] == message_id)
    bet_data = csv[csv_filter].iloc[0].to_dict()


    bet = Bet({})
    bet.update_from_dict(bet_data)
    bet.swap_score(home_score, away_score)

swap_score(args.message_id, args.home_score, args.away_score)