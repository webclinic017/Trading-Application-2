from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions, KiteConnect
import math
import time
import threading
import traceback
import datasetup as ds
from quantity import quantity
from circuit_limits import circuit_limits
from requests.exceptions import ReadTimeout
import pandas as pd
import socket
# from trigger import *


def calculate_ohlc_one_minute(company_data):
    try:
        # below if condition is to check the data being received, and the data present are of the same minute or not
        ds.candle_thread_running = "YES"
        if (str(((company_data["timestamp"]).replace(second=0))) != ds.ohlc[company_data['instrument_token']][1]) and (
                ds.ohlc[company_data['instrument_token']][1] != "Time"):
            ds.ohlc_temp = pd.DataFrame([ds.ohlc[company_data['instrument_token']]],
                                     columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA",
                                              "TMA"])
            # print(ohlc_temp.head(), ohlc_final_1min.head())
            ds.HA_temp = pd.DataFrame([ds.HA[company_data['instrument_token']]],
                                   columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA",
                                            "TMA"])

            # Calculating SMA for Heiken Ashi
            if len(ds.HA_Final.loc[
                       ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ds.HA_temp.iloc[-1, 8] = 0
            elif len(ds.HA_Final.loc[
                         ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                z = [ds.HA_temp.iloc[-1, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -10, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -11, 5],
                     ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -12, 5]]
                ds.HA_temp.iloc[-1, 8] = round(sum(z) / 13, 4)
            # SMA Calculation complete for ohlc

            # Calculating True Range
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
                ds.ohlc_temp.iloc[-1, 6] = round(max((abs((ds.ohlc_temp.iloc[-1, 3]) - (ds.ohlc_temp.iloc[-1, 4])),
                                                   abs((ds.ohlc_temp.iloc[-1, 3]) - (ds.ohlc_final_1min.loc[
                                                       ds.ohlc_final_1min.Symbol ==
                                                       ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                                       -1, 4])),
                                                   abs((ds.ohlc_temp.iloc[-1, 4]) - (ds.ohlc_final_1min.loc[
                                                       ds.ohlc_final_1min.Symbol ==
                                                       ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                                       -1, 4])))), 2)
            else:
                ds.ohlc_temp.iloc[-1, 6] = round(abs((ds.ohlc_temp.iloc[-1, 3]) - (ds.ohlc_temp.iloc[-1, 4])), 2)
            # True Range Calculation complete for ohlc
            # Calculating ATR for ohlc
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ds.ohlc_temp.iloc[-1, 7] = 0

            elif len(ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                ds.ohlc_temp.iloc[-1, 7] = round(((ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                    ds.trd_portfolio[company_data['instrument_token']][
                                                                        'Symbol']].iloc[-1, 7] * 13) + ds.ohlc_temp.iloc[
                                                   -1, 6]) / 14, 2)
                '''a = [ohlc_temp.iloc[-1, 6], ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 6]]
                ohlc_temp.iloc[-1, 7] = round(sum(a)/13, 2)'''

            '''elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) > 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]*13) + ohlc_temp.iloc[-1, 6])/14, 2)'''
            # ATR Calculation complete for ohlc
            # Calculating SMA for ohlc
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 10:
                ds.ohlc_temp.iloc[-1, 8] = 0
            elif len(ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 10:
                b = [ds.ohlc_temp.iloc[-1, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 5],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 5]]
                ds.ohlc_temp.iloc[-1, 8] = round(sum(b) / 10, 2)
            # SMA Calculation complete for ohlc

            # Calculating Triangular moving average for ohlc
            if len(ds.ohlc_final_1min.loc[
                       ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                ds.ohlc_temp.iloc[-1, 9] = 0
            elif len(ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                c = [ds.ohlc_temp.iloc[-1, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -1, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -2, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -3, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -4, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -5, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -6, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -7, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -8, 8],
                     ds.ohlc_final_1min.loc[
                         ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                         -9, 8]]
                ds.ohlc_temp.iloc[-1, 9] = round((sum(c) / 10), 2)
            # TMA calculation complete for ohlc

            # adding the row into the final ohlc table
            ds.ohlc_final_1min = ds.ohlc_final_1min.append(ds.ohlc_temp)
            ds.HA_Final = ds.HA_Final.append(ds.HA_temp)
            print(ds.HA_temp.to_string())
            # print(ohlc_temp.to_string())

        # making ohlc for new candle
        ds.ohlc[company_data['instrument_token']][2] = company_data['last_price']  # open
        ds.ohlc[company_data['instrument_token']][3] = company_data['last_price']  # high
        ds.ohlc[company_data['instrument_token']][4] = company_data['last_price']  # low
        ds.ohlc[company_data['instrument_token']][5] = company_data['last_price']  # close
        ds.ohlc[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']]['Symbol']

        if ds.ohlc[company_data['instrument_token']][3] < company_data['last_price']:  # calculating high
            ds.ohlc[company_data['instrument_token']][3] = company_data['last_price']

        if ds.ohlc[company_data['instrument_token']][4] > company_data['last_price'] or \
                ds.ohlc[company_data['instrument_token']][4] == 0:  # calculating low
            ds.ohlc[company_data['instrument_token']][4] = company_data['last_price']

        ds.ohlc[company_data['instrument_token']][5] = company_data['last_price']  # closing price
        ds.ohlc[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))

        if (len(ds.HA_Final.loc[
                    ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) < 1):
            if ds.HA[company_data['instrument_token']][0] == "Symbol":
                ds.HA[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']]['Symbol']
            ds.HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            ds.HA[company_data['instrument_token']][2] = round(
                (ds.ohlc[company_data['instrument_token']][2] + ds.ohlc[company_data['instrument_token']][5]) / 2, 4)
            ds.HA[company_data['instrument_token']][3] = round(ds.ohlc[company_data['instrument_token']][3], 4)
            ds.HA[company_data['instrument_token']][4] = round(ds.ohlc[company_data['instrument_token']][4], 4)
            ds.HA[company_data['instrument_token']][5] = round((ds.ohlc[company_data['instrument_token']][2] +
                                                             ds.ohlc[company_data['instrument_token']][3] +
                                                             ds.ohlc[company_data['instrument_token']][4] +
                                                             ds.ohlc[company_data['instrument_token']][5]) / 4, 4)
        if (len(ds.HA_Final.loc[
                    ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1):
            if ds.HA[company_data['instrument_token']][0] == "Symbol":
                ds.HA[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']]['Symbol']
            ds.HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            ds.HA[company_data['instrument_token']][5] = round((ds.ohlc[company_data['instrument_token']][2] +
                                                             ds.ohlc[company_data['instrument_token']][3] +
                                                             ds.ohlc[company_data['instrument_token']][4] +
                                                             ds.ohlc[company_data['instrument_token']][5]) / 4, 4)
            ds.HA[company_data['instrument_token']][2] = round((ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[
                company_data['instrument_token']]['Symbol']].iloc[-1, 2] + ds.HA_Final.loc[ds.HA_Final.Symbol ==
                                                                                        ds.trd_portfolio[company_data[
                                                                                            'instrument_token']][
                                                                                            'Symbol']].iloc[-1, 5]) / 2,
                                                            4)
            ds.HA[company_data['instrument_token']][3] = round(
                max(ds.ohlc[company_data['instrument_token']][3], ds.HA[company_data['instrument_token']][2],
                    ds.HA[company_data['instrument_token']][5]), 4)
            ds.HA[company_data['instrument_token']][4] = round(
                min(ds.ohlc[company_data['instrument_token']][4], ds.HA[company_data['instrument_token']][2],
                    ds.HA[company_data['instrument_token']][5]), 4)

        # starting to calculate the ds.RENKO table
        if len(ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']][
            'Symbol']]) > 0:  # or (len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):  # checking if there is atleast 1 candle in OHLC Dataframe or ds.RENKO Dataframe
            if ds.ohlc_final_1min.loc[
                ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                -1, 7] != 0:  # or (ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != [0, 'NaN']):  #checking that we do not have the ATR value as 0
                if ds.RENKO[company_data['instrument_token']][0] == "Symbol":
                    ds.RENKO[company_data['instrument_token']][0] = ds.trd_portfolio[company_data['instrument_token']][
                        'Symbol']
                ########################################################
                if ds.RENKO[company_data['instrument_token']][
                    1] == 0:  # assigning the first, last price of the tick to open
                    ds.RENKO[company_data['instrument_token']][1] = company_data['last_price']
                ########################################################
                if ds.RENKO[company_data['instrument_token']][3] == "Signal":
                    if company_data['last_price'] >= ds.ohlc_final_1min.loc[
                        ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7] + ds.RENKO[company_data['instrument_token']][1]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] + \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "BUY"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])

                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= ds.RENKO[company_data['instrument_token']][1] - ds.ohlc_final_1min.loc[
                        ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] - \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "SELL"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]

                if ds.RENKO[company_data['instrument_token']][3] == "BUY":
                    if company_data['last_price'] >= ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + ds.RENKO[company_data['instrument_token']][1]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] + \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "BUY"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= ds.RENKO[company_data['instrument_token']][1] - (ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 2] -
                                                                                                     ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 1]) - \
                            ds.ohlc_final_1min.loc[
                                ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                    'Symbol']].iloc[-1, 7]:
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO_Final.loc[ds.RENKO_Final.Symbol ==
                                                                                     ds.trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] - \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "SELL"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                if ds.RENKO[company_data['instrument_token']][3] == "SELL":
                    if company_data['last_price'] <= ds.RENKO[company_data['instrument_token']][1] - ds.ohlc_final_1min.loc[
                        ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                        -1, 7]:
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO[company_data['instrument_token']][1] - \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "SELL"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] >= ds.RENKO[company_data['instrument_token']][1] + (ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 1] -
                                                                                                     ds.RENKO_Final.loc[
                                                                                                         ds.RENKO_Final.Symbol ==
                                                                                                         ds.trd_portfolio[
                                                                                                             company_data[
                                                                                                                 'instrument_token']][
                                                                                                             'Symbol']].iloc[
                                                                                                         -1, 2]) + \
                            ds.ohlc_final_1min.loc[
                                ds.ohlc_final_1min.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                    'Symbol']].iloc[-1, 7]:
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        ds.RENKO[company_data['instrument_token']][2] = ds.RENKO_Final.loc[ds.RENKO_Final.Symbol ==
                                                                                     ds.trd_portfolio[company_data[
                                                                                         'instrument_token']][
                                                                                         'Symbol']].iloc[-1, 1] + \
                                                                     ds.ohlc_final_1min.loc[ds.ohlc_final_1min.Symbol ==
                                                                                         ds.trd_portfolio[company_data[
                                                                                             'instrument_token']][
                                                                                             'Symbol']].iloc[-1, 7]
                        ds.RENKO[company_data['instrument_token']][3] = "BUY"
                        ds.RENKO_temp = pd.DataFrame([ds.RENKO[company_data['instrument_token']]],
                                                  columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA",
                                                           "TMA"])
                        # Calculating SMA
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) <= 9:
                            ds.RENKO_temp.iloc[-1, 5] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) > 9:
                            d = [ds.RENKO_temp.iloc[-1, 2], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 2],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 2], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 2]]
                            ds.RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) < 19:
                            ds.RENKO_temp.iloc[-1, 6] = 0
                        elif len(ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                            'Symbol']]) >= 19:
                            e = [ds.RENKO_temp.iloc[-1, 5], ds.RENKO_Final.loc[
                                ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[
                                -1, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-2, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-3, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-4, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-5, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-6, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-7, 5],
                                 ds.RENKO_Final.loc[ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                     'Symbol']].iloc[-8, 5], ds.RENKO_Final.loc[
                                     ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                         'Symbol']].iloc[-9, 5]]
                            ds.RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        ds.RENKO_Final = ds.RENKO_Final.append(ds.RENKO_temp, sort=False)
                        # print(ds.RENKO_temp.to_string())
                        ds.RENKO[company_data['instrument_token']][1] = ds.RENKO_Final.loc[
                            ds.RENKO_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
        ds.candle_thread_running = "NO"
    except Exception as e:
        traceback.print_exc(e)


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


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc(e)


def order_status(token, orderid, trade_type):
    try:
        order_details = ds.kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                if trade_type == 'SELL':
                    ds.trd_portfolio[token]['Direction'] = "Down"
                    ds.trd_portfolio[token]['Target_order'] = "NO"
                    print(ds.trd_portfolio[token]['Direction'])
                    break
                elif trade_type == 'BUY':
                    ds.trd_portfolio[token]['Direction'] = "Up"
                    ds.trd_portfolio[token]['Target_order'] = "NO"
                    print(ds.trd_portfolio[token]['Direction'])
                    break
            elif item['status'] == "REJECTED":
                print("order got rejected", ds.trd_portfolio[token]['Direction'], ds.trd_portfolio[token]['Target_order'])
                break
        else:
            time.sleep(1)
            order_status(token, orderid, type)
    except Exception as e:
        order_status(token, orderid, type)
        traceback.print_exc(e)


def target_order_status(orderid):
    try:
        details = ds.kite.order_history(orderid)
        for item in details:
            if item['status'] == "OPEN":
                return "OPEN"
            elif item['status'] == "REJECTED":
                return "REJECTED"
            elif item['status'] == "COMPLETE":
                return "COMPLETED"
        else:
            time.sleep(1)
            target_order_status(orderid)
    except Exception as e:
        target_order_status(orderid)
        traceback.print_exc(e)


def trigger(token):
    try:
        ds.trigger_thread_running = "YES"
        if len(ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']]) >= 1:
            if ((ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 2]) == (
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 3])) and (
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 2] >
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 5]) and (
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 8] > (
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 5])):
                print("quantity validation before ordering", str(ds.profit[token][4]))
                if ds.profit[token][4] > 0:
                    ds.kite.modify_order(variety="regular", order_id=ds.trd_portfolio[token]['Target_order_id'],
                                      order_type=ds.kite.ORDER_TYPE_MARKET)
                    time.sleep(3)
                    print("exiting current positions")
                elif ds.profit[token][4] == 0:
                    if ds.trd_portfolio[token]['Direction'] != "Down":
                        if ds.trd_portfolio[token]['Tradable_quantity'] > 0:
                            print("Fresh order")
                            ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular",
                                                                               exchange=ds.trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=ds.trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=ds.kite.TRANSACTION_TYPE_SELL,
                                                                               quantity=ds.trd_portfolio[token][
                                                                                   'Tradable_quantity'],
                                                                               order_type=ds.kite.ORDER_TYPE_MARKET,
                                                                               product=ds.kite.PRODUCT_MIS)
                            print(ds.trd_portfolio[token]['Orderid'])
                            time.sleep(3)
                            order_status(token, ds.trd_portfolio[token]['Orderid'], 'SELL')
            # BUY Condition
            if (ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 2] ==
                ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 4]) and (
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 2] <
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 5]) \
                    and (ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 8] < (
                    ds.HA_Final.loc[ds.HA_Final.Symbol == ds.trd_portfolio[token]['Symbol']].iloc[-1, 5])):
                print("quantity validation before ordering", str(ds.profit[token][4]))
                if ds.profit[token][4] < 0:
                    ds.kite.modify_order(variety="regular", order_id=ds.trd_portfolio[token]['Target_order_id'],
                                      order_type=ds.kite.ORDER_TYPE_MARKET)
                    time.sleep(2)
                    print("exiting current positions")
                elif ds.profit[token][4] == 0:
                    if ds.trd_portfolio[token]['Direction'] != "Up":
                        if ds.trd_portfolio[token]['Tradable_quantity'] > 0:
                            print("Fresh order")
                            ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular",
                                                                               exchange=ds.trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=ds.trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=ds.kite.TRANSACTION_TYPE_BUY,
                                                                               quantity=ds.trd_portfolio[token][
                                                                                   'Tradable_quantity'],
                                                                               order_type=ds.kite.ORDER_TYPE_MARKET,
                                                                               product=ds.kite.PRODUCT_MIS)
                            print(ds.trd_portfolio[token]['Orderid'])
                            time.sleep(2)
                            order_status(token, ds.trd_portfolio[token]['Orderid'], 'BUY')
            # Below ones are target orders
            print("quantity validation before target set", str(ds.profit[token][4]))
            print(ds.profit[token])
            if ds.profit[token][4] > 0:
                if ds.trd_portfolio[token]['Target_order'] != "YES":
                    ds.trd_portfolio[token]['Target_order_id'] = ds.kite.place_order(variety="regular",
                                                                               exchange=ds.trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=ds.trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=ds.kite.TRANSACTION_TYPE_SELL,
                                                                               quantity=abs(
                                                                                   ds.trd_portfolio[token]['Positions']),
                                                                               order_type=ds.kite.ORDER_TYPE_LIMIT,
                                                                               price=round(
                                                                                   ds.trd_portfolio[token]['Target_amount'], 4), product=ds.kite.PRODUCT_MIS)
                    if target_order_status(ds.trd_portfolio[token]['Target_order_id']) == "OPEN":
                        ds.trd_portfolio[token]['Target_order'] = "YES"
            if ds.profit[token][4] < 0:
                if ds.trd_portfolio[token]['Target_order'] != "YES":
                    ds.trd_portfolio[token]['Target_order_id'] = ds.kite.place_order(variety="regular",
                                                                               exchange=ds.trd_portfolio[token][
                                                                                   'exchange'],
                                                                               tradingsymbol=ds.trd_portfolio[token][
                                                                                   'Symbol'],
                                                                               transaction_type=ds.kite.TRANSACTION_TYPE_BUY,
                                                                               quantity=abs(
                                                                                   ds.trd_portfolio[token]['Positions']),
                                                                               order_type=ds.kite.ORDER_TYPE_LIMIT,
                                                                               price=round_down(
                                                                                   ds.trd_portfolio[token]['Target_amount'], 4),
                                                                               product=ds.kite.PRODUCT_MIS)
                    if target_order_status(ds.trd_portfolio[token]['Target_order_id']) == "OPEN":
                        ds.trd_portfolio[token]['Target_order'] = "YES"
        ds.trigger_thread_running = "NO"
    except TypeError:
        traceback.print_exc()
        ds.trigger_thread_running = "NO"
        pass
    except exceptions.InputException:
        traceback.print_exc()
        ds.trigger_thread_running = "NO"
        pass
    except ReadTimeout:
        traceback.print_exc()
        ds.trigger_thread_running = "NO"
        pass
    except exceptions.NetworkException:
        traceback.print_exc()
        ds.trigger_thread_running = "NO"
        pass
    except AttributeError:
        traceback.print_exc()
        ds.trigger_thread_running = "NO"
        pass
    except Exception as e:
        traceback.print_exc(e)
        ds.trigger_thread_running = "NO"
        pass
    except WantReadError as e:
        ds.trigger_thread_running = "NO"
        pass


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    try:
        for company_data in ticks:
            if ds.trd_portfolio[company_data['instrument_token']]['LTP'] == 0:
                ds.trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
                quantity()
            else:
                ds.trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
            if ds.candle_thread_running != "YES":
                if ds.trd_portfolio[company_data['instrument_token']]['start_time'] < (
                        company_data['last_trade_time'].time()) < ds.trd_portfolio[company_data['instrument_token']]['end_time']:
                    candle = threading.Thread(target=calculate_ohlc_one_minute, args=(company_data,))
                    candle.start()
                    if ds.trd_portfolio[company_data['instrument_token']]['Trade'] == "YES":
                        if ((ds.carry_forward / ds.day_margin) * 100) < 2:
                            if ds.trigger_thread_running != 'YES':
                                if len(ds.HA_Final.loc[
                                           ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                               'Symbol']]) >= 1:
                                    if ds.HA_Final.loc[
                                        ds.HA_Final.Symbol == ds.trd_portfolio[company_data['instrument_token']][
                                            'Symbol']].iloc[-1, 8] != 0:
                                        order_trigger_loop_initiator = threading.Thread(target=trigger, args=[
                                                company_data['instrument_token']])
                                        order_trigger_loop_initiator.start()
    except Exception as e:
        traceback.print_exc(e)


def on_connect(ws, response):
    ws.subscribe([x for x in ds.trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in ds.trd_portfolio])


if __name__ == '__main__':
    ds.kws.on_ticks = on_ticks
    ds.kws.on_connect = on_connect
    ds.kws.connect()
