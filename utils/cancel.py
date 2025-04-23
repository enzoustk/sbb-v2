import argparse
from data import load
from object.bet import Bet

parser = argparse.ArgumentParser()
parser.add_argument('message_id')
args = parser.parse_args()


def cancel_bet(message_id):
    csv = load.data('historic')
    csv_filter = (csv['message_id'] == message_id)
    bet_data = csv[csv_filter].iloc[0].to_dict()


    bet = Bet({})
    bet.update_from_dict(bet_data)
    bet.cancel()

cancel_bet(args.message_id)
        