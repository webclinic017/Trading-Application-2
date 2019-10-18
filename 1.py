
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
import datetime,time,os,random


def ATR(df, n):  # df is the DataFrame, n is the period 7,14 ,etc
    df['H-L'] = abs(df['High'].astype(float)-df['Low'].astype(float))
    df['H-PC'] = abs(df['High'].astype(float)-df['Close'].astype(float).shift(1))
    df['L-PC'] = abs(df['Low'].astype(float)-df['Close'].astype(float).shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = np.nan
    df.ix[n-1, 'ATR'] = df['TR'][:n-1].mean()  # .ix is deprecated from pandas version- 0.19
    for i in range(n, len(df)):
        df['ATR'][i] = (df['ATR'][i-1]*(n-1) + df['TR'][i])/n
    return


def history(stock):
    global RENKO_Final
    with urlopen(
            "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=NSE:" + stock + "&interval=1min&outputsize=full&apikey=08AXPZ0UQEVKUSD8") as response:
        source = response.read()
        data = json.loads(source)
        minute_data = data["Time Series (1min)"]
        df = pd.DataFrame.from_dict(minute_data, orient='index')
        df.drop(['5. volume'], axis=1, inplace=True)
        df.rename(columns={'1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close'}, inplace=True)
        Position = ''

        # print(json.dumps(minute_data, indent=2))
        ATR(df, 14)
        df = df[['Open', 'High', 'Low', 'Close', 'ATR']]
        # print(df)

        renkoData_his = {'BrickSize': 0, 'Open': 0.0, 'Close': 0.0, 'Color': ''}
        renkoData_his['BrickSize'] = round(df['ATR'][-1], 2)  # This can be set manually as well!
        renkoData_his['Open'] = renkoData_his['BrickSize'] + renkoData_his[
            'Close']  # This can be done the otherway round
        renkoData_his['Color'] = 'SELL'  # Should you choose to do the other way round, please change the color to 'BUY'

        finalData_his = pd.DataFrame(index=None)
        finalData_his['ReOpen'] = 0.0
        finalData_his['ReHigh'] = 0.0
        finalData_his['ReLow'] = 0.0
        finalData_his['ReClose'] = 0.0
        finalData_his['Color'] = ''

        for index, row in df.iterrows():  # One may choose to use Pure python instead of Iterrows to loop though each n
            # every row to improve performance if datasets are large.
            if renkoData_his['Open'] > renkoData_his['Close']:
                while float(row['Close']) > (float(renkoData_his['Open']) + float(renkoData_his['BrickSize'])):
                    renkoData_his['Open'] += renkoData_his['BrickSize']
                    renkoData_his['Close'] += renkoData_his['BrickSize']
                    finalData_his.loc[index] = row
                    finalData_his['ReOpen'].loc[index] = renkoData_his['Close']
                    finalData_his['ReHigh'].loc[index] = renkoData_his['Open']
                    finalData_his['ReLow'].loc[index] = renkoData_his['Close']
                    finalData_his['ReClose'].loc[index] = renkoData_his['Open']
                    finalData_his['Color'].loc[index] = 'BUY'

                while float(row['Close']) < float((renkoData_his['Close']) - float(renkoData_his['BrickSize'])):
                    renkoData_his['Open'] -= renkoData_his['BrickSize']
                    renkoData_his['Close'] -= renkoData_his['BrickSize']
                    finalData_his.loc[index] = row
                    finalData_his['ReOpen'].loc[index] = renkoData_his['Open']
                    finalData_his['ReHigh'].loc[index] = renkoData_his['Open']
                    finalData_his['ReLow'].loc[index] = renkoData_his['Close']
                    finalData_his['ReClose'].loc[index] = renkoData_his['Close']
                    finalData_his['Color'].loc[index] = 'SELL'

            else:
                while float(row['Close']) < float((renkoData_his['Open']) - float(renkoData_his['BrickSize'])):
                    renkoData_his['Open'] -= renkoData_his['BrickSize']
                    renkoData_his['Close'] -= renkoData_his['BrickSize']
                    finalData_his.loc[index] = row
                    finalData_his['ReOpen'].loc[index] = renkoData_his['Close']
                    finalData_his['ReHigh'].loc[index] = renkoData_his['Close']
                    finalData_his['ReLow'].loc[index] = renkoData_his['Open']
                    finalData_his['ReClose'].loc[index] = renkoData_his['Open']
                    finalData_his['Color'].loc[index] = 'SELL'

                while float(row['Close']) > float((renkoData_his['Close']) + float(renkoData_his['BrickSize'])):
                    renkoData_his['Open'] += renkoData_his['BrickSize']
                    renkoData_his['Close'] += renkoData_his['BrickSize']
                    finalData_his.loc[index] = row
                    finalData_his['ReOpen'].loc[index] = renkoData_his['Open']
                    finalData_his['ReHigh'].loc[index] = renkoData_his['Close']
                    finalData_his['ReLow'].loc[index] = renkoData_his['Open']
                    finalData_his['ReClose'].loc[index] = renkoData_his['Close']
                    finalData_his['Color'].loc[index] = 'BUY'

        finalData_his['SMA'] = finalData_his.ReClose.rolling(10).mean()
        finalData_his['TMA'] = finalData_his.SMA.rolling(10).mean()
        # print(finalData_his)

        # "Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"

        finalRenko = {'Symbol': '', 'Open': 0, 'Close': 0, 'Signal': '', 'Position': '', 'SMA': 0, 'TMA': 0}
        finalRenko['Symbol'] = stock
        finalRenko['Position'] = Position
        finalRenko['Open'] = finalData_his['ReOpen']
        finalRenko['Close'] = finalData_his['ReClose']
        finalRenko['Signal'] = finalData_his['Color']
        finalRenko['SMA'] = finalData_his['SMA']
        finalRenko['TMA'] = finalData_his['TMA']
        finalRenkodf = pd.DataFrame(finalRenko, index=None)
        finalRenkodf.set_index('Symbol', inplace=True)
        # print(finalRenkodf)
        RENKO_Final = RENKO_Final.append(finalRenkodf)


def calculate_ohlc_one_minute(company_data):
    global ohlc_final_1min, ohlc_temp, RENKO_temp, RENKO_Final
    try:
        # below if condition is to check the data being received, and the data present are of the same minute or not
        if (str(((company_data["timestamp"]).replace(second=0))) != ohlc[company_data['instrument_token']][1]) and (ohlc[company_data['instrument_token']][1]!= "Time"):
            ohlc_temp = pd.DataFrame([ohlc[x]], columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
        # Calculating True Range
            if len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
                ohlc_temp.iloc[-1, 6] = round(max((abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 3]) - (ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 4]) - (ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4])))), 2)
            else:
                ohlc_temp.iloc[-1, 6] = round(abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])), 2)
        # True Range Calculation complete
        # Calculating ATR
            if len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ohlc_temp.iloc[-1, 7] = 0

            elif len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) == 13:
                a = [ohlc_temp.iloc[-1, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 6],
                     ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 6],
                ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 6], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 6]]
                ohlc_temp.iloc[-1, 7] = round(sum(a)/13, 2)

            elif len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]*13) + ohlc_temp.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6])/14, 2)
        # ATR Calculation complete
        # Calculating SMA
            if len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 10:
                ohlc_temp.iloc[-1, 8] = 0
            elif len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 10:
                b = [ohlc_temp.iloc[-1, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                     ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                ohlc_temp.iloc[-1, 8] = round(sum(b) / 10, 2)
        # SMA Calculation complete

        # Calculating Triangular moving average
            if len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                ohlc_temp.iloc[-1, 9] = 0
            elif len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                c = [ohlc_temp.iloc[-1, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 8],
                     ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 8], ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 8]]
                ohlc_temp.iloc[-1, 9] = round((sum(c) / 10), 2)
        # TMA calculation complete

        # adding the row into the final ohlc table
            ohlc_temp.set_index('Symbol', inplace=True)
            ohlc_final_1min = ohlc_final_1min.append(ohlc_temp)
            #print(ohlc_final_1min.tail())

            # making ohlc for new candle
            ohlc[company_data['instrument_token']][2] = company_data['last_price']  # open
            ohlc[company_data['instrument_token']][3] = company_data['last_price']  # high
            ohlc[company_data['instrument_token']][4] = company_data['last_price']  # low
            ohlc[company_data['instrument_token']][5] = company_data['last_price']  # close
            ohlc[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]

        if ohlc[company_data['instrument_token']][3] < company_data['last_price']:  # calculating high
            ohlc[company_data['instrument_token']][3] = company_data['last_price']

        if ohlc[company_data['instrument_token']][4] > company_data['last_price'] or \
                ohlc[company_data['instrument_token']][4] == 0:  # calculating low
            ohlc[company_data['instrument_token']][4] = company_data['last_price']

        ohlc[company_data['instrument_token']][5] = company_data['last_price']  # closing price
        ohlc[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))

        if len(ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:  # checking if there is atleast 1 candle in OHLC Dataframe
            if ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != 0:  #checking that we do not have the ATR value as 0
                if RENKO[company_data['instrument_token']][0] == "Symbol":
                    RENKO[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
                ########################################################
                if RENKO[company_data['instrument_token']][1] == 0:  # assigning the first, last price of the tick to open
                    RENKO[company_data['instrument_token']][1] = company_data['last_price']
                ########################################################
                if RENKO[company_data['instrument_token']][3] == "Signal":
                    if (company_data['last_price'] >= ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + RENKO[company_data['instrument_token']][1]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[x]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])

                        # Calculating SMA
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_temp.set_index('Symbol', inplace=True)
                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        print(RENKO_temp)
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif (company_data['last_price']<= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[x]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_temp.set_index('Symbol', inplace=True)
                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        print(RENKO_temp)
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]

                if RENKO[company_data['instrument_token']][3] == "BUY":
                    if (company_data['last_price'] >= ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + RENKO[company_data['instrument_token']][1]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[x]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_temp.set_index('Symbol', inplace=True)
                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        print(RENKO_temp)
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= RENKO[company_data['instrument_token']][1] - (RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2] - RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]) - ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] - ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[x]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_temp.set_index('Symbol', inplace=True)
                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        print(RENKO_temp)
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                if RENKO[company_data['instrument_token']][3] == "SELL":
                    if (company_data['last_price']<= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[x]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_temp.set_index('Symbol', inplace=True)
                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        print(RENKO_temp)
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] >= RENKO[company_data['instrument_token']][1] + (RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] - RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]) + ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] + ohlc_final_1min.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[x]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_temp.set_index('Symbol', inplace=True)
                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        print(RENKO_temp)
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]

    except Exception as e:
        traceback.print_exc()


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    global ohlc_final_1min, RENKO_Final, final_position, order_quantity
    '''try:
        for company_data in ticks:
            if (company_data['last_trade_time'].time()) > datetime.time(9,15,00) and (company_data['last_trade_time'].time()) < datetime.time(15,31,00):
                calculate_ohlc_one_minute(company_data)
                RENKO_TRIMA(company_data)
    except Exception as e:
        traceback.print_exc()'''

def on_connect(ws, response):
    for x in trd_portfolio:
        for j in trd_portfolio[x]:
            if j == "token":
                ws.subscribe(trd_portfolio[x]['token'])
                ws.set_mode(ws.MODE_FULL, trd_portfolio[x]['token'])


api_k = "dysoztj41hntm1ma";  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94";  # api_secret
access_token = "IshHd3RQqLERm0TR4Vg3y5qjKHvZaxjP"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

trd_portfolio = {779521: {"Symbol": "SBIN", "max_quantity": 10000, 'Direction': "", 'Orderid': "", 'Target_order': '', 'Target_order_id': ''},
                 5633: {"Symbol": "ACC", "max_quantity": 10000, 'Direction': "", 'Orderid': "", 'Target_order': '', 'Target_order_id': ''}
                 }

ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol","Time", "Open", "High", "Low", "Close", "TR","ATR","SMA","TMA"])
ohlc_final_1min = pd.DataFrame()
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame()
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit"])
profit_Final = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit"])

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit"]

#for loop to order history for all the stocks
for x, y in trd_portfolio.items():
    for z in y:
        if z == "Symbol":
            history(y[z])

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect()