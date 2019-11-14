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
access_token = "RpvsXCI9SVqgV0I7Lpf9U4xCYvg9x5Xc"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

trd_portfolio = {60417: {"Symbol": "ASIANPAINT", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 1510401: {"Symbol": "AXISBANK", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 4267265: {"Symbol": "BAJAJ-AUTO", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 4268801: {"Symbol": "BAJAJFINSV", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 81153: {"Symbol": "BAJFINANCE", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 134657: {"Symbol": "BPCL", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 140033: {"Symbol": "BRITANNIA", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 177665: {"Symbol": "CIPLA", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 5215745: {"Symbol": "COALINDIA", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 232961: {"Symbol": "EICHERMOT", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 315393: {"Symbol": "GRASIM", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 1850625: {"Symbol": "HCLTECH", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 340481: {"Symbol": "HDFC", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 341249: {"Symbol": "HDFCBANK", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 345089: {"Symbol": "HEROMOTOCO", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 348929: {"Symbol": "HINDALCO", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 356865: {"Symbol": "HINDUNILVR", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 364545: {"Symbol": "HINDZINC", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 1270529: {"Symbol": "ICICIBANK", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 7458561: {"Symbol": "INFRATEL", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 424961: {"Symbol": "ITC", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 3001089: {"Symbol": "JSWSTEEL", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 492033: {"Symbol": "KOTAKBANK", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 2939649: {"Symbol": "LT", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 2815745: {"Symbol": "MARUTI", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 4598529: {"Symbol": "NESTLEIND", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 633601: {"Symbol": "ONGC", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 3834113: {"Symbol": "POWERGRID", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 779521: {"Symbol": "SBIN", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 895745: {"Symbol": "TATASTEEL", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 2953217: {"Symbol": "TCS", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 3465729: {"Symbol": "TECHM", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 2170625: {"Symbol": "TVSMOTOR", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 2952193: {"Symbol": "ULTRACEMCO", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 969473: {"Symbol": "WIPRO", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 25601: {"Symbol": "AMARAJABAT", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0}}

profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume"])
profit_Final = pd.DataFrame(columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume"])

for x in trd_portfolio:
    profit[x] = ["Symbol", 0, 0, "Profit", 0]

opening_margin = KiteConnect.margins(kite)
day_margin = opening_margin['equity']['net']
print(day_margin)

orders = kite.orders()
overall_profit = 0
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
        overall_profit = overall_profit + profit[token][3]
        profit_temp = pd.DataFrame([profit[token]], columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume"])
        profit_Final = profit_Final.append(profit_temp)
        profit_Final.drop(profit_Final.iloc[0:0], axis=0)
        print(profit_Final)

def day_positions():
    pos = kite.positions()
    day_pos = pos['day']
    posdf = pd.DataFrame(day_pos)
    if posdf.empty:
        return 0
    else:
        return posdf['quantity'].sum()
        '''total_pos = posdf.loc[posdf['instrument_token'] == token, ['quantity']]
        if total_pos.empty:
            return 0
        else:
            current_pos = total_pos.iloc[0, 0]
            return current_pos'''

print(profit_Final)
print(overall_profit)
print(day_positions())
print((overall_profit/day_margin)*100)