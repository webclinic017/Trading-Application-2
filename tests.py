import logging
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import pandas as pd
import traceback
import requests
from requests.exceptions import ReadTimeout
from kiteconnect import exceptions
from urllib.request import *
import json
import numpy as np
import datetime, time, os, random
import math

api_k = "dysoztj41hntm1ma";  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94";  # api_secret
access_token = "qgQXadxhn24xhSu0wn8Svrm1OXz5Usxz"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

opening_margin = KiteConnect.margins(kite)
day_margin = opening_margin['equity']['net']

ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])

trd_portfolio = {1510401: {"Symbol": "AXISBANK", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 1195009: {"Symbol": "BANKBARODA", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 94977: {"Symbol": "BATAINDIA", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 140033: {"Symbol": "BRITANNIA", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 177665: {"Symbol": "CIPLA", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 340481: {"Symbol": "HDFC", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 341249: {"Symbol": "HDFCBANK", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 1270529: {"Symbol": "ICICIBANK", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 738561: {"Symbol": "RELIANCE", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 779521: {"Symbol": "SBIN", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 }

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]

def attained_profit():
    global day_margin, profit_Final, profit_temp
    current_profit = 0
    orders = kite.orders()
    for x in orders:
        price = x['average_price']
        symbol = x['tradingsymbol']
        type = x['transaction_type']
        token = x['instrument_token']
        volume = x['quantity']
        if type == 'BUY':
            profit[token][1] = price
        elif type == 'SELL':
            profit[token][2] = price
        profit[token][0] = symbol
        profit[token][4] = volume
        if (profit[token][1] != 0) & (profit[token][2] != 0):
            buy_brookerage = min((profit[token][1] * volume * 0.0001), 20)
            sell_brookerage = min((profit[token][2] * volume * 0.0001), 20)
            stt_ctt = profit[token][2] * volume * 0.00025
            buy_tran = profit[token][1] * volume * 0.0000325
            sell_tran = profit[token][2] * volume * 0.0000325
            gst = (buy_brookerage + sell_brookerage + buy_tran + sell_tran) * 0.18
            sebi_total = round((profit[token][1] + profit[token][2]) * 0.000001, 0)
            total_charges = sebi_total + gst + sell_tran + buy_tran + stt_ctt + buy_brookerage + sell_brookerage
            profit[token][3] = ((profit[token][2] - profit[token][1]) * volume) - total_charges
            current_profit = current_profit + profit[token][3]
            profit[token][1] = 0
            profit[token][2] = 0
    return (current_profit / day_margin) * 100


def positions(token):
    try:
        pos = kite.positions()
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
    except Exception as e:
        traceback.print_exc()


'''print(attained_profit())
print(attained_profit())
print(attained_profit())
print(attained_profit())
print(attained_profit())'''
#orders = kite.orders()
for x in trd_portfolio:
    print(x)


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    global ohlc_final_1min, RENKO_Final, final_position, order_quantity, ohlc_temp, candle_thread_running, renko_thread_running
    try:
        for company_data in ticks:
            print(attained_profit())
    except Exception as e:
        traceback.print_exc()


def on_connect(ws, response):
    ws.subscribe([x for x in trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in trd_portfolio])

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect()