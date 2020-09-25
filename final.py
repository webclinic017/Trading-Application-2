import math
import socket
from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions
import pandas as pd
from kiteconnect import KiteTicker, KiteConnect
from flask import Flask, request
import os
import datetime
import json
import traceback
from requests.exceptions import ReadTimeout
import time
import threading

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94"  # api_secret
access_token = "Tnir63yOjF9pMQUSEwsFSQmJkRrDFeic"
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
              "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0},
    690691: {"Market": "CDS", "Segment": "Currency", "Symbol": "USDINR20OCTFUT", "max_quantity": 100, 'Direction': "",
              'Orderid': 0,
              'Target_order': '',
              'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050,
              'Quantity_multiplier': 1000, 'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003, 'stt_ctt': 0,
              'buy_tran': 0.000009, 'sell_tran': 0.000009, 'gst': 0.18, 'stamp': 0.000001, 'margin_multiplier': 36,
              'exchange': kite.EXCHANGE_CDS, 'buffer_quantity': 1, 'round_value': 2, 'Trade': "YES", 'tick_size': .0025,
              'start_time': datetime.time(9, 00, 00), 'end_time': datetime.time(14, 45, 00), "lower_circuit_limit": 0,
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
        temp_open_margin = KiteConnect.margins(kite)
        temp_day_margin = temp_open_margin['equity']['net']
        for items in trd_portfolio:
            if trd_portfolio[items]['Segment'] == "Options":  # calculating quantity for options
                maxquantity = min(temp_day_margin / trd_portfolio[items]['LTP'], trd_portfolio[items]['max_quantity'])
                multiplier = 0
                while (multiplier * 75) < maxquantity: # trd_portfolio[items]['max_quantity']:
                    multiplier = multiplier + 1
                else:
                    trd_portfolio[items]['Tradable_quantity'] = (multiplier - 1) * 75
            elif trd_portfolio[items]['Segment'] != "Options":  # calculating quantity for equities
                if trd_portfolio[items]['LTP'] != 0:
                    if ((temp_day_margin * trd_portfolio[items]['margin_multiplier']) / (trd_portfolio[items]['LTP'] * trd_portfolio[items]['Quantity_multiplier'])) - trd_portfolio[items]['buffer_quantity'] < 1:
                        trd_portfolio[items]['Tradable_quantity'] = 0
                        print("a")
                    else:
                        trd_portfolio[items]['Tradable_quantity'] = int(round(min(((day_margin * trd_portfolio[items]['margin_multiplier']) / (trd_portfolio[items]['LTP'] * trd_portfolio[items][
                            'Quantity_multiplier'])) - trd_portfolio[items]['buffer_quantity'],
                                                                                  trd_portfolio[items]['max_quantity']), 0))
                        print("b", trd_portfolio[items]['Tradable_quantity'])
                        print(str(day_margin) + "*" + str(trd_portfolio[items]['margin_multiplier']) + "/" + str(trd_portfolio[items]['LTP']) + "*" + str(trd_portfolio[items][
                            'Quantity_multiplier']) + "-" + str(trd_portfolio[items]['buffer_quantity']), str(trd_portfolio[items]['max_quantity']))
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
    except exceptions.InputException:
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
        global profit_Final, carry_forward
        print("values before target module exe starts: " + str(profit[instrument_token]))
        volume = volume * trd_portfolio[instrument_token]['Quantity_multiplier']
        if status == "COMPLETE":
            profit[instrument_token][0] = symbol
            if transacion_type == "BUY":
                if profit[instrument_token][4] + volume == 0:
                    profit[instrument_token][1] = price
                    profit[instrument_token][4] = volume
                else:
                    profit[instrument_token][1] = ((profit[instrument_token][1] * profit[instrument_token][4]) + (price * volume)) / (profit[instrument_token][4] + volume)
                    profit[instrument_token][4] = profit[instrument_token][4] + volume
            elif transacion_type == "SELL":
                if profit[instrument_token][4] - volume == 0:
                    profit[instrument_token][2] = price
                    profit[instrument_token][4] = volume
                else:
                    profit[instrument_token][2] = ((profit[instrument_token][2] * profit[instrument_token][4]) + (price * volume)) / (profit[instrument_token][4] + volume)
                    profit[instrument_token][4] = profit[instrument_token][4] - volume
            print(profit[instrument_token])
            if (profit[instrument_token][1] != 0) & (profit[instrument_token][2] != 0):
                buy_brokerage = min((profit[instrument_token][1] * volume * trd_portfolio[instrument_token]['buy_brokerage']), 20)
                sell_brokerage = min((profit[instrument_token][2] * volume * trd_portfolio[instrument_token]['sell_brokerage']), 20)
                stt_ctt = profit[instrument_token][2] * volume * trd_portfolio[instrument_token]['stt_ctt']
                buy_tran = profit[instrument_token][1] * volume * trd_portfolio[instrument_token]['buy_tran']
                sell_tran = profit[instrument_token][2] * volume * trd_portfolio[instrument_token]['sell_tran']
                gst = (buy_brokerage + sell_brokerage + buy_tran + sell_tran + stt_ctt) * trd_portfolio[instrument_token][
                    'gst']
                sebi_total = round((profit[instrument_token][1] + profit[instrument_token][2]) * volume * 0.000001, 0)
                stamp_charges = profit[instrument_token][1] * volume * trd_portfolio[instrument_token]['stamp']
                profit[instrument_token][
                    5] = sebi_total + gst + sell_tran + buy_tran + buy_brokerage + sell_brokerage + stamp_charges
                profit[instrument_token][3] = ((profit[instrument_token][2] - profit[instrument_token][1]) * volume) - profit[instrument_token][5]
                profit[instrument_token][6] = profit[instrument_token][3] - profit[instrument_token][5]
                profit_temp = pd.DataFrame([profit[instrument_token]],
                                           columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges",
                                                    "final_profit"])
                profit_Final = profit_Final.append(profit_temp)
                profit_Final.drop_duplicates(keep='first', inplace=True)
                carry_forward = carry_forward + profit[instrument_token][6]
                print(profit_Final.to_string())
                print("Amount made till now: " + str(carry_forward))
                profit[instrument_token] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
                print("the profit list after an order update" + str(profit[instrument_token]))
            for entries in trd_portfolio:
                if profit[entries][4] != 0:
                    traded_price = max(profit[entries][1], profit[entries][2])
                    traded_quantity = abs(profit[entries][4]) * trd_portfolio[entries]['Quantity_multiplier']
                    Brokerage = min(((traded_price * traded_quantity) * trd_portfolio[entries]['buy_brokerage']) * 2, 40)
                    STT = (traded_price * traded_quantity) * trd_portfolio[entries]['stt_ctt']
                    TNXChrgs = ((traded_price * traded_quantity) * 2) * trd_portfolio[entries]['buy_tran']
                    GST = (Brokerage + TNXChrgs) * trd_portfolio[entries]['gst']
                    SEBIChrgs = ((traded_price * 2) * traded_quantity) * 0.000001
                    StampDuty = ((traded_price * 2) * traded_quantity) * trd_portfolio[entries]['stamp']
                    order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty + STT
                    if carry_forward < 0:
                        target_amount = abs((order_charges * -2) + carry_forward) / traded_quantity
                        print("amount to gain in this trade" + str(target_amount))
                    else:
                        target_amount = abs(order_charges * 2) / abs(traded_quantity)
                        print("amount to gain in this trade" + str(target_amount))
                    if profit[entries][4] > 0:
                        trd_portfolio[entries]['Target_amount'] = min(((traded_price + target_amount) - (
                                (traded_price + target_amount) % trd_portfolio[entries]['tick_size'])) + trd_portfolio[entries]['tick_size'], trd_portfolio[entries]['upper_circuit_limit'])
                    elif profit[entries][4] < 0:
                        trd_portfolio[entries]['Target_amount'] = max((traded_price - target_amount) - (
                                (traded_price - target_amount) % trd_portfolio[entries]['tick_size']), trd_portfolio[entries]['upper_circuit_limit'])
                    print("final target price" + str(trd_portfolio[entries]['Target_amount']))
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


