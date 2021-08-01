import calendar
import math
from kiteconnect import KiteTicker, KiteConnect
import threading
import traceback
import datetime
import pandas as pd
import mysql.connector

# if calendar.day_name[datetime.date.today().weekday()] in ['Saturday', 'Sunday']:
#     print("holiday")
#     os.system("shutdown /s /t 1")

acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()

RENKO_temp_columns = ["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"]
ohlc_temp_columns = ["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA", "Gain", "Loss", "Avg_Gain", "Avg_Loss", "RS", "RSI", "PSAR"]
#                       0          1      2       3      4       5       6     7      8      9      10       11        12         13        14    15     16
ha_temp_columns = ["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA", "Gain", "Loss", "Avg_Gain", "Avg_Loss", "RS", "RSI", "PSAR"]
candle_thread_running = ""

trd_portfolio = {
    1152769: {'Trade': "YES", "Market": "NSE", "Segment": "Equity", "Symbol": "MPHASIS", "max_quantity": 1300, 'Direction': "",
              'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
              'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
              'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
              'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
              'margin_multiplier': 8, 'exchange': kite.EXCHANGE_NSE,
              'buffer_quantity': 2, 'round_value': 2, 'tick_size': .05,
              'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 30, 30),
              "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
              'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
              'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
              'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
              'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    2672641: {'Trade': "YES", "Market": "NSE", "Segment": "Equity", "Symbol": "LUPIN", "max_quantity": 1300, 'Direction': "",
              'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
              'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
              'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
              'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
              'margin_multiplier': 8, 'exchange': kite.EXCHANGE_NSE,
              'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
              'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 30, 30),
              "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
              'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
              'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
              'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
              'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    895745: {'Trade': "YES", "Market": "NSE", "Segment": "Equity", "Symbol": "TATASTEEL", "max_quantity": 1300, 'Direction': "",
             'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
             'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
             'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
             'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
             'margin_multiplier': 8, 'exchange': kite.EXCHANGE_NSE,
             'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
             'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 30, 30),
             "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
             'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
             'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
             'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
             'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    1270529: {'Trade': "YES", "Market": "NSE", "Segment": "Equity", "Symbol": "ICICIBANK", "max_quantity": 1300, 'Direction': "",
              'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
              'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
              'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
              'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
              'margin_multiplier': 8, 'exchange': kite.EXCHANGE_NSE,
              'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
              'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 30, 30),
              "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
              'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
              'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
              'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
              'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    4708097: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "RBLBANK", "max_quantity": 2500, 'Direction': "",
              'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
              'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
              'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
              'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
              'margin_multiplier': 5, 'exchange': kite.EXCHANGE_NSE,
              'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
              'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
              "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
              'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
              'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
              'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
              'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    779521: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "SBIN", "max_quantity": 1400, 'Direction': "",
             'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
             'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
             'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
             'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
             'margin_multiplier': 5, 'exchange': kite.EXCHANGE_NSE,
             'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
             'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
             "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
             'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
             'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
             'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
             'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    41729: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "APOLLOTYRE", "max_quantity": 3400, 'Direction': "",
            'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
            'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
            'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
            'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
            'margin_multiplier': 8, 'exchange': kite.EXCHANGE_NSE,
            'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
            'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
            "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
            'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
            'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
            'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
            'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    54273: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "ASHOKLEY", "max_quantity": 4500, 'Direction': "",
            'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
            'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
            'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
            'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
            'margin_multiplier': 5, 'exchange': kite.EXCHANGE_NSE,
            'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
            'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
            "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
            'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
            'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
            'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
            'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    884737: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "TATAMOTORS", "max_quantity": 2000, 'Direction': "",
             'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
             'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
             'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
             'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
             'margin_multiplier': 6, 'exchange': kite.EXCHANGE_NSE,
             'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
             'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
             "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
             'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
             'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
             'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
             'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    60417: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "ASIANPAINT", "max_quantity": 375, 'Direction': "",
            'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
            'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
            'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
            'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
            'margin_multiplier': 9, 'exchange': kite.EXCHANGE_NSE,
            'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
            'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
            "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
            'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
            'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
            'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
            'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    2865921: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "INDIGO", "max_quantity": 400, 'Direction': "",
              'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
              'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
              'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
              'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
              'margin_multiplier': 6, 'exchange': kite.EXCHANGE_NSE,
              'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
              'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
              "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
              'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
              'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
              'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
              'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    1510401: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "AXISBANK", "max_quantity": 850, 'Direction': "",
              'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
              'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
              'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
              'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
              'margin_multiplier': 6, 'exchange': kite.EXCHANGE_NSE,
              'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
              'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
              "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
              'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
              'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
              'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
              'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
    2170625: {'Trade': "NO", "Market": "NSE", "Segment": "Equity", "Symbol": "TVSMOTOR", "max_quantity": 1450, 'Direction': "",
              'Orderid': 0, 'Target_order': '', 'Target_order_id': 0,
              'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050, 'Quantity_multiplier': 1,
              'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003,
              'stt_ctt': 0.00025, 'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003,
              'margin_multiplier': 9, 'exchange': kite.EXCHANGE_NSE,
              'buffer_quantity': 5, 'round_value': 2, 'tick_size': .05,
              'start_time': datetime.time(9, 00, 10), 'end_time': datetime.time(15, 15, 10),
              "lower_circuit_limit": 0, "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0,
              'OHLC_Thread_Running': 'NO', 'DB': '', 'SQL': '',
              'RENKO_temp': pd.DataFrame(columns=RENKO_temp_columns),
              'ohlc_temp': pd.DataFrame(columns=ohlc_temp_columns), 'ha_temp': pd.DataFrame(columns=ha_temp_columns),
              'brick_size': 0, 'up_EP': 0, 'down_EP': 0, 'up_AF': 0.02, 'down_AF': 0.02, 'up_PSAR': 0,  'down_PSAR': 0,  'PSAR_direction': 'None'},
}

ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=ohlc_temp_columns)
ohlc_final_1min = pd.DataFrame(columns=ohlc_temp_columns)
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_Final = pd.DataFrame(columns=RENKO_temp_columns)
HA = {}  # python dictionary to store the ohlc data in it
HA_temp = pd.DataFrame(columns=ha_temp_columns)
HA_Final = pd.DataFrame(columns=ha_temp_columns)

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average, Gain, Loss, Avg_Gain, Avg_Loss, RS, RSI]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0, "Time"]
    HA[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    trd_portfolio[x]['DB'] = mysql.connector.connect(host="127.0.0.1", user="root", passwd="password123", database="testdb", port=3306, connect_timeout=100000)
    trd_portfolio[x]['SQL'] = trd_portfolio[x]['DB'].cursor()


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc(e)


def find_existing_ohlc():
    global ohlc_final_1min
    for items in trd_portfolio:
        trd_portfolio[items]['SQL'].execute(
            "select * from " + str(trd_portfolio[items]['Symbol']) + "_ohlc_final_1min order by time desc limit 20;")
        tup_data = trd_portfolio[items]['SQL'].fetchall()
        data = [list(ele) for ele in tup_data]
        for s in range(len(data)):
            ohlc[items] = data[-(s + 1)]
            trd_portfolio[items]['ohlc_temp'] = pd.DataFrame([ohlc[items]], columns=ohlc_temp_columns)
            ohlc_final_1min = ohlc_final_1min.append(trd_portfolio[items]['ohlc_temp'])
            # ohlc_final_1min.loc[ohlc[items][1], :] = ohlc[items]
        ohlc[items] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    print(ohlc_final_1min)


def find_existing_ha():
    global HA_Final
    for items in trd_portfolio:
        trd_portfolio[items]['SQL'].execute(
            "select * from " + str(trd_portfolio[items]['Symbol']) + "_ha_final order by time desc limit 20;")
        tup_data = trd_portfolio[items]['SQL'].fetchall()
        data = [list(ele) for ele in tup_data]
        for s in range(len(data)):
            HA[items] = data[-(s + 1)]
            trd_portfolio[items]['ha_temp'] = pd.DataFrame([HA[items]], columns=ha_temp_columns)
            HA_Final = HA_Final.append(trd_portfolio[items]['ha_temp'])
            # HA_Final.loc[HA[items][1], :] = HA[items]
        HA[items] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    print(HA_Final)


def find_existing_renko():
    global RENKO_Final
    for items in trd_portfolio:
        trd_portfolio[items]['SQL'].execute(
            "select * from " + str(trd_portfolio[items]['Symbol']) + "_renko_final order by time desc limit 20;")
        tup_data = trd_portfolio[items]['SQL'].fetchall()
        data = [list(ele) for ele in tup_data]
        for s in range(len(data)):
            RENKO[items] = data[-(s + 1)]
            trd_portfolio[items]['RENKO_temp'] = pd.DataFrame([RENKO[items]], columns=RENKO_temp_columns)
            RENKO_Final = RENKO_Final.append(trd_portfolio[items]['RENKO_temp'], sort=False)
            # RENKO_Final.loc[RENKO[items][1], :] = RENKO[items]
    # RENKO[items] = ["Symbol", 0, 0, "Signal", "None", 0, 0, "Time"]
    print(RENKO_Final)


def sma_tma_renko(token):
    trd_portfolio[token]['OHLC_Thread_Running'] = "YES"
    # Calculating SMA
    if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']]) <= 9:
        RENKO[token][5] = 0
    elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']]) > 9:
        d = [RENKO[token][2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-2, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-3, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-4, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-5, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-6, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-7, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-8, 2],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-9, 2]]
        RENKO[token][5] = round(sum(d) / 10, 2)
    # SMA Calculation complete

    # Calculating Triangular moving average
    if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']]) < 9:
        RENKO[token][6] = 0
    elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']]) >= 9:
        e = [RENKO[token][5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-2, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-3, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-4, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-5, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-6, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-7, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-8, 5],
             RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-9, 5]]
        RENKO[token][6] = round((sum(e) / 10), 2)
    RENKO_Final.loc[RENKO[token][1], :] = RENKO[token]
    trd_portfolio[token]['SQL'].execute(
        "INSERT INTO " + str(trd_portfolio[token]['Symbol']) + "_RENKO_Final values (\"" + str(RENKO[token][0]) +
        "\"," + str(RENKO[token][1]) + "," + str(RENKO[token][2]) + ",\"" + str(RENKO[token][3]) + "\",\"" + str(
            RENKO[token][4]) + "\"," +
        str(RENKO[token][5]) + "," + str(RENKO[token][6]) + ",\"" + str(RENKO[token][7]) + "\")")
    trd_portfolio[token]['DB'].commit()
    trd_portfolio[token]['OHLC_Thread_Running'] = "NO"


def del_old_records():
    date = datetime.datetime.now()
    date = date.replace(hour=0, minute=0, second=0)
    date = date.isoformat(' ', 'seconds')
    for items in trd_portfolio:
        trd_portfolio[items]['SQL'].execute(
            "delete FROM testdb." + trd_portfolio[items]['Symbol'] + "_ohlc_final_1min where Time < \"" + str(
                date) + "\";")
        trd_portfolio[items]['DB'].commit()
        trd_portfolio[items]['SQL'].execute(
            "delete FROM testdb." + trd_portfolio[items]['Symbol'] + "_ha_final where Time < \"" + str(date) + "\";")
        trd_portfolio[items]['DB'].commit()
        trd_portfolio[items]['SQL'].execute(
            "delete FROM testdb." + trd_portfolio[items]['Symbol'] + "_renko_final where Time < \"" + str(date) + "\";")
        trd_portfolio[items]['DB'].commit()


del_old_records()


def calculate_ohlc_one_minute(company_data):
    global candle_thread_running, ohlc_temp, HA_temp, ohlc_final_1min, ohlc, HA_Final, HA, RENKO, RENKO_Final
    try:
        # below if condition is to check the data being received, and the data present are of the same minute or not
        trd_portfolio[company_data['instrument_token']]['OHLC_Thread_Running'] = "YES"
        if (str(((company_data["timestamp"]).replace(second=0))) != ohlc[company_data['instrument_token']][1]) and (
                ohlc[company_data['instrument_token']][1] != "Time"):

            # Calculating SMA for Heiken Ashi. Only SMA Calculation for Henken Ashi
            if len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                HA[company_data['instrument_token']][8] = 0
            elif len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                z = [HA[company_data['instrument_token']][5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 5]]
                HA[company_data['instrument_token']][8] = round(sum(z) / 13, 4)
            # SMA Calculation complete for Heiken Ashi

            # Starting to calculate the RSI
            # Calculating the change
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
                change = ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5] - ohlc[company_data['instrument_token']][5]
                # positive change or gain
                if change < 0:
                    ohlc[company_data['instrument_token']][10] = abs(change)
                    ohlc[company_data['instrument_token']][11] = 0
                # negative change or loss
                if change > 0:
                    ohlc[company_data['instrument_token']][11] = abs(change)
                    ohlc[company_data['instrument_token']][10] = 0

            # Calculating average gain and aveage lost
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) == 14:
                Avg_Gain_List = [ohlc[company_data['instrument_token']][10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 10],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-13, 10]]
                ohlc[company_data['instrument_token']][12] = round_down(sum(Avg_Gain_List)/14, 2)
                Avg_Loss_List = [ohlc[company_data['instrument_token']][11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 11],
                                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-13, 11]]
                ohlc[company_data['instrument_token']][13] = round_down(sum(Avg_Loss_List) / 14, 2)
                if ohlc[company_data['instrument_token']][13] == 0:
                    ohlc[company_data['instrument_token']][15] = 100
                else:
                    ohlc[company_data['instrument_token']][14] = round_down(ohlc[company_data['instrument_token']][12] / ohlc[company_data['instrument_token']][13], 2)
                    ohlc[company_data['instrument_token']][15] = round_down(100-(100/(1 + ohlc[company_data['instrument_token']][14])), 2)

            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 15:
                ohlc[company_data['instrument_token']][12] = round_down(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 12] * 13) + ohlc[company_data['instrument_token']][10]) / 14, 2)
                ohlc[company_data['instrument_token']][13] = round_down(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 13] * 13) + ohlc[company_data['instrument_token']][11]) / 14, 2)
                if ohlc[company_data['instrument_token']][13] == 0:
                    ohlc[company_data['instrument_token']][15] = 100
                else:
                    ohlc[company_data['instrument_token']][14] = round_down(ohlc[company_data['instrument_token']][12] / ohlc[company_data['instrument_token']][13], 2)
                    ohlc[company_data['instrument_token']][15] = round_down(100 - (100 / (1 + ohlc[company_data['instrument_token']][14])), 2)

            # Starting to calculate the Parabolic SAR
            # EP calculation for the first time at 5th candle
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) == 4:
                trd_portfolio[company_data['instrument_token']]['up_EP'] = max(ohlc[company_data['instrument_token']][3],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 3],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 3],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 3],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 3])
                trd_portfolio[company_data['instrument_token']]['down_EP'] = min(ohlc[company_data['instrument_token']][4],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 4],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 4],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 4])
                trd_portfolio[company_data['instrument_token']]['up_PSAR'] = trd_portfolio[company_data['instrument_token']]['down_EP']
                trd_portfolio[company_data['instrument_token']]['down_PSAR'] = trd_portfolio[company_data['instrument_token']]['up_EP']

                # taking the above calculated EP and applying to PSAR based on the trend direction
                if ohlc[company_data['instrument_token']][5] > ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5]:
                    ohlc[company_data['instrument_token']][16] = trd_portfolio[company_data['instrument_token']]['up_PSAR']
                    trd_portfolio[company_data['instrument_token']]['PSAR_direction'] = "UP"
                else:
                    ohlc[company_data['instrument_token']][16] = trd_portfolio[company_data['instrument_token']]['down_PSAR']
                    trd_portfolio[company_data['instrument_token']]['PSAR_direction'] = "DOWN"

            # PSAR Calculation when length > 4
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 4:

                trd_portfolio[company_data['instrument_token']]['up_PSAR'] = round_down(min(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4],
                    ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 4],
                    trd_portfolio[company_data['instrument_token']]['up_PSAR'] + trd_portfolio[company_data['instrument_token']]['up_AF'] * (trd_portfolio[company_data['instrument_token']]['up_EP']
                        - trd_portfolio[company_data['instrument_token']]['up_PSAR'])), 2)
                trd_portfolio[company_data['instrument_token']]['down_PSAR'] = round_down(max(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 3],
                    ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 3],
                    trd_portfolio[company_data['instrument_token']]['down_PSAR'] - trd_portfolio[company_data['instrument_token']]['down_AF'] * (trd_portfolio[company_data['instrument_token']]['down_PSAR'] -
                    trd_portfolio[company_data['instrument_token']]['down_EP'])), 2)

                # Up PSAR calculation when the trend is already up
                if trd_portfolio[company_data['instrument_token']]['PSAR_direction'] == "UP":  # if previous PSAR value is "UP"
                    if ohlc[company_data['instrument_token']][4] > trd_portfolio[company_data['instrument_token']]['up_PSAR']:
                        ohlc[company_data['instrument_token']][16] = trd_portfolio[company_data['instrument_token']]['up_PSAR']
                        if ohlc[company_data['instrument_token']][3] > trd_portfolio[company_data['instrument_token']]['up_EP']:
                            trd_portfolio[company_data['instrument_token']]['up_EP'] = ohlc[company_data['instrument_token']][3]
                            trd_portfolio[company_data['instrument_token']]['up_AF'] = trd_portfolio[company_data['instrument_token']]['up_AF'] + 0.01
                    else:
                        trd_portfolio[company_data['instrument_token']]['down_PSAR'] = ohlc[company_data['instrument_token']][16] = trd_portfolio[company_data['instrument_token']]['up_EP']
                        trd_portfolio[company_data['instrument_token']]['down_AF'] = 0.02
                        trd_portfolio[company_data['instrument_token']]['down_EP'] = ohlc[company_data['instrument_token']][4]
                        trd_portfolio[company_data['instrument_token']]['PSAR_direction'] = "DOWN"

                        # Down PSAR calculation when the trend is already down
                if trd_portfolio[company_data['instrument_token']]['PSAR_direction'] == "DOWN":  # if previous PSAR value is "DOWN"
                    if ohlc[company_data['instrument_token']][3] < trd_portfolio[company_data['instrument_token']]['down_PSAR']:
                        ohlc[company_data['instrument_token']][16] = trd_portfolio[company_data['instrument_token']]['down_PSAR']
                        if ohlc[company_data['instrument_token']][4] < trd_portfolio[company_data['instrument_token']]['down_EP']:
                            trd_portfolio[company_data['instrument_token']]['down_EP'] = ohlc[company_data['instrument_token']][4]
                            trd_portfolio[company_data['instrument_token']]['down_AF'] = trd_portfolio[company_data['instrument_token']]['down_AF'] + 0.01
                    else:
                        trd_portfolio[company_data['instrument_token']]['up_PSAR'] = ohlc[company_data['instrument_token']][16] = trd_portfolio[company_data['instrument_token']]['down_EP']
                        trd_portfolio[company_data['instrument_token']]['up_AF'] = 0.02
                        trd_portfolio[company_data['instrument_token']]['up_EP'] = ohlc[company_data['instrument_token']][3]
                        trd_portfolio[company_data['instrument_token']]['PSAR_direction'] = "UP"

            # adding the row into the final ohlc table
            trd_portfolio[company_data['instrument_token']]['ohlc_temp'] = pd.DataFrame(
                [ohlc[company_data['instrument_token']]], columns=ohlc_temp_columns)
            ohlc_final_1min = ohlc_final_1min.append(trd_portfolio[company_data['instrument_token']]['ohlc_temp'])
            # ohlc_final_1min.loc[ohlc[company_data['instrument_token']][1], :] = ohlc[company_data['instrument_token']]
            trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                trd_portfolio[company_data['instrument_token']]['Symbol']) + "_ohlc_final_1min values (\"" + str(
                ohlc[company_data['instrument_token']][0]) + "\",\"" + str(ohlc[company_data['instrument_token']][1]) + "\"," + str(ohlc[company_data['instrument_token']][2]) + "," +
                str(ohlc[company_data['instrument_token']][3]) + "," + str(ohlc[company_data['instrument_token']][4]) + "," + str(ohlc[company_data['instrument_token']][5]) + "," +
                str(ohlc[company_data['instrument_token']][6]) + "," + str(ohlc[company_data['instrument_token']][7]) + "," + str(ohlc[company_data['instrument_token']][8]) + "," +
                str(ohlc[company_data['instrument_token']][9]) + "," + str(ohlc[company_data['instrument_token']][10]) + "," + str(ohlc[company_data['instrument_token']][11]) + "," +
                str(ohlc[company_data['instrument_token']][12]) + "," + str(ohlc[company_data['instrument_token']][13]) + "," + str(ohlc[company_data['instrument_token']][14]) + "," +
                str(ohlc[company_data['instrument_token']][15]) + "," + str(ohlc[company_data['instrument_token']][16]) + ");")
            trd_portfolio[company_data['instrument_token']]['DB'].commit()

            print("PSAR DATA:- Time: " + str(ohlc[company_data['instrument_token']][1]) + ", Symbol: " + str(trd_portfolio[company_data['instrument_token']]['Symbol']) + ", up_EP: " + str(trd_portfolio[company_data['instrument_token']]['up_EP']) + ", down_EP: " + str(trd_portfolio[company_data['instrument_token']]['down_EP']) + ", up_AF " + str(trd_portfolio[company_data['instrument_token']]['up_AF']) + ", down_AF: " + str(trd_portfolio[company_data['instrument_token']]['down_AF']) + ", up_PSAR: " + str(trd_portfolio[company_data['instrument_token']]['up_PSAR']) + ", down_PSAR: " + str(trd_portfolio[company_data['instrument_token']]['down_PSAR']) + ", PSAR_direction: " + str(trd_portfolio[company_data['instrument_token']]['PSAR_direction']) + ", Final PSAR: " + str(ohlc[company_data['instrument_token']][16]))

            # HA_Final.loc[HA[company_data['instrument_token']][1], :] = HA[company_data['instrument_token']]
            trd_portfolio[company_data['instrument_token']]['ha_temp'] = pd.DataFrame(
                [HA[company_data['instrument_token']]], columns=ha_temp_columns)
            HA_Final = HA_Final.append(trd_portfolio[company_data['instrument_token']]['ha_temp'])
            trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                trd_portfolio[company_data['instrument_token']]['Symbol']) + "_HA_Final values (\"" + str(HA[company_data['instrument_token']][0]) + "\",\"" + str(
                HA[company_data['instrument_token']][1]) + "\"," + str(HA[company_data['instrument_token']][2]) + "," + str(HA[company_data['instrument_token']][3]) + "," +
                str(HA[company_data['instrument_token']][4]) + "," + str(HA[company_data['instrument_token']][5]) + "," + str(HA[company_data['instrument_token']][6]) + "," + str(
                HA[company_data['instrument_token']][7]) + "," + str(HA[company_data['instrument_token']][8]) + "," + str(HA[company_data['instrument_token']][9]) + "," +
                str(HA[company_data['instrument_token']][10]) + "," + str(HA[company_data['instrument_token']][11]) + "," + str(HA[company_data['instrument_token']][12]) + "," + str(
                HA[company_data['instrument_token']][13]) + "," + str(HA[company_data['instrument_token']][14]) + "," + str(HA[company_data['instrument_token']][15]) + ");")
            trd_portfolio[company_data['instrument_token']]['DB'].commit()

            # making ohlc for new candle
            ohlc[company_data['instrument_token']][2] = company_data['last_price']  # open
            ohlc[company_data['instrument_token']][3] = company_data['last_price']  # high
            ohlc[company_data['instrument_token']][4] = company_data['last_price']  # low
            ohlc[company_data['instrument_token']][5] = company_data['last_price']  # close
            ohlc[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']

        if ohlc[company_data['instrument_token']][2] == 0:  # assigning open for the first time
            ohlc[company_data['instrument_token']][2] = company_data['last_price']

        if ohlc[company_data['instrument_token']][3] < company_data['last_price']:  # calculating high
            ohlc[company_data['instrument_token']][3] = company_data['last_price']

        if ohlc[company_data['instrument_token']][4] > company_data['last_price'] or \
                ohlc[company_data['instrument_token']][4] == 0:  # calculating low
            ohlc[company_data['instrument_token']][4] = company_data['last_price']

        ohlc[company_data['instrument_token']][5] = company_data['last_price']  # closing price
        ohlc[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
        ohlc[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']

        # Calculating True Range
        if len(ohlc_final_1min.loc[
                   ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
            ohlc[company_data['instrument_token']][6] = round(
                max((abs((ohlc[company_data['instrument_token']][3]) - (ohlc[company_data['instrument_token']][4])),
                     abs((ohlc[company_data['instrument_token']][3]) - (ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 4])),
                     abs((ohlc[company_data['instrument_token']][4]) - (ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 4])))), 2)
        else:
            ohlc[company_data['instrument_token']][6] = round(abs((ohlc[company_data['instrument_token']][3]) - (ohlc[company_data['instrument_token']][4])), 2)
        # True Range Calculation complete for ohlc

        # Calculating ATR for ohlc
        if len(ohlc_final_1min.loc[
                   ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
            ohlc[company_data['instrument_token']][7] = 0
        elif len(ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
            a = [ohlc[company_data['instrument_token']][6], ohlc_final_1min.loc[
                ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 6],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 6]]
            ohlc[company_data['instrument_token']][7] = round(sum(a) / 13, 2)

        # elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 13:
        #     ohlc[company_data['instrument_token']][7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] * 13) +
        #         ohlc[company_data['instrument_token']][6]) / 14, 2)
        # ATR Calculation complete for ohlc

        # Calculating SMA for ohlc
        if len(ohlc_final_1min.loc[
                   ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 10:
            ohlc[company_data['instrument_token']][8] = 0
            # print(len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]))
        elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 10:
            b = [ohlc[company_data['instrument_token']][5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5],
                 ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
            ohlc[company_data['instrument_token']][8] = round(sum(b) / 10, 2)
        # SMA Calculation complete for ohlc

        # Calculating Triangular moving average for ohlc
        if len(ohlc_final_1min.loc[
                   ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 20:
            ohlc[company_data['instrument_token']][9] = 0
        elif len(ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 20:
            c = [ohlc[company_data['instrument_token']][8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 8],
                 ohlc_final_1min.loc[
                     ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 8]]
            ohlc[company_data['instrument_token']][9] = round((sum(c) / 10), 2)
        # TMA calculation complete for ohlc

        # ohlc calculation for HA
        if len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 1:
            if HA[company_data['instrument_token']][0] == "Symbol":
                HA[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
            HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            HA[company_data['instrument_token']][2] = round(
                (ohlc[company_data['instrument_token']][2] + ohlc[company_data['instrument_token']][5]) / 2, 4)
            HA[company_data['instrument_token']][3] = round(ohlc[company_data['instrument_token']][3], 4)
            HA[company_data['instrument_token']][4] = round(ohlc[company_data['instrument_token']][4], 4)
            HA[company_data['instrument_token']][5] = round(
                (ohlc[company_data['instrument_token']][2] + ohlc[company_data['instrument_token']][3] +
                 ohlc[company_data['instrument_token']][4] + ohlc[company_data['instrument_token']][5]) / 4, 4)
        if len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1:
            if HA[company_data['instrument_token']][0] == "Symbol":
                HA[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
            HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            HA[company_data['instrument_token']][5] = round(
                (ohlc[company_data['instrument_token']][2] + ohlc[company_data['instrument_token']][3] +
                 ohlc[company_data['instrument_token']][4] + ohlc[company_data['instrument_token']][5]) / 4, 4)
            HA[company_data['instrument_token']][2] = round((HA_Final.loc[HA_Final.Symbol == trd_portfolio[
                company_data['instrument_token']]['Symbol']].iloc[-1, 2] +
                                                             HA_Final.loc[HA_Final.Symbol == trd_portfolio[
                                                                 company_data['instrument_token']]['Symbol']].iloc[
                                                                 -1, 5]) / 2, 4)
            HA[company_data['instrument_token']][3] = round(
                max(ohlc[company_data['instrument_token']][3], HA[company_data['instrument_token']][2],
                    HA[company_data['instrument_token']][5]), 4)
            HA[company_data['instrument_token']][4] = round(
                min(ohlc[company_data['instrument_token']][4], HA[company_data['instrument_token']][2],
                    HA[company_data['instrument_token']][5]), 4)

        # starting to calculate the RENKO table
        if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:  # or (len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):  # checking if there is atleast 1 candle in OHLC Dataframe or RENKO Dataframe
            if trd_portfolio[company_data['instrument_token']]['brick_size'] == 0:
                trd_portfolio[company_data['instrument_token']]['brick_size'] = ohlc_final_1min.loc[
                                                                                    ohlc_final_1min.Symbol ==
                                                                                    trd_portfolio[company_data[
                                                                                        'instrument_token']][
                                                                                        'Symbol']].iloc[-1, 5] * 0.0015
                print("\nbrick size of " + str(trd_portfolio[company_data['instrument_token']]['Symbol']) + " - " + str(
                    trd_portfolio[company_data['instrument_token']]['brick_size']))
            if trd_portfolio[company_data['instrument_token']]['brick_size'] != 0:
                if RENKO[company_data['instrument_token']][0] == "Symbol":
                    RENKO[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']][
                        'Symbol']
                ########################################################
                if RENKO[company_data['instrument_token']][
                    1] == 0:  # assigning the first, last price of the tick to open
                    RENKO[company_data['instrument_token']][1] = ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5]
                ########################################################
                if RENKO[company_data['instrument_token']][3] == "Signal":
                    if ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 5] >= trd_portfolio[company_data['instrument_token']]['brick_size'] + \
                            RENKO[company_data['instrument_token']][1]:
                        RENKO[company_data['instrument_token']][7] = str(company_data["timestamp"])
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + \
                                                                     trd_portfolio[company_data['instrument_token']][
                                                                         'brick_size']
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        trd_portfolio[company_data['instrument_token']]['RENKO_temp'] = pd.DataFrame(
                            [RENKO[company_data['instrument_token']]],
                            columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"])

                        # Calculating SMA
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) <= 9:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-1, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-2, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-4, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = round(
                                sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) < 19:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-1, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-2, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-4, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = round(
                                (sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(trd_portfolio[company_data['instrument_token']]['RENKO_temp'],
                                                         sort=False)
                        print(trd_portfolio[company_data['instrument_token']]['RENKO_temp'].to_string())
                        trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                            trd_portfolio[company_data['instrument_token']][
                                'Symbol']) + "_RENKO_Final values (\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 0]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 1]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 3]) + "\",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 4]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 7]) + "\")")
                        trd_portfolio[company_data['instrument_token']]['DB'].commit()
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 2]
                    elif ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 5] <= RENKO[company_data['instrument_token']][1] - \
                            trd_portfolio[company_data['instrument_token']]['brick_size']:
                        RENKO[company_data['instrument_token']][7] = str(company_data["timestamp"])
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - \
                                                                     trd_portfolio[company_data['instrument_token']][
                                                                         'brick_size']
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        trd_portfolio[company_data['instrument_token']]['RENKO_temp'] = pd.DataFrame(
                            [RENKO[company_data['instrument_token']]],
                            columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) <= 9:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) > 9:
                            d = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = round(
                                sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) < 19:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) >= 19:
                            e = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = round(
                                (sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(trd_portfolio[company_data['instrument_token']]['RENKO_temp'],
                                                         sort=False)
                        print(trd_portfolio[company_data['instrument_token']]['RENKO_temp'].to_string())
                        trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                            trd_portfolio[company_data['instrument_token']][
                                'Symbol']) + "_RENKO_Final values (\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 0]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 1]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 3]) + "\",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 4]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 7]) + "\")")
                        trd_portfolio[company_data['instrument_token']]['DB'].commit()
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 2]

                if RENKO[company_data['instrument_token']][3] == "BUY":
                    if ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 5] >= trd_portfolio[company_data['instrument_token']]['brick_size'] + \
                            RENKO[company_data['instrument_token']][1]:
                        RENKO[company_data['instrument_token']][7] = str(company_data["timestamp"])
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + \
                                                                     trd_portfolio[company_data['instrument_token']][
                                                                         'brick_size']
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        trd_portfolio[company_data['instrument_token']]['RENKO_temp'] = pd.DataFrame(
                            [RENKO[company_data['instrument_token']]],
                            columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) <= 9:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) > 9:
                            d = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = round(
                                sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) < 19:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) >= 19:
                            e = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = round(
                                (sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(trd_portfolio[company_data['instrument_token']]['RENKO_temp'],
                                                         sort=False)
                        print(trd_portfolio[company_data['instrument_token']]['RENKO_temp'].to_string())
                        trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                            trd_portfolio[company_data['instrument_token']][
                                'Symbol']) + "_RENKO_Final values (\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 0]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 1]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 3]) + "\",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 4]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 7]) + "\")")
                        trd_portfolio[company_data['instrument_token']]['DB'].commit()
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 2]
                    elif ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 5] <= RENKO[company_data['instrument_token']][1] - (RENKO_Final.loc[RENKO_Final.Symbol ==
                                                                                                trd_portfolio[
                                                                                                    company_data[
                                                                                                        'instrument_token']][
                                                                                                    'Symbol']].iloc[
                                                                                    -1, 2] - RENKO_Final.loc[
                                                                                    RENKO_Final.Symbol == trd_portfolio[
                                                                                        company_data[
                                                                                            'instrument_token']][
                                                                                        'Symbol']].iloc[-1, 1]) - \
                            trd_portfolio[company_data['instrument_token']]['brick_size']:
                        RENKO[company_data['instrument_token']][7] = str(company_data["timestamp"])
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol ==
                                                                                     trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] - \
                                                                     trd_portfolio[company_data['instrument_token']][
                                                                         'brick_size']
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        trd_portfolio[company_data['instrument_token']]['RENKO_temp'] = pd.DataFrame(
                            [RENKO[company_data['instrument_token']]],
                            columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) <= 9:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) > 9:
                            d = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = round(
                                sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) < 19:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) >= 19:
                            e = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = round(
                                (sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(trd_portfolio[company_data['instrument_token']]['RENKO_temp'],
                                                         sort=False)
                        print(trd_portfolio[company_data['instrument_token']]['RENKO_temp'].to_string())
                        trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                            trd_portfolio[company_data['instrument_token']][
                                'Symbol']) + "_RENKO_Final values (\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 0]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 1]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 3]) + "\",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 4]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 7]) + "\")")
                        trd_portfolio[company_data['instrument_token']]['DB'].commit()
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 2]
                if RENKO[company_data['instrument_token']][3] == "SELL":
                    if ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 5] <= RENKO[company_data['instrument_token']][1] - \
                            trd_portfolio[company_data['instrument_token']]['brick_size']:
                        RENKO[company_data['instrument_token']][7] = str(company_data["timestamp"])
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - \
                                                                     trd_portfolio[company_data['instrument_token']][
                                                                         'brick_size']
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        trd_portfolio[company_data['instrument_token']]['RENKO_temp'] = pd.DataFrame(
                            [RENKO[company_data['instrument_token']]],
                            columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) <= 9:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) > 9:
                            d = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = round(
                                sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) < 19:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) >= 19:
                            e = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = round(
                                (sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(trd_portfolio[company_data['instrument_token']]['RENKO_temp'],
                                                         sort=False)
                        print(trd_portfolio[company_data['instrument_token']]['RENKO_temp'].to_string())
                        trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                            trd_portfolio[company_data['instrument_token']][
                                'Symbol']) + "_RENKO_Final values (\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 0]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 1]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 3]) + "\",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 4]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 7]) + "\")")
                        trd_portfolio[company_data['instrument_token']]['DB'].commit()
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 2]
                    elif ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 5] >= RENKO[company_data['instrument_token']][1] + (
                            RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 1] - RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2]) + trd_portfolio[company_data['instrument_token']]['brick_size']:
                        RENKO[company_data['instrument_token']][7] = str(company_data["timestamp"])
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol ==
                                                                                     trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] + \
                                                                     trd_portfolio[company_data['instrument_token']][
                                                                         'brick_size']
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        trd_portfolio[company_data['instrument_token']]['RENKO_temp'] = pd.DataFrame(
                            [RENKO[company_data['instrument_token']]],
                            columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA", "Time"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) <= 9:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) > 9:
                            d = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5] = round(
                                sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[
                                   RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                       'Symbol']]) < 19:
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']]) >= 19:
                            e = [trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[
                                     -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6] = round(
                                (sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(trd_portfolio[company_data['instrument_token']]['RENKO_temp'],
                                                         sort=False)
                        print(trd_portfolio[company_data['instrument_token']]['RENKO_temp'].to_string())
                        trd_portfolio[company_data['instrument_token']]['SQL'].execute("INSERT INTO " + str(
                            trd_portfolio[company_data['instrument_token']][
                                'Symbol']) + "_RENKO_Final values (\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 0]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 1]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 2]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 3]) + "\",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 4]) + "\"," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 5]) + "," + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 6]) + ",\"" + str(
                            trd_portfolio[company_data['instrument_token']]['RENKO_temp'].iloc[-1, 7]) + "\")")
                        trd_portfolio[company_data['instrument_token']]['DB'].commit()
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                'Symbol']].iloc[-1, 2]
        trd_portfolio[company_data['instrument_token']]['OHLC_Thread_Running'] = "NO"
    except Exception as e:
        traceback.print_exc(e)
        trd_portfolio[company_data['instrument_token']]['OHLC_Thread_Running'] = "NO"


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    try:
        for company_data in ticks:
            trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
            if trd_portfolio[company_data['instrument_token']]['Trade'] == "YES":
                if trd_portfolio[company_data['instrument_token']]['OHLC_Thread_Running'] == "NO":
                    if trd_portfolio[company_data['instrument_token']]['start_time'] < (
                            company_data['last_trade_time'].time()) < trd_portfolio[company_data['instrument_token']][
                        'end_time']:
                        candle = threading.Thread(target=calculate_ohlc_one_minute, args=(company_data,))
                        candle.start()
    except Exception as e:
        traceback.print_exc(e)


def on_connect(ws, response):
    ws.subscribe([x for x in trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in trd_portfolio])


if __name__ == '__main__':
    # find_existing_ohlc()
    # find_existing_ha()
    # find_existing_renko()
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.connect()
