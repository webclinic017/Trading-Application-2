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
from datasetup import *


def quantity():
    global trd_portfolio, day_margin
    try:
        for items in trd_portfolio:
            if trd_portfolio[items]['Segment'] == "Options":  # calculating quantity for options
                maxquantity = min(day_margin / trd_portfolio[items]['LTP'], trd_portfolio[items]['max_quantity'])
                multiplier = 0
                while (multiplier * 75) < trd_portfolio[items]['max_quantity']:
                    multiplier = multiplier + 1
                else:
                    trd_portfolio[items]['Tradable_quantity'] = (multiplier - 1) * 75
            elif trd_portfolio[items]['Segment'] == "Equity":  # calculating quantity for equities
                if trd_portfolio[items]['LTP'] != 0:
                    if ((day_margin * trd_portfolio[items]['margin_multiplier']) / (trd_portfolio[items]['LTP'] * trd_portfolio[items]['Quantity_multiplier'])) - trd_portfolio[items]['buffer_quantity'] < 1:
                        trd_portfolio[items]['Tradable_quantity'] = 0
                    else:
                        trd_portfolio[items]['Tradable_quantity'] = int(round(min(((day_margin * trd_portfolio[items]['margin_multiplier']) / (trd_portfolio[items]['LTP'] * trd_portfolio[items][
                            'Quantity_multiplier'])) - trd_portfolio[items]['buffer_quantity'],
                                                                                  trd_portfolio[items]['max_quantity']), 0))
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