import calendar
import os
from kiteconnect import KiteTicker, KiteConnect
import threading
import traceback
import datetime
import pandas as pd
import mysql.connector

acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()

RENKO_temp_columns = ["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"]

trd_portfolio = {
    1270529: {"Market": "NSE", "Segment": "Equity", "Symbol": "ICICIBANK", "max_quantity": 100, 'Direction': "", 'Orderid': 0,
              'Target_order': '',
              'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050,
              'Quantity_multiplier': 1, 'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003, 'stt_ctt': 0.00025,
              'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003, 'margin_multiplier': 8,
              'exchange': kite.EXCHANGE_NSE, 'buffer_quantity': 5, 'round_value': 2, 'Trade': "YES", 'tick_size': .05,
              'start_time': datetime.time(9, 29, 10), 'end_time': datetime.time(15, 30, 30), "lower_circuit_limit": 0,
              "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0, 'OHLC_Thread_Running': 'NO', 'DB':'', 'SQL': '', 'RENKO_temp':pd.DataFrame(columns=RENKO_temp_columns)},
    4708097: {"Market": "NSE", "Segment": "Equity", "Symbol": "RBLBANK", "max_quantity": 100, 'Direction': "",
              'Orderid': 0,
              'Target_order': '',
              'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050,
              'Quantity_multiplier': 1, 'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003, 'stt_ctt': 0.00025,
              'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003, 'margin_multiplier': 5,
              'exchange': kite.EXCHANGE_NSE, 'buffer_quantity': 5, 'round_value': 2, 'Trade': "YES", 'tick_size': .05,
              'start_time': datetime.time(9, 29, 10), 'end_time': datetime.time(15, 15, 10), "lower_circuit_limit": 0,
              "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0, 'OHLC_Thread_Running': 'NO', 'DB':'', 'SQL': '', 'RENKO_temp':pd.DataFrame(columns=RENKO_temp_columns)}
}

for x in trd_portfolio:
    print(trd_portfolio[x]['RENKO_temp'])

