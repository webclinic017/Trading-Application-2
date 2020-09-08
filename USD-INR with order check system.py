import logging
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import pandas as pd
import traceback
import requests
from kiteconnect.exceptions import DataException
from requests.exceptions import ReadTimeout
from kiteconnect import exceptions
from urllib.request import *
import json
import numpy as np
import datetime, time, os, random
import math
import threading
import socket
import sys
from datasetup import *

api_k = "dysoztj41hntm1ma";  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94";  # api_secret
access_token = "KbfwyzrmsbF0wJ7g69KzmcQE3IsuYp22"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

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

trd_portfolio = {1077251: {"Symbol": "USDINR20AUGFUT", "max_quantity": 100, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050}
                 }


ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
HA = {}  # python dictionary to store the ohlc data in it
HA_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
HA_Final = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])


def order_function():
    global order_count, profit_temp, profit_Final, carry_forward, last_order_id, last_order_type, last_order_status
    try:
        days_orde = kite.orders()
        days_order = list(filter(lambda i: i['status'] != "REJECTED", days_orde))
        if len(days_order) == 0:
            pass
        elif order_count < len(days_order):
            quantity()
            last_order_id = days_order[-1]['order_id']
            last_order_type = days_order[-1]['transaction_type']
            last_order_status = days_order[-1]['status']
            last_order_price = days_order[-1]['average_price']
            token = days_order[-1]['instrument_token']
            order_count = len(days_order)
            symbol = days_order[-1]['tradingsymbol']
            volume = days_order[-1]['quantity']
            if last_order_status == "COMPLETE":
                if last_order_type == "BUY":
                    profit[token][1] = last_order_price
                elif last_order_type == "SELL":
                    profit[token][2] = last_order_price
                profit[token][0] = symbol
                profit[token][4] = volume
                if (profit[token][1] != 0) and (profit[token][2] != 0):
                    buy_brookerage = min((profit[token][1] * volume * 0.0003), 20)
                    print(buy_brookerage)
                    sell_brookerage = min((profit[token][2] * volume * 0.0003), 20)
                    print(sell_brookerage)
                    # stt_ctt = profit[token][2] * volume * 0.00025
                    buy_tran = profit[token][1] * volume * 0.000009
                    print(buy_tran)
                    sell_tran = profit[token][2] * volume * 0.000009
                    print(sell_tran)
                    gst = (buy_brookerage + sell_brookerage + buy_tran + sell_tran) * 0.18
                    print(gst)
                    sebi_total = round((profit[token][1] + profit[token][2]) * volume * 0.000001, 0)
                    print(sebi_total)
                    stamp_charges = profit[token][1] * volume * 0.000001
                    print(stamp_charges)
                    profit[token][
                        5] = sebi_total + gst + sell_tran + buy_tran + buy_brookerage + sell_brookerage + stamp_charges
                    profit[token][3] = ((profit[token][2] - profit[token][1]) * volume) - profit[token][5]
                    profit[token][6] = profit[token][3] - profit[token][5]
                    profit_temp = pd.DataFrame([profit[token]],
                                               columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges",
                                                        "final_profit"])
                    profit_Final = profit_Final.append(profit_temp)
                    profit_Final.drop_duplicates(keep='first', inplace=True)
                    print(profit_Final)
                    profit[token][1] = 0
                    profit[token][2] = 0
                    carry_forward = carry_forward + profit_Final.iloc[-1, 6]
    except Exception as e:
        traceback.print_exc()

