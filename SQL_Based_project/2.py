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

from_date = '2022-03-11 09:30:00'
to_date = '2022-03-11 15:30:00'

call_historical_data = kite.historical_data(CE_ins_tkn, from_date, to_date, 'minute')
call_his_df = pd.DataFrame(call_historical_data)

