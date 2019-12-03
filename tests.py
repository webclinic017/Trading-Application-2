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
access_token = "p0yUnKMgBmXtHIupn9AE4vbeeVnjSllY"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

trd_portfolio = {779521: {"Symbol": "SBIN", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0}}

ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume"])
profit_Final = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume"])


for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0]

current_profit = 0
orders = kite.orders()
for x in orders:
    print(x)
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
        profit_temp = pd.DataFrame([profit[token]], columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume"])
        profit_Final = profit_Final.append(profit_temp)
        print(profit_Final)
        profit[token][1] = 0
        profit[token][2] = 0