def positions(token):
    try:
        pos = kite.positions()
        # print(pos)
        day_pos = pos['day']
        posdf = pd.DataFrame(day_pos)
        if posdf.empty:
            return 0
        else:
            total_pos = posdf.loc[posdf['instrument_token'] == token, ['quantity']]
            if total_pos.empty:
                return 0
            else:
                current_pos = total_pos.iloc[0, 0]
                return int(current_pos)
    except ReadTimeout:
        traceback.print_exc()
        print("positions read timeout exception")
        positions(token)
        pass
    except socket.timeout:
        traceback.print_exc()
        print("positions socket timeout exception")
        positions(token)
        pass
    except Exception as e:
        traceback.print_exc()

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average, positions ]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    HA[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
    trd_portfolio[x]['Positions'] = positions(x)


'''
def attained_profit():
    try:
        global day_margin, profit_Final, profit_temp, day_profit_percent
        current_profit = 0
        orders = kite.orders()
        for x in orders:
            price = x['average_price']
            symbol = x['tradingsymbol']
            type = x['transaction_type']
            token = x['instrument_token']
            status = x['status']
            volume = x['quantity'] * 1000
            if type == 'BUY' and status == 'COMPLETE':
                profit[token][1] = price
            elif type == 'SELL' and status == 'COMPLETE':
                profit[token][2] = price
            profit[token][0] = symbol
            profit[token][4] = volume
            if (profit[token][1] != 0) & (profit[token][2] != 0):
                buy_brookerage = min((profit[token][1] * volume * 0.0003), 20)
                sell_brookerage = min((profit[token][2] * volume * 0.0003), 20)
                #stt_ctt = profit[token][2] * volume * 0.00025
                buy_tran = profit[token][1] * volume * 0.000009
                sell_tran = profit[token][2] * volume * 0.000009
                gst = (buy_brookerage + sell_brookerage + buy_tran + sell_tran) * 0.18
                sebi_total = round((profit[token][1] + profit[token][2]) * volume * 0.000001, 0)
                stamp_charges = profit[token][1] * volume * 0.000001
                total_charges = sebi_total + gst + sell_tran + buy_tran + buy_brookerage + sell_brookerage + stamp_charges
                profit[token][3] = ((profit[token][2] - profit[token][1]) * volume) - total_charges
                current_profit = current_profit + profit[token][3]
                profit[token][1] = 0
                profit[token][2] = 0
        day_profit_percent = (current_profit / day_margin) * 100
    except Exception as e:
        attained_profit()
        traceback.print_exc()
'''


def quantity():
    global trd_portfolio
    try:
        for stock in trd_portfolio:
            if trd_portfolio[stock]['LTP'] != 0:
                mar = kite.margins()
                equity_mar = mar['equity']['net']
                if (((equity_mar * 36) / (trd_portfolio[stock]['LTP'] * 1000)) * 2) - 1 < 1:
                    trd_portfolio[stock]['Tradable_quantity'] = 0
                else:
                    trd_portfolio[stock]['Tradable_quantity'] = int(round(min((((equity_mar * 36) / (trd_portfolio[stock]['LTP'] * 1000)) * 2) - 1, trd_portfolio[stock]['max_quantity']), 0))
    except DataException:
        quantity()
    except Exception as e:
        traceback.print_exc()


quantity()


def target(orderid, direction):
    global profit_Final, profit_temp, carry_forward
    try:
        Order_data = kite.order_history(orderid)
        for item in Order_data:
            if item['status'] == "COMPLETE":
                traded_price = item['average_price']
                print(traded_price)
                traded_quantity = item['quantity'] * 1000
                print(traded_quantity)
                Brokerage = min(((traded_price * traded_quantity) * 0.0003)*2, 40)
                print(Brokerage)
                #STT = (traded_price * traded_quantity) * (.03 / 100)
                TNXChrgs = ((traded_price * traded_quantity) * 2) * (.000009)
                print(TNXChrgs)
                GST = (Brokerage + TNXChrgs) * 0.18
                print(GST)
                SEBIChrgs = ((traded_price * 2) * traded_quantity) * 0.000001
                print(SEBIChrgs)
                StampDuty = ((traded_price * 2) * traded_quantity) * 0.000001
                print(StampDuty)
                order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty
                print(order_charges)
                if carry_forward < 0:
                    target_amount = abs((order_charges * -2) + carry_forward) / traded_quantity
                    print(target_amount)
                else:
                    target_amount = abs(order_charges * 2)/traded_quantity
                    print(target_amount)
                if direction == "Up":
                    return ((traded_price + target_amount) - ((traded_price + target_amount) % .0025)) + 0.0025
                elif direction == "Down":
                    return (traded_price - target_amount) - ((traded_price - target_amount) % .0025)
    except Exception as e:
        traceback.print_exc()
        target(orderid, direction)


def calculate_ohlc_one_minute(company_data):
    global ohlc_final_1min, ohlc_temp, RENKO_temp, RENKO_Final, candle_thread_running, HA_temp, HA_Final
    try:
        # below if condition is to check the data being received, and the data present are of the same minute or not
        candle_thread_running = "YES"
        if (str(((company_data["timestamp"]).replace(second=0))) != ohlc[company_data['instrument_token']][1]) and (ohlc[company_data['instrument_token']][1] != "Time"):
            ohlc_temp = pd.DataFrame([ohlc[company_data['instrument_token']]], columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
            #print(ohlc_temp.head(), ohlc_final_1min.head())
            HA_temp = pd.DataFrame([HA[company_data['instrument_token']]],
                                   columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA",
                                            "TMA"])

            # Calculating SMA for Heiken Ashi
            if len(HA_Final.loc[
                       HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                HA_temp.iloc[-1, 8] = 0
            elif len(HA_Final.loc[
                         HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                x = [HA_temp.iloc[-1, 5],HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5],
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
                HA_temp.iloc[-1, 8] = round(sum(x) / 13, 4)
            # SMA Calculation complete for ohlc

        # Calculating True Range
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
                ohlc_temp.iloc[-1, 6] = round(max((abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 3]) - (ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 4]) - (ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4])))), 2)
            else:
                ohlc_temp.iloc[-1, 6] = round(abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])), 2)
        # True Range Calculation complete for ohlc
        # Calculating ATR for ohlc
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ohlc_temp.iloc[-1, 7] = 0

            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] * 13) + ohlc_temp.iloc[-1, 6]) / 14, 2)
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
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 10:
                ohlc_temp.iloc[-1, 8] = 0
            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 10:
                b = [ohlc_temp.iloc[-1, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                ohlc_temp.iloc[-1, 8] = round(sum(b) / 10, 2)
        # SMA Calculation complete for ohlc

        # Calculating Triangular moving average for ohlc
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                ohlc_temp.iloc[-1, 9] = 0
            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                c = [ohlc_temp.iloc[-1, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 8]]
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
            HA[company_data['instrument_token']][2] = round((ohlc[company_data['instrument_token']][2] +
                                                       ohlc[company_data['instrument_token']][5]) / 2,4)
            HA[company_data['instrument_token']][3] = round(ohlc[company_data['instrument_token']][3],4)
            HA[company_data['instrument_token']][4] = round(ohlc[company_data['instrument_token']][4],4)
            HA[company_data['instrument_token']][5] = round((ohlc[company_data['instrument_token']][2] +
                                                       ohlc[company_data['instrument_token']][3] +
                                                       ohlc[company_data['instrument_token']][4] +
                                                       ohlc[company_data['instrument_token']][5]) / 4,4)
        if (len(HA_Final.loc[
                        HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1):
            if HA[company_data['instrument_token']][0] == "Symbol":
                HA[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
            HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            HA[company_data['instrument_token']][5] = round((ohlc[company_data['instrument_token']][2] + ohlc[company_data['instrument_token']][3] + ohlc[company_data['instrument_token']][4] + ohlc[company_data['instrument_token']][5])/4,4)
            HA[company_data['instrument_token']][2] = round((HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2] + HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5])/2,4)
            HA[company_data['instrument_token']][3] = round(max(ohlc[company_data['instrument_token']][3], HA[company_data['instrument_token']][2], HA[company_data['instrument_token']][5]),4)
            HA[company_data['instrument_token']][4] = round(min(ohlc[company_data['instrument_token']][4], HA[company_data['instrument_token']][2], HA[company_data['instrument_token']][5]),4)

        #starting to calculate the RENKO table
        if (len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):# or (len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):  # checking if there is atleast 1 candle in OHLC Dataframe or RENKO Dataframe
            if (ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != 0):# or (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != [0, 'NaN']):  #checking that we do not have the ATR value as 0
                if RENKO[company_data['instrument_token']][0] == "Symbol":
                    RENKO[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
                ########################################################
                if RENKO[company_data['instrument_token']][1] == 0:  # assigning the first, last price of the tick to open
                    RENKO[company_data['instrument_token']][1] = company_data['last_price']
                ########################################################
                if RENKO[company_data['instrument_token']][3] == "Signal":
                    if (company_data['last_price'] >= ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + RENKO[company_data['instrument_token']][1]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])

                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif (company_data['last_price']<= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]

                if RENKO[company_data['instrument_token']][3] == "BUY":
                    if (company_data['last_price'] >= ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + RENKO[company_data['instrument_token']][1]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= RENKO[company_data['instrument_token']][1] - (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2] - RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]) - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                if RENKO[company_data['instrument_token']][3] == "SELL":
                    if (company_data['last_price']<= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] >= RENKO[company_data['instrument_token']][1] + (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] - RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]) + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
        candle_thread_running = "NO"
    except Exception as e:
        traceback.print_exc()


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc()


