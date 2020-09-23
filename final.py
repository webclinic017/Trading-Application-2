import math
import socket
from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions
import pandas as pd
from kiteconnect import KiteTicker, KiteConnect
import datetime
from flask import Flask, request
import os
import datetime
import json
import traceback
from requests.exceptions import ReadTimeout
import time

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94"  # api_secret
access_token = "ybwbzq2nPydxn52ORdT6VoE4gyyKZe9N"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

app = Flask(__name__)

headers = {  # header for API request to update circuit limits
    'Authorization': 'token dysoztj41hntm1ma:' + access_token
}

opening_margin = KiteConnect.margins(kite)
day_margin = opening_margin['equity']['net']

candle_thread_running = ""
trigger_thread_running = ""
day_profit_percent = 0
last_order_id = 0
carry_forward = 0
last_order_type = ''
last_order_status = ''
tick_count = 0
order_count = 0

trd_portfolio = {
    4708097: {"Market": "NSE", "Segment": "Equity", "Symbol": "RBLBANK", "max_quantity": 100, 'Direction': "", 'Orderid': 0,
              'Target_order': '',
              'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050,
              'Quantity_multiplier': 1, 'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003, 'stt_ctt': 0.00025,
              'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003, 'margin_multiplier': 5,
              'exchange': kite.EXCHANGE_NSE, 'buffer_quantity': 5, 'round_value': 2, 'Trade': "YES", 'tick_size': .05,
              'start_time': datetime.time(9, 30, 00), 'end_time': datetime.time(15, 15, 00), "lower_circuit_limit": 0,
              "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0},
    1270529: {"Market": "NSE", "Segment": "Equity", "Symbol": "ICICIBANK", "max_quantity": 100, 'Direction': "", 'Orderid': 0,
              'Target_order': '',
              'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050,
              'Quantity_multiplier': 1, 'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003, 'stt_ctt': 0.00025,
              'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003, 'margin_multiplier': 5,
              'exchange': kite.EXCHANGE_NSE, 'buffer_quantity': 5, 'round_value': 2, 'Trade': "YES", 'tick_size': .05,
              'start_time': datetime.time(9, 30, 00), 'end_time': datetime.time(15, 15, 00), "lower_circuit_limit": 0,
              "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0}}

ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA", "TMA"])
HA = {}  # python dictionary to store the ohlc data in it
HA_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
HA_Final = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(
    columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0,
               0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average, positions ]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    HA[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]  # ["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"]


def quantity():
    try:
        temp_open_margin = KiteConnect.margins(ds.kite)
        temp_day_margin = temp_open_margin['equity']['net']
        for items in ds.trd_portfolio:
            if ds.trd_portfolio[items]['Segment'] == "Options":  # calculating quantity for options
                maxquantity = min(temp_day_margin / ds.trd_portfolio[items]['LTP'], ds.trd_portfolio[items]['max_quantity'])
                multiplier = 0
                while (multiplier * 75) < maxquantity: # ds.trd_portfolio[items]['max_quantity']:
                    multiplier = multiplier + 1
                else:
                    ds.trd_portfolio[items]['Tradable_quantity'] = (multiplier - 1) * 75
            elif ds.trd_portfolio[items]['Segment'] != "Options":  # calculating quantity for equities
                if ds.trd_portfolio[items]['LTP'] != 0:
                    if ((temp_day_margin * ds.trd_portfolio[items]['margin_multiplier']) / (ds.trd_portfolio[items]['LTP'] * ds.trd_portfolio[items]['Quantity_multiplier'])) - ds.trd_portfolio[items]['buffer_quantity'] < 1:
                        ds.trd_portfolio[items]['Tradable_quantity'] = 0
                        print("a")
                    else:
                        ds.trd_portfolio[items]['Tradable_quantity'] = int(round(min(((ds.day_margin * ds.trd_portfolio[items]['margin_multiplier']) / (ds.trd_portfolio[items]['LTP'] * ds.trd_portfolio[items][
                            'Quantity_multiplier'])) - ds.trd_portfolio[items]['buffer_quantity'],
                                                                                  ds.trd_portfolio[items]['max_quantity']), 0))
                        print("b", ds.trd_portfolio[items]['Tradable_quantity'])
                        print(str(ds.day_margin) + "*" + str(ds.trd_portfolio[items]['margin_multiplier']) + "/" + str(ds.trd_portfolio[items]['LTP']) + "*" + str(ds.trd_portfolio[items][
                            'Quantity_multiplier']) + "-" + str(ds.trd_portfolio[items]['buffer_quantity']), str(ds.trd_portfolio[items]['max_quantity']))
    except ReadTimeout:
        traceback.print_exc()
        print("positions read timeout exception")
        trigger_thread_running = "NO"
        pass
    except socket.timeout:
        traceback.print_exc()
        print("positions socket timeout exception")
        trigger_thread_running = "NO"
        pass
    except TypeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except TypeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.InputException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except ReadTimeout:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.NetworkException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except Exception as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass
    except WantReadError as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass


def target(price, symbol, transacion_type, volume, status, instrument_token):
    try:
        print("values before target module exe starts: " + str(ds.profit[instrument_token]))
        volume = volume * ds.trd_portfolio[instrument_token]['Quantity_multiplier']
        if status == "COMPLETE":
            ds.profit[instrument_token][0] = symbol
            if transacion_type == "BUY":
                if ds.profit[instrument_token][4] + volume == 0:
                    ds.profit[instrument_token][1] = price
                    ds.profit[instrument_token][4] = volume
                else:
                    ds.profit[instrument_token][1] = ((ds.profit[instrument_token][1] * ds.profit[instrument_token][4]) + (price * volume)) / (ds.profit[instrument_token][4] + volume)
                    ds.profit[instrument_token][4] = ds.profit[instrument_token][4] + volume
            elif transacion_type == "SELL":
                if ds.profit[instrument_token][4] - volume == 0:
                    ds.profit[instrument_token][2] = price
                    ds.profit[instrument_token][4] = volume
                else:
                    ds.profit[instrument_token][2] = ((ds.profit[instrument_token][2] * ds.profit[instrument_token][4]) + (price * volume)) / (ds.profit[instrument_token][4] + volume)
                    ds.profit[instrument_token][4] = ds.profit[instrument_token][4] - volume
            print(ds.profit[instrument_token])
            if (ds.profit[instrument_token][1] != 0) & (ds.profit[instrument_token][2] != 0):
                buy_brokerage = min((ds.profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['buy_brokerage']), 20)
                sell_brokerage = min((ds.profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['sell_brokerage']), 20)
                stt_ctt = ds.profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['stt_ctt']
                buy_tran = ds.profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['buy_tran']
                sell_tran = ds.profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['sell_tran']
                gst = (buy_brokerage + sell_brokerage + buy_tran + sell_tran + stt_ctt) * ds.trd_portfolio[instrument_token][
                    'gst']
                sebi_total = round((ds.profit[instrument_token][1] + ds.profit[instrument_token][2]) * volume * 0.000001, 0)
                stamp_charges = ds.profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['stamp']
                ds.profit[instrument_token][
                    5] = sebi_total + gst + sell_tran + buy_tran + buy_brokerage + sell_brokerage + stamp_charges
                ds.profit[instrument_token][3] = ((ds.profit[instrument_token][2] - ds.profit[instrument_token][1]) * volume) - ds.profit[instrument_token][5]
                ds.profit[instrument_token][6] = ds.profit[instrument_token][3] - ds.profit[instrument_token][5]
                ds.profit_temp = pd.DataFrame([ds.profit[instrument_token]],
                                           columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges",
                                                    "final_profit"])
                ds.profit_Final = ds.profit_Final.append(ds.profit_temp)
                ds.profit_Final.drop_duplicates(keep='first', inplace=True)
                ds.carry_forward = ds.carry_forward + ds.profit[instrument_token][6]
                print(ds.profit_Final.to_string())
                print("Amount made till now: " + str(ds.carry_forward))
                ds.profit[instrument_token] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
                print("the profit list after an order update" + str(ds.profit[instrument_token]))
            for entries in ds.trd_portfolio:
                if ds.profit[entries][4] != 0:
                    traded_price = max(ds.profit[entries][1], ds.profit[entries][2])
                    traded_quantity = abs(ds.profit[entries][4]) * ds.trd_portfolio[entries]['Quantity_multiplier']
                    Brokerage = min(((traded_price * traded_quantity) * ds.trd_portfolio[entries]['buy_brokerage']) * 2, 40)
                    STT = (traded_price * traded_quantity) * ds.trd_portfolio[entries]['stt_ctt']
                    TNXChrgs = ((traded_price * traded_quantity) * 2) * ds.trd_portfolio[entries]['buy_tran']
                    GST = (Brokerage + TNXChrgs) * ds.trd_portfolio[entries]['gst']
                    SEBIChrgs = ((traded_price * 2) * traded_quantity) * 0.000001
                    StampDuty = ((traded_price * 2) * traded_quantity) * ds.trd_portfolio[entries]['stamp']
                    order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty + STT
                    if ds.carry_forward < 0:
                        target_amount = abs((order_charges * -2) + ds.carry_forward) / traded_quantity
                        print("amount to gain in this trade" + str(target_amount))
                    else:
                        target_amount = abs(order_charges * 2) / abs(traded_quantity)
                        print("amount to gain in this trade" + str(target_amount))
                    if ds.profit[entries][4] > 0:
                        ds.trd_portfolio[entries]['Target_amount'] = min(((traded_price + target_amount) - (
                                (traded_price + target_amount) % ds.trd_portfolio[entries]['tick_size'])) + ds.trd_portfolio[entries]['tick_size'], ds.trd_portfolio[entries]['upper_circuit_limit'])
                    elif ds.profit[entries][4] < 0:
                        ds.trd_portfolio[entries]['Target_amount'] = max((traded_price - target_amount) - (
                                (traded_price - target_amount) % ds.trd_portfolio[entries]['tick_size']), ds.trd_portfolio[entries]['upper_circuit_limit'])
                    print("final target price" + str(ds.trd_portfolio[entries]['Target_amount']))
    except Exception as e:
        traceback.print_exc(e)


def log_name():
    # logs will be saved in files with current date
    return datetime.datetime.now().strftime("%Y-%m-%d") + '.txt'


@app.route('/post', methods=['POST'])
def post():
    # post back json data will be inside request.get_data()
    # as an example here it is being stored to a file
    f = open(log_name(), 'a+')
    order_response = request.get_data()
    f.write(str(order_response) + '\n')
    quantity()
    structured_response = json.loads(order_response)
    print(structured_response['average_price'], structured_response['tradingsymbol'], structured_response['transaction_type'], structured_response['quantity'], structured_response['status'], structured_response['instrument_token'])
    # circuit_limits()
    target(structured_response['average_price'], structured_response['tradingsymbol'], structured_response['transaction_type'], structured_response['quantity'], structured_response['status'], structured_response['instrument_token'])
    f.close()
    return 'done'


@app.route('/')
def index():
    # show the contents of todays log file
    if not os.path.exists(log_name()):
        open(log_name(), 'a+').close()
    return open(log_name()).read()


def calculate_ohlc_one_minute(company_data):
    try:
        # below if condition is to check the data being received, and the data present are of the same minute or not
        ds.candle_thread_running = "YES"
        if (str(((company_data["timestamp"]).replace(second=0))) != ds.ohlc[company_data['instrument_token']][1]) and (
                ds.ohlc[company_data['instrument_token']][1] != "Time"):
            ds.ohlc_temp = pd.DataFrame([ds.ohlc[company_data['instrument_token']]],
                                     columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA",
                                              "TMA"])
            # print(ohlc_temp.head(), ohlc_final_1min.head())
            ds.HA_temp = pd.DataFrame([ds.HA[company_data['instrument_token']]],
                                   columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA",
                                            "TMA"])

            # Calculating SMA for Heiken Ashi
            if len(ds.HA_Final.loc[
                       ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ds.HA_temp.iloc[-1, 8] = 0
            elif len(ds.HA_Final.loc[
                         ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                z = [ds.HA_temp.iloc[-1, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -10, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -11, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -12, 5]]
                ds.HA_temp.iloc[-1, 8] = round(sum(z) / 13, 4)
            # SMA Calculation complete for ohlc

            # Calculating True Range
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
                ds.ohlc_temp.iloc[-1, 6] = round(max((abs((ds.ohlc_temp.iloc[-1, 3]) - (ds.ohlc_temp.iloc[-1, 4])),
                                                   abs((ds.ohlc_temp.iloc[-1, 3]) - (ds.ohlc_final_1min.loc[
                                                       ds.ohlc_final_1min.Symbol ==
                                                       ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                                       -1, 4])),
                                                   abs((ds.ohlc_temp.iloc[-1, 4]) - (ds.ohlc_final_1min.loc[
                                                       ds.ohlc_final_1min.Symbol ==
                                                       ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                                       -1, 4])))), 2)
            else:
                ds.ohlc_temp.iloc[-1, 6] = round(abs((ds.ohlc_temp.iloc[-1, 3]) - (ds.ohlc_temp.iloc[-1, 4])), 2)
            # True Range Calculation complete for ohlc
            # Calculating ATR for ohlc
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ds.ohlc_temp.iloc[-1, 7] = 0

            elif len(ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                ds.ohlc_temp.iloc[-1, 7] = round(((ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                    ds.trd_portfolio[company_data['instrument_token']][
                                                                        'Symbol']].iloc[-1, 7] * 13) + ds.ohlc_temp.iloc[
                                                   -1, 6]) / 14, 2)
                '''a = [ohlc_temp.iloc[-1, 6], ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 6]]
                ohlc_temp.iloc[-1, 7] = round(sum(a)/13, 2)'''

            '''elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) > 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]*13) + ohlc_temp.iloc[-1, 6])/14, 2)'''
            # ATR Calculation complete for ohlc
            # Calculating SMA for ohlc
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 10:
                ds.ohlc_temp.iloc[-1, 8] = 0
            elif len(ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 10:
                b = [ds.ohlc_temp.iloc[-1, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 5]]
                ds.ohlc_temp.iloc[-1, 8] = round(sum(b) / 10, 2)
            # SMA Calculation complete for ohlc

            # Calculating Triangular moving average for ohlc
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                ds.ohlc_temp.iloc[-1, 9] = 0
            elif len(ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                c = [ds.ohlc_temp.iloc[-1, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 8]]
                ds.ohlc_temp.iloc[-1, 9] = round((sum(c) / 10), 2)
            # TMA calculation complete for ohlc

            # adding the row into the final ohlc table
            ds.ohlc_final_1min = ds.ohlc_final_1min.append(ds.ohlc_temp)
            ds.HA_Final = ds.HA_Final.append(ds.HA_temp)
            print(ds.HA_temp.to_string())
            # print(ohlc_temp.to_string())

        # making ohlc for new candle
        ds.ohlc[company_data['instrument_token']][2] = company_data['last_price']  # open
        ds.ohlc[company_data['instrument_token']][3] = company_data['last_price']  # high
        ds.ohlc[company_data['instrument_token']][4] = company_data['last_price']  # low
        ds.ohlc[company_data['instrument_token']][5] = company_data['last_price']  # close
        ds.ohlc[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']]['Symbol']

        if ds.ohlc[company_data['instrument_token']][3] < company_data['last_price']:  # calculating high
            ds.ohlc[company_data['instrument_token']][3] = company_data['last_price']

        if ds.ohlc[company_data['instrument_token']][4] > company_data['last_price'] or \
                ds.ohlc[company_data['instrument_token']][4] == 0:  # calculating low
            ds.ohlc[company_data['instrument_token']][4] = company_data['last_price']

        ds.ohlc[company_data['instrument_token']][5] = company_data['last_price']  # closing price
        ds.ohlc[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))

        if (len(ds.HA_Final.loc[
                    ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 1):
            if ds.HA[company_data['instrument_token']][0] == "Symbol":
                ds.HA[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']]['Symbol']
            ds.HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            ds.HA[company_data['instrument_token']][2] = round(
                (ds.ohlc[company_data['instrument_token']][2] + ds.ohlc[company_data['instrument_token']][5]) / 2, 4)
            ds.HA[company_data['instrument_token']][3] = round(ds.ohlc[company_data['instrument_token']][3], 4)
            ds.HA[company_data['instrument_token']][4] = round(ds.ohlc[company_data['instrument_token']][4], 4)
            ds.HA[company_data['instrument_token']][5] = round((ds.ohlc[company_data['instrument_token']][2] +
                                                             ds.ohlc[company_data['instrument_token']][3] +
                                                             ds.ohlc[company_data['instrument_token']][4] +
                                                             ds.ohlc[company_data['instrument_token']][5]) / 4, 4)
        if (len(ds.HA_Final.loc[
                    ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1):
            if ds.HA[company_data['instrument_token']][0] == "Symbol":
                ds.HA[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']]['Symbol']
            ds.HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            ds.HA[company_data['instrument_token']][5] = round((ds.ohlc[company_data['instrument_token']][2] +
                                                             ds.ohlc[company_data['instrument_token']][3] +
                                                             ds.ohlc[company_data['instrument_token']][4] +
                                                             ds.ohlc[company_data['instrument_token']][5]) / 4, 4)
            ds.HA[company_data['instrument_token']][2] = round((ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[
                company_data['instrument_token']]['Symbol']].iloc[-1, 2] + ds.HA_Final.loc[ds.HA_Final.Symbol ==
                                                                                        ds.trd_portfolio[company_data[
                                                                                            'instrument_token']][
                                                                                            'Symbol']].iloc[-1, 5]) / 2,
                                                            4)
            ds.HA[company_data['instrument_token']][3] = round(
                max(ds.ohlc[company_data['instrument_token']][3], ds.HA[company_data['instrument_token']][2],
                    ds.HA[company_data['instrument_token']][5]), 4)
            ds.HA[company_data['instrument_token']][4] = round(
                min(ds.ohlc[company_data['instrument_token']][4], ds.HA[company_data['instrument_token']][2],
                    ds.HA[company_data['instrument_token']][5]), 4)

        # starting to calculate the ds.RENKO table
        if len(ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']][
            'Symbol']]) > 0:  # or (len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):  # checking if there is atleast 1 candle in OHLC Dataframe or ds.RENKO Dataframe
            if ds.ohlc_final_1min.loc[
                ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                -1, 7] != 0:  # or (ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != [0, 'NaN']):  #checking that we do not have the ATR value as 0
                if ds.RENKO[company_data['instrument_token']][0] == "Symbol":
                    ds.RENKO[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']][
                        'Symbol']
                ########################################################
                if ds.RENKO[company_data['instrument_token']][
                    1] == 0:  # assigning the first, last price of the tick to open
                    ds.RENKO[company_data['instrument_token']][1] = company_data['last_price']
                ########################################################
                if ds.RENKO[company_data['instrument_token']][3] == "Signal":
                    if company_data['last_price'] >= ds.ohlc_final_1min.loc[
                        ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7] + ds.RENKO[company_data['instrument_token']][1]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] + \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "BUY"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])

                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= ds.RENKO[company_data['instrument_token']][1] - ds.ohlc_final_1min.loc[
                        ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] - \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "SELL"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]

                if ds.RENKO[company_data['instrument_token']][3] == "BUY":
                    if company_data['last_price'] >= ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + ds.RENKO[company_data['instrument_token']][1]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] + \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "BUY"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= ds.RENKO[company_data['instrument_token']][1] - (ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 2] -
                                                                                                     ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 1]) - \
                            ds.ohlc_final_1min.loc[
                                ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                    'Symbol']].iloc[-1, 7]:
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO_Final.loc[ds.RENKO_Final.Symbol ==
                                                                                     ds.trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] - \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "SELL"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                if ds.RENKO[company_data['instrument_token']][3] == "SELL":
                    if company_data['last_price'] <= ds.RENKO[company_data['instrument_token']][1] - ds.ohlc_final_1min.loc[
                        ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] - \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "SELL"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] >= ds.RENKO[company_data['instrument_token']][1] + (ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 1] -
                                                                                                     ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 2]) + \
                            ds.ohlc_final_1min.loc[
                                ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                    'Symbol']].iloc[-1, 7]:
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO_Final.loc[ds.RENKO_Final.Symbol ==
                                                                                     ds.trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] + \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "BUY"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
        ds.candle_thread_running = "NO"
    except Exception as e:
        traceback.print_exc(e)


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc(e)


def order_status(token, orderid, trade_type):
    try:
        order_details = ds.kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                if trade_type == 'SELL':
                    ds.trd_portfolio[token]['Direction'] = "Down"
                    ds.trd_portfolio[token]['Target_order'] = "NO"
                    print(ds.trd_portfolio[token]['Direction'])
                    break
                elif trade_type == 'BUY':
                    ds.trd_portfolio[token]['Direction'] = "Up"
                    ds.trd_portfolio[token]['Target_order'] = "NO"
                    print(ds.trd_portfolio[token]['Direction'])
                    break
            elif item['status'] == "REJECTED":
                print("order got rejected", ds.trd_portfolio[token]['Direction'], ds.trd_portfolio[token]['Target_order'])
                break
        else:
            time.sleep(1)
            order_status(token, orderid, type)
    except Exception as e:
        order_status(token, orderid, type)
        traceback.print_exc(e)


app.run(debug=True, host='0.0.0.0', port=80)