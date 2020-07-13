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
import threading
import sys

api_k = "dysoztj41hntm1ma";  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94";  # api_secret
access_token = "kFrtYYHrdA77u5jsDjTwKX4NMnK3ZHXJ"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

opening_margin = KiteConnect.margins(kite)
day_margin = opening_margin['equity']['net']

candle_thread_running = ""
renko_thread_running = ""
day_profit_percent = 0

trd_portfolio = {698627: {"Symbol": "USDINR20JULFUT", "max_quantity": 100, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0}}

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

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average, positions ]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    HA[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]


print(kite.orders())