app.run(debug=True, host='0.0.0.0', port=80)


def calculate_ohlc_one_minute(company_data):
    try:
        global HA_Final, ohlc_final_1min, RENKO_Final
        # below if condition is to check the data being received, and the data present are of the same minute or not
        candle_thread_running = "YES"
        if (str(((company_data["timestamp"]).replace(second=0))) != ohlc[company_data['instrument_token']][1]) and (
                ohlc[company_data['instrument_token']][1] != "Time"):
            ohlc_temp = pd.DataFrame([ohlc[company_data['instrument_token']]],
                                     columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA",
                                              "TMA"])
            # print(ohlc_temp.head(), ohlc_final_1min.head())
            HA_temp = pd.DataFrame([HA[company_data['instrument_token']]],
                                   columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA",
                                            "TMA"])

            # Calculating SMA for Heiken Ashi
            if len(HA_Final.loc[
                       HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                HA_temp.iloc[-1, 8] = 0
            elif len(HA_Final.loc[
                         HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                z = [HA_temp.iloc[-1, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -10, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -11, 5],
                     HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -12, 5]]
                HA_temp.iloc[-1, 8] = round(sum(z) / 13, 4)
            # SMA Calculation complete for ohlc

            # Calculating True Range
            if len(ohlc_final_1min.loc[
                       ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
                ohlc_temp.iloc[-1, 6] = round(max((abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 3]) - (ohlc_final_1min.loc[
                                                       ohlc_final_1min.Symbol ==
                                                       trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                                       -1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 4]) - (ohlc_final_1min.loc[
                                                       ohlc_final_1min.Symbol ==
                                                       trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                                       -1, 4])))), 2)
            else:
                ohlc_temp.iloc[-1, 6] = round(abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])), 2)
            # True Range Calculation complete for ohlc
            # Calculating ATR for ohlc
            if len(ohlc_final_1min.loc[
                       ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ohlc_temp.iloc[-1, 7] = 0

            elif len(ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol ==
                                                                    trd_portfolio[company_data['instrument_token']][
                                                                        'Symbol']].iloc[-1, 7] * 13) + ohlc_temp.iloc[
                                                   -1, 6]) / 14, 2)
                '''a = [ohlc_temp.iloc[-1, 6], ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 6]]
                ohlc_temp.iloc[-1, 7] = round(sum(a)/13, 2)'''

            '''elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]*13) + ohlc_temp.iloc[-1, 6])/14, 2)'''
            # ATR Calculation complete for ohlc
            # Calculating SMA for ohlc
            if len(ohlc_final_1min.loc[
                       ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 10:
                ohlc_temp.iloc[-1, 8] = 0
            elif len(ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 10:
                b = [ohlc_temp.iloc[-1, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 5],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 5]]
                ohlc_temp.iloc[-1, 8] = round(sum(b) / 10, 2)
            # SMA Calculation complete for ohlc

            # Calculating Triangular moving average for ohlc
            if len(ohlc_final_1min.loc[
                       ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                ohlc_temp.iloc[-1, 9] = 0
            elif len(ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                c = [ohlc_temp.iloc[-1, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 8],
                     ohlc_final_1min.loc[
                         ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 8]]
                ohlc_temp.iloc[-1, 9] = round((sum(c) / 10), 2)
            # TMA calculation complete for ohlc

            # adding the row into the final ohlc table
            ohlc_final_1min = ohlc_final_1min.append(ohlc_temp)
            HA_Final = HA_Final.append(HA_temp)
            print(HA_temp.to_string())
            # print(ohlc_temp.to_string())

        # making ohlc for new candle
        ohlc[company_data['instrument_token']][2] = company_data['last_price']  # open
        ohlc[company_data['instrument_token']][3] = company_data['last_price']  # high
        ohlc[company_data['instrument_token']][4] = company_data['last_price']  # low
        ohlc[company_data['instrument_token']][5] = company_data['last_price']  # close
        ohlc[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']

        if ohlc[company_data['instrument_token']][3] < company_data['last_price']:  # calculating high
            ohlc[company_data['instrument_token']][3] = company_data['last_price']

        if ohlc[company_data['instrument_token']][4] > company_data['last_price'] or \
                ohlc[company_data['instrument_token']][4] == 0:  # calculating low
            ohlc[company_data['instrument_token']][4] = company_data['last_price']

        ohlc[company_data['instrument_token']][5] = company_data['last_price']  # closing price
        ohlc[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))

        if (len(HA_Final.loc[
                    HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 1):
            if HA[company_data['instrument_token']][0] == "Symbol":
                HA[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
            HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            HA[company_data['instrument_token']][2] = round(
                (ohlc[company_data['instrument_token']][2] + ohlc[company_data['instrument_token']][5]) / 2, 4)
            HA[company_data['instrument_token']][3] = round(ohlc[company_data['instrument_token']][3], 4)
            HA[company_data['instrument_token']][4] = round(ohlc[company_data['instrument_token']][4], 4)
            HA[company_data['instrument_token']][5] = round((ohlc[company_data['instrument_token']][2] +
                                                             ohlc[company_data['instrument_token']][3] +
                                                             ohlc[company_data['instrument_token']][4] +
                                                             ohlc[company_data['instrument_token']][5]) / 4, 4)
        if (len(HA_Final.loc[
                    HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1):
            if HA[company_data['instrument_token']][0] == "Symbol":
                HA[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
            HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            HA[company_data['instrument_token']][5] = round((ohlc[company_data['instrument_token']][2] +
                                                             ohlc[company_data['instrument_token']][3] +
                                                             ohlc[company_data['instrument_token']][4] +
                                                             ohlc[company_data['instrument_token']][5]) / 4, 4)
            HA[company_data['instrument_token']][2] = round((HA_Final.loc[HA_Final.Symbol == trd_portfolio[
                company_data['instrument_token']]['Symbol']].iloc[-1, 2] + HA_Final.loc[HA_Final.Symbol ==
                                                                                        trd_portfolio[company_data[
                                                                                            'instrument_token']][
                                                                                            'Symbol']].iloc[-1, 5]) / 2,
                                                            4)
            HA[company_data['instrument_token']][3] = round(
                max(ohlc[company_data['instrument_token']][3], HA[company_data['instrument_token']][2],
                    HA[company_data['instrument_token']][5]), 4)
            HA[company_data['instrument_token']][4] = round(
                min(ohlc[company_data['instrument_token']][4], HA[company_data['instrument_token']][2],
                    HA[company_data['instrument_token']][5]), 4)

        # starting to calculate the RENKO table
        if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']][
            'Symbol']]) > 0:  # or (len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):  # checking if there is atleast 1 candle in OHLC Dataframe or RENKO Dataframe
            if ohlc_final_1min.loc[
                ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                -1, 7] != 0:  # or (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != [0, 'NaN']):  #checking that we do not have the ATR value as 0
                if RENKO[company_data['instrument_token']][0] == "Symbol":
                    RENKO[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']][
                        'Symbol']
                ########################################################
                if RENKO[company_data['instrument_token']][
                    1] == 0:  # assigning the first, last price of the tick to open
                    RENKO[company_data['instrument_token']][1] = company_data['last_price']
                ########################################################
                if RENKO[company_data['instrument_token']][3] == "Signal":
                    if company_data['last_price'] >= ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7] + RENKO[company_data['instrument_token']][1]:
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + \
                                                                     ohlc_final_1min.loc[ohlc_final_1min.Symbol ==
                                                                                         trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])

                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        # print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7]:
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - \
                                                                     ohlc_final_1min.loc[ohlc_final_1min.Symbol ==
                                                                                         trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        # print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]

                if RENKO[company_data['instrument_token']][3] == "BUY":
                    if company_data['last_price'] >= ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + RENKO[company_data['instrument_token']][1]:
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + \
                                                                     ohlc_final_1min.loc[ohlc_final_1min.Symbol ==
                                                                                         trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        # print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= RENKO[company_data['instrument_token']][1] - (RENKO_Final.loc[
                                                                                                         RENKO_Final.Symbol ==
                                                                                                         trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 2] -
                                                                                                     RENKO_Final.loc[
                                                                                                         RENKO_Final.Symbol ==
                                                                                                         trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 1]) - \
                            ohlc_final_1min.loc[
                                ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']][
                                    'Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol ==
                                                                                     trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] - \
                                                                     ohlc_final_1min.loc[ohlc_final_1min.Symbol ==
                                                                                         trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        # print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                if RENKO[company_data['instrument_token']][3] == "SELL":
                    if company_data['last_price'] <= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[
                        ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7]:
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - \
                                                                     ohlc_final_1min.loc[ohlc_final_1min.Symbol ==
                                                                                         trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        # print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] >= RENKO[company_data['instrument_token']][1] + (RENKO_Final.loc[
                                                                                                         RENKO_Final.Symbol ==
                                                                                                         trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 1] -
                                                                                                     RENKO_Final.loc[
                                                                                                         RENKO_Final.Symbol ==
                                                                                                         trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 2]) + \
                            ohlc_final_1min.loc[
                                ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']][
                                    'Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol ==
                                                                                     trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] + \
                                                                     ohlc_final_1min.loc[ohlc_final_1min.Symbol ==
                                                                                         trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[
                                RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], RENKO_Final.loc[
                                     RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        # print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[
                            RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
        candle_thread_running = "NO"
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
        order_details = kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                if trade_type == 'SELL':
                    trd_portfolio[token]['Direction'] = "Down"
                    trd_portfolio[token]['Target_order'] = "NO"
                    print(trd_portfolio[token]['Direction'])
                    break
                elif trade_type == 'BUY':
                    trd_portfolio[token]['Direction'] = "Up"
                    trd_portfolio[token]['Target_order'] = "NO"
                    print(trd_portfolio[token]['Direction'])
                    break
            elif item['status'] == "REJECTED":
                print("order got rejected", trd_portfolio[token]['Direction'], trd_portfolio[token]['Target_order'])
                break
        else:
            time.sleep(1)
            order_status(token, orderid, type)
    except Exception as e:
        order_status(token, orderid, type)
        traceback.print_exc(e)


def target_order_status(orderid):
    try:
        details = kite.order_history(orderid)
        for item in details:
            if item['status'] == "OPEN":
                return "OPEN"
            elif item['status'] == "REJECTED":
                return "REJECTED"
            elif item['status'] == "COMPLETE":
                return "COMPLETED"
        else:
            time.sleep(1)
            target_order_status(orderid)
    except Exception as e:
        target_order_status(orderid)
        traceback.print_exc(e)


def trigger(token):
    try:
        trigger_thread_running = "YES"
        if len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']]) >= 1:
            if ((HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2]) == (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 3])) and (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] >
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5]) and (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 8] > (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5])):
                print("quantity validation before ordering", str(profit[token][4]))
                if profit[token][4] > 0:
                    kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                      order_type=kite.ORDER_TYPE_MARKET)
                    time.sleep(3)
                    print("exiting current positions")
                elif profit[token][4] == 0:
                    if trd_portfolio[token]['Direction'] != "Down":
                        if trd_portfolio[token]['Tradable_quantity'] > 0:
                            print("Fresh order")
                            trd_portfolio[token]['Orderid'] = kite.place_order(variety="regular",
                                                                               exchange=trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                               quantity=trd_portfolio[token][
                                                                                   'Tradable_quantity'],
                                                                               order_type=kite.ORDER_TYPE_MARKET,
                                                                               product=kite.PRODUCT_MIS)
                            print(trd_portfolio[token]['Orderid'])
                            time.sleep(3)
                            order_status(token, trd_portfolio[token]['Orderid'], 'SELL')
            # BUY Condition
            if (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] ==
                HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 4]) and (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] <
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5]) \
                    and (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 8] < (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5])):
                print("quantity validation before ordering", str(profit[token][4]))
                if profit[token][4] < 0:
                    kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                      order_type=kite.ORDER_TYPE_MARKET)
                    time.sleep(2)
                    print("exiting current positions")
                elif profit[token][4] == 0:
                    if trd_portfolio[token]['Direction'] != "Up":
                        if trd_portfolio[token]['Tradable_quantity'] > 0:
                            print("Fresh order")
                            trd_portfolio[token]['Orderid'] = kite.place_order(variety="regular",
                                                                               exchange=trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                               quantity=trd_portfolio[token][
                                                                                   'Tradable_quantity'],
                                                                               order_type=kite.ORDER_TYPE_MARKET,
                                                                               product=kite.PRODUCT_MIS)
                            print(trd_portfolio[token]['Orderid'])
                            time.sleep(2)
                            order_status(token, trd_portfolio[token]['Orderid'], 'BUY')
            # Below ones are target orders
            print("quantity validation before target set", str(profit[token][4]))
            print(profit[token])
            if profit[token][4] > 0:
                if trd_portfolio[token]['Target_order'] != "YES":
                    trd_portfolio[token]['Target_order_id'] = kite.place_order(variety="regular",
                                                                               exchange=trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                               quantity=abs(
                                                                                   trd_portfolio[token]['Positions']),
                                                                               order_type=kite.ORDER_TYPE_LIMIT,
                                                                               price=round(
                                                                                   trd_portfolio[token]['Target_amount'], 4), product=kite.PRODUCT_MIS)
                    if target_order_status(trd_portfolio[token]['Target_order_id']) == "OPEN":
                        trd_portfolio[token]['Target_order'] = "YES"
            if profit[token][4] < 0:
                if trd_portfolio[token]['Target_order'] != "YES":
                    trd_portfolio[token]['Target_order_id'] = kite.place_order(variety="regular",
                                                                               exchange=trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                               quantity=abs(
                                                                                   trd_portfolio[token]['Positions']),
                                                                               order_type=kite.ORDER_TYPE_LIMIT,
                                                                               price=round_down(
                                                                                   trd_portfolio[token]['Target_amount'], 4),
                                                                               product=kite.PRODUCT_MIS)
                    if target_order_status(trd_portfolio[token]['Target_order_id']) == "OPEN":
                        trd_portfolio[token]['Target_order'] = "YES"
        trigger_thread_running = "NO"
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
    except AttributeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except Exception as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass
    except WantReadError as e:
        trigger_thread_running = "NO"
        pass


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    try:
        for company_data in ticks:
            if trd_portfolio[company_data['instrument_token']]['LTP'] == 0:
                trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
                quantity()
            else:
                trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
            if candle_thread_running != "YES":
                if trd_portfolio[company_data['instrument_token']]['start_time'] < (
                        company_data['last_trade_time'].time()) < trd_portfolio[company_data['instrument_token']]['end_time']:
                    candle = threading.Thread(target=calculate_ohlc_one_minute, args=(company_data,))
                    candle.start()
                    if trd_portfolio[company_data['instrument_token']]['Trade'] == "YES":
                        if ((carry_forward / day_margin) * 100) < 2:
                            if trigger_thread_running != 'YES':
                                if len(HA_Final.loc[
                                           HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                               'Symbol']]) >= 1:
                                    if HA_Final.loc[
                                        HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                            'Symbol']].iloc[-1, 8] != 0:
                                        order_trigger_loop_initiator = threading.Thread(target=trigger, args=[
                                                company_data['instrument_token']])
                                        order_trigger_loop_initiator.start()
    except Exception as e:
        traceback.print_exc(e)


def on_connect(ws, response):
    ws.subscribe([x for x in trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in trd_portfolio])


if __name__ == '__main__':
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.connect()
