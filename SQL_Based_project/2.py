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

date = datetime.datetime.today().date()
time = datetime.time(9, 15, 00)
start_time = datetime.datetime.combine(date, time)
processed_time = datetime.datetime.combine(date, time)
print(processed_time - datetime.timedelta(minutes=5))

while processed_time < datetime.datetime.now():
    if processed_time + datetime.timedelta(minutes=5) > datetime.datetime.now():
        break
    else:
        processed_time = processed_time + datetime.timedelta(minutes=5)
        print(processed_time)
