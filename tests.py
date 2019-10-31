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
access_token = "lG6E8NNt9G9UYik755sZSj3inegj42Hd"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

print(kite.order_history(191031001576644))

def order_status():
    order_details = kite.order_history(191031001576644)
    for item in order_details:
        if item['status'] == "COMPLETE":
            print('order successfull')
            order_status()

order_status()