def order_status(token, orderid, type):
    try:
        order_details = kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                if type == 'SELL':
                    trd_portfolio[token]['Direction'] = "Down"
                    trd_portfolio[token]['Target_order'] = "NO"
                    print(trd_portfolio[token]['Direction'])
                    break
                elif type == 'BUY':
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
        traceback.print_exc()

def target_order_status(orderid):
    try:
        details = kite.order_history(orderid)
        for item in details:
            if item['status'] == "OPEN":
                return "OPEN"
                break
            elif item['status'] == "REJECTED":
                return "REJECTED"
                break
            elif item['status'] == "COMPLETE":
                return "COMPLETED"
                break
        else:
            time.sleep(1)
            target_order_status(orderid)
    except Excepton as e:
        target_order_status(orderid)
        traceback.print_exc()

def trigger(token):
    global trigger_thread_running
    try:
        trigger_thread_running = "YES"
        if (len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']]) >= 1):
            trd_portfolio[token]['Positions'] = positions(token)
            if ((HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2]) == (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 3])) and (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] > HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5]) and (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 8] > (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5])):
                if trd_portfolio[token]['Positions'] > 0:
                    kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                      order_type=kite.ORDER_TYPE_MARKET)
                    time.sleep(3)
                    trd_portfolio[token]['Positions'] = positions(token)
                    quantity()
                elif trd_portfolio[token]['Positions'] == 0:
                    if trd_portfolio[token]['Direction'] != "Down":
                        quantity()
                        if trd_portfolio[token]['Tradable_quantity'] > 0:
                            trd_portfolio[token]['Orderid'] = kite.place_order(variety="regular",
                                                                               exchange=kite.EXCHANGE_CDS,
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
                            trd_portfolio[token]['Positions'] = positions(token)
            # BUY Condition
            if (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] ==
                HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 4]) and (
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] <
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5])\
                    and ((HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 8] < (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5]))):
                if trd_portfolio[token]['Positions'] < 0:
                    kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                      order_type=kite.ORDER_TYPE_MARKET)
                    time.sleep(2)
                    trd_portfolio[token]['Positions'] = positions(token)
                    quantity()
                elif trd_portfolio[token]['Positions'] == 0:
                    if trd_portfolio[token]['Direction'] != "Up":
                        quantity()
                        if trd_portfolio[token]['Tradable_quantity'] > 0:
                            trd_portfolio[token]['Orderid'] = kite.place_order(variety="regular",
                                                                               exchange=kite.EXCHANGE_CDS,
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
                            trd_portfolio[token]['Positions'] = positions(token)
            if trd_portfolio[token]['Positions'] > 0:
                if trd_portfolio[token]['Target_order'] != "YES":
                    trd_portfolio[token]['Target_order_id'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_CDS, tradingsymbol=trd_portfolio[token]['Symbol'],
                                     transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=abs(trd_portfolio[token]['Positions']),
                                     order_type=kite.ORDER_TYPE_LIMIT, price=round(target(trd_portfolio[token]['Orderid'], 'Up'), 4), product=kite.PRODUCT_MIS)
                    if target_order_status(trd_portfolio[token]['Target_order_id']) == "OPEN":
                        trd_portfolio[token]['Target_order'] = "YES"
            if trd_portfolio[token]['Positions'] < 0:
                if trd_portfolio[token]['Target_order'] != "YES":
                    trd_portfolio[token]['Target_order_id'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_CDS, tradingsymbol=trd_portfolio[token]['Symbol'],
                                     transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=abs(trd_portfolio[token]['Positions']),
                                     order_type=kite.ORDER_TYPE_LIMIT, price=round_down(target(trd_portfolio[token]['Orderid'], 'Down'), 4), product=kite.PRODUCT_MIS)
                    if target_order_status(trd_portfolio[token]['Target_order_id']) == "OPEN":
                        trd_portfolio[token]['Target_order'] = "YES"
        trigger_thread_running = "NO"
        quantity()
    except TypeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.InputException:
        traceback.print_exc()
        trigger_thread_running = "NO"
    except ReadTimeout:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.NetworkException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except Exception as e:
        traceback.print_exc()
        trigger_thread_running = "NO"


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    global ohlc_final_1min, RENKO_Final, final_position, order_quantity, ohlc_temp, candle_thread_running, trigger_thread_running, last_order_status, last_order_type, order_count, tick_count
    try:
        for company_data in ticks:
            tick_count = tick_count + 1
            if tick_count % 5 == 0:
                order_function()
            trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
            if candle_thread_running != "YES":
                if (company_data['last_trade_time'].time()) > datetime.time(9,00,00) and (company_data['last_trade_time'].time()) < datetime.time(16,45,00):
                    candle = threading.Thread(target=calculate_ohlc_one_minute, args=(company_data,))
                    candle.start()
            if (company_data['last_trade_time'].time()) > datetime.time(9, 15, 00) and (
            company_data['last_trade_time'].time()) < datetime.time(16, 45, 00):
                if (len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1):
                    if HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8] != 0:
                        # Sell Condition
                        if ((HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]) == (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 3])) and (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2] > (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5])) and (
                                HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8] > (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5])):
                            if trd_portfolio[company_data['instrument_token']]['Orderid'] == 0 or \
                                    ((order_count + 2) % 2 == 0 and last_order_status == "COMPLETE" and last_order_type == "SELL"):
                                print(trd_portfolio[company_data['instrument_token']]['Tradable_quantity'])
                                if trd_portfolio[company_data['instrument_token']]['Tradable_quantity'] > 0:
                                    print("quantity available")
                                    trd_portfolio[company_data['instrument_token']]['Orderid'] = kite.place_order(variety="regular",
                                                                                       exchange=kite.EXCHANGE_CDS,
                                                                                       tradingsymbol=
                                                                                       trd_portfolio[company_data['instrument_token']][
                                                                                           'Symbol'],
                                                                                       transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                                       quantity=trd_portfolio[company_data['instrument_token']][
                                                                                           'Tradable_quantity'],
                                                                                       order_type=kite.ORDER_TYPE_MARKET,
                                                                                       product=kite.PRODUCT_MIS)
                                    print(trd_portfolio[company_data['instrument_token']]['Orderid'])
                                    time.sleep(2)
                            if (order_count + 2) % 2 == 0 and last_order_status == "OPEN" and last_order_type == "SELL":
                                print("modify sell order validation successfull")
                                kite.modify_order(variety="regular", order_id=trd_portfolio[company_data['instrument_token']]['Target_order_id'],
                                                  order_type=kite.ORDER_TYPE_MARKET)
                                time.sleep(2)
                        # Buy Condition
                        if (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2] ==
                            HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4]) and (
                                HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5] >
                                HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]) and (
                                HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8] < (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5])):
                            print("buy condition validated")
                            if trd_portfolio[company_data['instrument_token']]['Orderid'] == 0 or \
                                    (order_count + 2) % 2 == 0 and last_order_status == "COMPLETE" and last_order_type == "BUY":
                                print("buy condition validated 2")
                                if trd_portfolio[company_data['instrument_token']]['Tradable_quantity'] > 0:
                                    print("buy quantity available")
                                    trd_portfolio[company_data['instrument_token']]['Orderid'] = kite.place_order(variety="regular",
                                                                                       exchange=kite.EXCHANGE_CDS,
                                                                                       tradingsymbol=trd_portfolio[company_data['instrument_token']][
                                                                                           'Symbol'],
                                                                                       transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                                       quantity=trd_portfolio[company_data['instrument_token']][
                                                                                           'Tradable_quantity'],
                                                                                       order_type=kite.ORDER_TYPE_MARKET,
                                                                                       product=kite.PRODUCT_MIS)
                                    print(trd_portfolio[company_data['instrument_token']]['Orderid'])
                                    time.sleep(2)
                            if (order_count + 2) % 2 == 0 and last_order_status == "OPEN" and last_order_type == "BUY":
                                print("buy modification satisfied")
                                kite.modify_order(variety="regular",
                                                  order_id=trd_portfolio[company_data['instrument_token']]['Target_order_id'],
                                                  order_type=kite.ORDER_TYPE_MARKET)
                        # Target Orders
                        if (order_count + 2) % 2 == 1 and last_order_status == "COMPLETE" and last_order_type == "BUY":
                            print("buy target condition satisfied")
                            trd_portfolio[company_data['instrument_token']]['Target_order_id'] = kite.place_order(variety="regular",
                                                                                       exchange=kite.EXCHANGE_CDS,
                                                                                       tradingsymbol=
                                                                                       trd_portfolio[company_data['instrument_token']][
                                                                                           'Symbol'],
                                                                                       transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                                       quantity=abs(
                                                                                           trd_portfolio[company_data['instrument_token']][
                                                                                               'Positions']),
                                                                                       order_type=kite.ORDER_TYPE_LIMIT,
                                                                                       price=round(target(
                                                                                           trd_portfolio[company_data['instrument_token']][
                                                                                               'Orderid'], 'Up'),
                                                                                                   4),
                                                                                       product=kite.PRODUCT_MIS)
                        if (order_count + 2) % 2 == 1 and last_order_status == "COMPLETE" and \
                                last_order_type == "SELL":
                                print("sell target condition satisfied")
                                trd_portfolio[company_data['instrument_token']]['Target_order_id'] = kite.place_order(variety="regular",
                                                                                           exchange=kite.EXCHANGE_CDS,
                                                                                           tradingsymbol=
                                                                                           trd_portfolio[company_data['instrument_token']][
                                                                                               'Symbol'],
                                                                                           transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                                           quantity=abs(
                                                                                               trd_portfolio[company_data['instrument_token']][
                                                                                                   'Positions']),
                                                                                           order_type=kite.ORDER_TYPE_LIMIT,
                                                                                           price=round_down(target(
                                                                                               trd_portfolio[company_data['instrument_token']][
                                                                                                   'Orderid'], 'Down'),
                                                                                                            4),
                                                                                           product=kite.PRODUCT_MIS)
    except Exception as e:
        traceback.print_exc()


def on_connect(ws, response):
    ws.subscribe([x for x in trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in trd_portfolio])


kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect()