import datetime
import json
import math
import socket
import threading
import time
import traceback
from urllib.request import *
import requests
import numpy as np
import pandas as pd
from OpenSSL.SSL import WantReadError
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
from kiteconnect import exceptions
from kiteconnect.exceptions import DataException
from requests.exceptions import ReadTimeout
import datasetup as ds


def quantity():
    try:
        temp_open_margin = KiteConnect.margins(ds.kite)
        temp_day_margin = temp_open_margin['equity']['net']
        for items in ds.trd_portfolio:
            if ds.trd_portfolio[items]['Segment'] == "Options":  # calculating quantity for options
                maxquantity = min(temp_day_margin / ds.trd_portfolio[items]['LTP'], ds.trd_portfolio[items]['max_quantity'])
                multiplier = 0
                while (multiplier * 75) < maxquantity: # ds.trd_portfolio[items]['max_quantity']:
                    multiplier = multiplier + 1
                else:
                    ds.trd_portfolio[items]['Tradable_quantity'] = (multiplier - 1) * 75
            elif ds.trd_portfolio[items]['Segment'] != "Options":  # calculating quantity for equities
                if ds.trd_portfolio[items]['LTP'] != 0:
                    if ((temp_day_margin * ds.trd_portfolio[items]['margin_multiplier']) / (ds.trd_portfolio[items]['LTP'] * ds.trd_portfolio[items]['Quantity_multiplier'])) - ds.trd_portfolio[items]['buffer_quantity'] < 1:
                        ds.trd_portfolio[items]['Tradable_quantity'] = 0
                        print("a")
                    else:
                        ds.trd_portfolio[items]['Tradable_quantity'] = int(round(min(((ds.day_margin * ds.trd_portfolio[items]['margin_multiplier']) / (ds.trd_portfolio[items]['LTP'] * ds.trd_portfolio[items][
                            'Quantity_multiplier'])) - ds.trd_portfolio[items]['buffer_quantity'],
                                                                                  ds.trd_portfolio[items]['max_quantity']), 0))
                        print("b", ds.trd_portfolio[items]['Tradable_quantity'])
                        print(str(ds.day_margin) + "*" + str(ds.trd_portfolio[items]['margin_multiplier']) + "/" + str(ds.trd_portfolio[items]['LTP']) + "*" + str(ds.trd_portfolio[items][
                            'Quantity_multiplier']) + "-" + str(ds.trd_portfolio[items]['buffer_quantity']), str(ds.trd_portfolio[items]['max_quantity']))
    except ReadTimeout:
        traceback.print_exc()
        print("positions read timeout exception")
        trigger_thread_running = "NO"
        pass
    except socket.timeout:
        traceback.print_exc()
        print("positions socket timeout exception")
        trigger_thread_running = "NO"
        pass
    except TypeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except TypeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.InputException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except ReadTimeout:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.NetworkException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except Exception as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass
    except WantReadError as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass