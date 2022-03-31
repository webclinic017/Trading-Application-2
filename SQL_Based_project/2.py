import datetime
import socket
import threading
import traceback
import time
# from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions
from requests.exceptions import ReadTimeout
import math
import mysql.connector
import usdinr as ds
import pandas as pd
import requests
import json
from kiteconnect import KiteTicker, KiteConnect

acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()

noted_time = ''
CE_symbol = 'NIFTY2231716600CE'
CE_ins_tkn = 12961282
PE_ins_tkn = 12961538
PE_symbol = 'NIFTY2231716600PE'

from_date = '2022-03-23 09:15:00'
to_date = '2022-03-23 15:30:00'

date = datetime.date(2022, 3, 23)
time = datetime.time(9, 15, 00)
from_to_date = '2022-03-17 11:15:00'
start_time = datetime.datetime.combine(date, time)
processed_time = datetime.datetime.combine(date, time)

while processed_time < datetime.datetime.now():
    if processed_time + datetime.timedelta(minutes=5) > datetime.datetime.now():
        break
    else:
        processed_time = processed_time + datetime.timedelta(minutes=5)
        # print(processed_time)
        pass

historical_data = kite.historical_data(256265, from_date, to_date, '5minute')
his_df = pd.DataFrame(historical_data)
print(his_df.to_string())