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
access_token = "YeDIn3IQ3b52tw4bGS1jrZipfJq7bhCW"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

trd_portfolio = {5633: {"Symbol": "ACC", "max_quantity": 10000, "Direction": "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0},
                 25601: {"Symbol": "AMARAJABAT", "max_quantity": 10000, "Direction": "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0}
                 }


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    try:
        print(ticks)
        for company_data in ticks:
            print(company_data['instrument_token'])
    except Exception as e:
        traceback.print_exc()

def on_connect(ws, response):
    ws.subscribe([x for x in trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in trd_portfolio])

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect()