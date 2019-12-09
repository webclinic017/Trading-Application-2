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
access_token = "QYsCgjXkSYGnlUMMJJkkAFLGaqlYta7r"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

trd_portfolio = {779521: {"Symbol": "SBIN", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0}}

def positions(token):
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
            return current_pos

print(positions(779521))


