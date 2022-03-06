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

temp_historical_min = int((datetime.datetime.now().strftime("%M")))-1
print(datetime.datetime.today().replace(minute=temp_historical_min, second=0,microsecond=0))
print(math.ceil(626.1245*10)/10)
print(divmod(626.1245,.05))
print((kite.ltp("NFO:{}".format("NIFTY2231016200CE"))).get("NFO:{}".format("NIFTY2231016200CE")).get('last_price'))