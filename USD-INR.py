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
import threading
import sys
#sys.setrecursionlimit(30000000)

api_k = "dysoztj41hntm1ma";  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94";  # api_secret
access_token = "kFrtYYHrdA77u5jsDjTwKX4NMnK3ZHXJ"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

opening_margin = KiteConnect.margins(kite)
day_margin = opening_margin['equity']['net']

candle_thread_running = ""
renko_thread_running = ""
day_profit_percent = 0

trd_portfolio = {698627: {"Symbol": "USDINR20JULFUT", "max_quantity": 100, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0},
                 }


ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
HA = {}  # python dictionary to store the ohlc data in it
HA_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
HA_Final = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])

def positions(token):
    try:
        pos = kite.positions()
        #print(pos)
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
                return int(current_pos)
    except Exception as e:
        positions(token)
        traceback.print_exc()

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average, positions ]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    HA[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
    trd_portfolio[x]['Positions'] = positions(x)

def attained_profit():
    try:
        global day_margin, profit_Final, profit_temp, day_profit_percent
        current_profit = 0
        orders = kite.orders()
        for x in orders:
            price = x['average_price']
            symbol = x['tradingsymbol']
            type = x['transaction_type']
            token = x['instrument_token']
            status = x['status']
            volume = x['quantity'] * 1000
            if type == 'BUY' and status == 'COMPLETE':
                profit[token][1] = price
            elif type == 'SELL' and status == 'COMPLETE':
                profit[token][2] = price
            profit[token][0] = symbol
            profit[token][4] = volume
            if (profit[token][1] != 0) & (profit[token][2] != 0):
                buy_brookerage = min((profit[token][1] * volume * 0.0003), 20)
                sell_brookerage = min((profit[token][2] * volume * 0.0003), 20)
                #stt_ctt = profit[token][2] * volume * 0.00025
                buy_tran = profit[token][1] * volume * 0.000009
                sell_tran = profit[token][2] * volume * 0.000009
                gst = (buy_brookerage + sell_brookerage + buy_tran + sell_tran) * 0.18
                sebi_total = round((profit[token][1] + profit[token][2]) * volume * 0.000001, 0)
                stamp_charges = profit[token][1] * volume * 0.000001
                total_charges = sebi_total + gst + sell_tran + buy_tran + buy_brookerage + sell_brookerage + stamp_charges
                profit[token][3] = ((profit[token][2] - profit[token][1]) * volume) - total_charges
                current_profit = current_profit + profit[token][3]
                profit[token][1] = 0
                profit[token][2] = 0
        day_profit_percent = (current_profit / day_margin) * 100
    except Exception as e:
        attained_profit()
        traceback.print_exc()

def quantity():
    global trd_portfolio
    try:
        for x in trd_portfolio:
            if trd_portfolio[x]['LTP'] != 0:
                mar = KiteConnect.margins(kite)
                equity_mar = mar['equity']['net']
                if (equity_mar / 2090) < 1:
                    trd_portfolio[x]['Tradable_quantity'] = 0
                else:
                    trd_portfolio[x]['Tradable_quantity'] = int(round(min(((equity_mar / 2090)), trd_portfolio[x]['max_quantity']), 0))
    except Exception as e:
        quantity()
        traceback.print_exc()


def target(Orderid, direction):
    global profit_Final, profit_temp
    try:
        day_profit = 0
        carry_forward = 0
        trade_profit = 0
        orders = kite.orders()
        for x in orders:
            price = x['average_price']
            symbol = x['tradingsymbol']
            type = x['transaction_type']
            token = x['instrument_token']
            volume = x['quantity'] * 1000
            status = x['status']
            if type == 'BUY' and status == 'COMPLETE':
                profit[token][1] = price
            elif type == 'SELL' and status == 'COMPLETE':
                profit[token][2] = price
            profit[token][0] = symbol
            profit[token][4] = volume
            if (profit[token][1] != 0) & (profit[token][2] != 0):
                buy_brookerage = min((profit[token][1] * volume * 0.0003), 20)
                sell_brookerage = min((profit[token][2] * volume * 0.0003), 20)
                #stt_ctt = profit[token][2] * volume * 0.00025
                buy_tran = profit[token][1] * volume * 0.000009
                sell_tran = profit[token][2] * volume * 0.000009
                gst = (buy_brookerage + sell_brookerage + buy_tran + sell_tran) * 0.18
                sebi_total = round((profit[token][1] + profit[token][2]) * volume * 0.000001, 0)
                stamp_charges = profit[token][1] * volume * 0.000001
                profit[token][5] = sebi_total + gst + sell_tran + buy_tran + buy_brookerage + sell_brookerage + stamp_charges
                profit[token][3] = ((profit[token][2] - profit[token][1]) * volume) - profit[token][5]
                profit[token][6] = profit[token][3] - profit[token][5]
                profit_temp = pd.DataFrame([profit[token]],
                                           columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges",
                                                    "final_profit"])
                profit_Final = profit_Final.append(profit_temp)
                profit_Final.drop_duplicates(keep='first', inplace=True)
                profit[token][1] = 0
                profit[token][2] = 0
        for x in range(len(profit_Final)):
            carry_forward = carry_forward + profit_Final.iloc[-(x + 1), 6]

        Order_data = kite.order_history(Orderid)
        for item in Order_data:
            if item['status'] == "COMPLETE":
                traded_price = item['average_price']
                traded_quantity = item['quantity'] * 1000
                Brokerage = min(((traded_price * traded_quantity) * (.03 / 100))*2, 40)
                #STT = (traded_price * traded_quantity) * (.03 / 100)
                TNXChrgs = ((traded_price * traded_quantity) * 2) * (.0009 / 100)
                GST = (Brokerage + TNXChrgs) * (18 / 100)
                SEBIChrgs = ((traded_price * 2) * traded_quantity) * .0000005
                StampDuty = ((traded_price * 2) * traded_quantity) * .000001
                order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty
                if carry_forward < 0:
                    target_amount = abs(order_charges * -2 + carry_forward) / traded_quantity
                else:
                    target_amount = abs(order_charges * 2)/traded_quantity
                if direction == "Up":
                    return traded_price + target_amount
                elif direction == "Down":
                    return traded_price - target_amount
    except Exception as e:
        traceback.print_exc()
        target(Orderid, direction)


def ATR(df, n):  # df is the DataFrame, n is the period 7,14 ,etc
    try:
        df['H-L'] = abs(df['High'].astype(float)-df['Low'].astype(float))
        df['H-PC'] = abs(df['High'].astype(float)-df['Close'].astype(float).shift(1))
        df['L-PC'] = abs(df['Low'].astype(float)-df['Close'].astype(float).shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        df['ATR'] = np.nan
        df.ix[n-1, 'ATR'] = df['TR'][:n-1].mean()  # .ix is deprecated from pandas version- 0.19
        for i in range(n, len(df)):
            df['ATR'][i] = (df['ATR'][i-1]*(n-1) + df['TR'][i])/n
        return
    except Exception as e:
        traceback.print_exc()


def history(stock):
    global RENKO_Final, ohlc_final_1min
    try:
        with urlopen(
                "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=NSE:" + stock + "&interval=1min&outputsize=full&apikey=08AXPZ0UQEVKUSD8") as response:
            source = response.read()
            data = json.loads(source)
            minute_data = data["Time Series (1min)"]
            df = pd.DataFrame.from_dict(minute_data, orient='index')
            df.drop(['5. volume'], axis=1, inplace=True)
            df.sort_index(axis=0, ascending=True, inplace=True)
            df.rename(columns={'1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close'}, inplace=True)
            Position = ''

            # print(json.dumps(minute_data, indent=2))
            ATR(df, 14)
            renkoData_his = {'BrickSize': 0, 'Open': 0.0, 'Close': 0.0, 'Color': ''}
            renkoData_his['BrickSize'] = round(df['ATR'][-1], 2)  # This can be set manually as well!
            renkoData_his['Open'] = renkoData_his['BrickSize'] + renkoData_his['Close']  # This can be done the otherway round
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
            RENKO_Final = RENKO_Final.append(finalRenkodf)
            print(RENKO_Final)

            df['Symbol'] = stock
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'Time'}, inplace=True)
            df['SMA'] = df.Close.rolling(10).mean()
            df['TMA'] = df.SMA.rolling(10).mean()
            df = df[['Symbol', 'Time', 'Open', 'High', 'Low', 'Close', 'TR', 'ATR', 'SMA', 'TMA']]
            # print(df.to_string())
            ohlc_final_1min = ohlc_final_1min.append(df)
            print(ohlc_final_1min)
    except Exception as e:
        traceback.print_exc()


def calculate_ohlc_one_minute(company_data):
    global ohlc_final_1min, ohlc_temp, RENKO_temp, RENKO_Final, candle_thread_running, HA_temp, HA_Final
    try:
        # below if condition is to check the data being received, and the data present are of the same minute or not
        candle_thread_running = "YES"
        if (str(((company_data["timestamp"]).replace(second=0))) != ohlc[company_data['instrument_token']][1]) and (ohlc[company_data['instrument_token']][1] != "Time"):
            ohlc_temp = pd.DataFrame([ohlc[company_data['instrument_token']]], columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
            HA_temp = pd.DataFrame([HA[company_data['instrument_token']]], columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
            #print(ohlc_temp.head(), ohlc_final_1min.head())
        # Calculating True Range
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
                ohlc_temp.iloc[-1, 6] = round(max((abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 3]) - (ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4])),
                                                   abs((ohlc_temp.iloc[-1, 4]) - (ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 4])))), 2)
            else:
                ohlc_temp.iloc[-1, 6] = round(abs((ohlc_temp.iloc[-1, 3]) - (ohlc_temp.iloc[-1, 4])), 2)
        # True Range Calculation complete for ohlc
        # Calculating ATR for ohlc
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 13:
                ohlc_temp.iloc[-1, 7] = 0

            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] * 13) + ohlc_temp.iloc[-1, 6]) / 14, 2)
                '''a = [ohlc_temp.iloc[-1, 6], ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-10, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-11, 6],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-12, 6]]
                ohlc_temp.iloc[-1, 7] = round(sum(a)/13, 2)'''

            '''elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]*13) + ohlc_temp.iloc[-1, 6])/14, 2)'''
        # ATR Calculation complete for ohlc
        # Calculating SMA for ohlc
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 10:
                ohlc_temp.iloc[-1, 8] = 0
            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 10:
                b = [ohlc_temp.iloc[-1, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                ohlc_temp.iloc[-1, 8] = round(sum(b) / 10, 2)
        # SMA Calculation complete for ohlc

        # Calculating Triangular moving average for ohlc
            if len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                ohlc_temp.iloc[-1, 9] = 0
            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                c = [ohlc_temp.iloc[-1, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 8],
                     ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 8]]
                ohlc_temp.iloc[-1, 9] = round((sum(c) / 10), 2)
        # TMA calculation complete for ohlc

        # adding the row into the final ohlc table
            ohlc_final_1min = ohlc_final_1min.append(ohlc_temp)
            HA_Final = HA_Final.append(HA_temp)
            # print(ohlc_temp.to_string())

            # making ohlc for new candle
            ohlc[company_data['instrument_token']][2] = company_data['last_price']  # open
            ohlc[company_data['instrument_token']][3] = company_data['last_price']  # high
            ohlc[company_data['instrument_token']][4] = company_data['last_price']  # low
            ohlc[company_data['instrument_token']][5] = company_data['last_price']  # close
            ohlc[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']

        if ohlc[company_data['instrument_token']][3] < company_data['last_price']:  # calculating high
            ohlc[company_data['instrument_token']][3] = company_data['last_price']

        if ohlc[company_data['instrument_token']][4] > company_data['last_price'] or \
                ohlc[company_data['instrument_token']][4] == 0:  # calculating low
            ohlc[company_data['instrument_token']][4] = company_data['last_price']

        ohlc[company_data['instrument_token']][5] = company_data['last_price']  # closing price
        ohlc[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))

        #starting to calculate the RENKO table
        if (len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):# or (len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0):  # checking if there is atleast 1 candle in OHLC Dataframe or RENKO Dataframe
            if (ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != 0):# or (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] != [0, 'NaN']):  #checking that we do not have the ATR value as 0
                if RENKO[company_data['instrument_token']][0] == "Symbol":
                    RENKO[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
                ########################################################
                if RENKO[company_data['instrument_token']][1] == 0:  # assigning the first, last price of the tick to open
                    RENKO[company_data['instrument_token']][1] = company_data['last_price']
                ########################################################
                if RENKO[company_data['instrument_token']][3] == "Signal":
                    if (company_data['last_price'] >= ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + RENKO[company_data['instrument_token']][1]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])

                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif (company_data['last_price']<= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]

                if RENKO[company_data['instrument_token']][3] == "BUY":
                    if (company_data['last_price'] >= ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7] + RENKO[company_data['instrument_token']][1]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] <= RENKO[company_data['instrument_token']][1] - (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2] - RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]) - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                if RENKO[company_data['instrument_token']][3] == "SELL":
                    if (company_data['last_price']<= RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]):
                        RENKO[company_data['instrument_token']][2] = RENKO[company_data['instrument_token']][1] - ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "SELL"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
                    elif company_data['last_price'] >= RENKO[company_data['instrument_token']][1] + (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] - RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]) + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]:
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1]
                        RENKO[company_data['instrument_token']][2] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 1] + ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]
                        RENKO[company_data['instrument_token']][3] = "BUY"
                        RENKO_temp = pd.DataFrame([RENKO[company_data['instrument_token']]], columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
                        # Calculating SMA
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) <= 9:
                            RENKO_temp.iloc[-1, 5] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 9:
                            d = [RENKO_temp.iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 2],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 2], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 2]]
                            RENKO_temp.iloc[-1, 5] = round(sum(d) / 10, 2)
                        # SMA Calculation complete

                        # Calculating Triangular moving average
                        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 19:
                            RENKO_temp.iloc[-1, 6] = 0
                        elif len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 19:
                            e = [RENKO_temp.iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-2, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-3, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-4, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-5, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-6, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-7, 5],
                                 RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-8, 5], RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-9, 5]]
                            RENKO_temp.iloc[-1, 6] = round((sum(e) / 10), 2)
                        # TMA calculation complete

                        RENKO_Final = RENKO_Final.append(RENKO_temp, sort=False)
                        #print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
        if (len(HA_Final.loc[
                        HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) < 1):
            if HA[company_data['instrument_token']][0] == "Symbol":
                HA[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
            HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            HA[company_data['instrument_token']][2] = (ohlc[company_data['instrument_token']][2] +
                                                       ohlc[company_data['instrument_token']][5]) / 2
            HA[company_data['instrument_token']][3] = ohlc[company_data['instrument_token']][3]
            HA[company_data['instrument_token']][4] = ohlc[company_data['instrument_token']][4]
            HA[company_data['instrument_token']][5] = (ohlc[company_data['instrument_token']][2] +
                                                       ohlc[company_data['instrument_token']][3] +
                                                       ohlc[company_data['instrument_token']][4] +
                                                       ohlc[company_data['instrument_token']][5]) / 4
        if (len(HA_Final.loc[
                        HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1):
            if HA[company_data['instrument_token']][0] == "Symbol":
                HA[company_data['instrument_token']][0] = trd_portfolio[company_data['instrument_token']]['Symbol']
            HA[company_data['instrument_token']][1] = str(((company_data["timestamp"]).replace(second=0)))
            HA[company_data['instrument_token']][5] = (ohlc[company_data['instrument_token']][2] + ohlc[company_data['instrument_token']][3] + ohlc[company_data['instrument_token']][4] + ohlc[company_data['instrument_token']][5])/4
            HA[company_data['instrument_token']][2] = (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2] + HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5])/2
            HA[company_data['instrument_token']][3] = max(ohlc[company_data['instrument_token']][3], HA[company_data['instrument_token']][2], HA[company_data['instrument_token']][5])
            HA[company_data['instrument_token']][4] = min(HA[company_data['instrument_token']][4], HA[company_data['instrument_token']][2], HA[company_data['instrument_token']][5])
        candle_thread_running = "NO"
    except Exception as e:
        traceback.print_exc()


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc()


def order_status(token, orderid, type):
    try:
        order_details = kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                if type == 'SELL':
                    trd_portfolio[token]['Direction'] = "Down"
                    trd_portfolio[token]['Target_order'] = "NO"
                    print(trd_portfolio[token]['Direction'])
                    break
                elif type == 'BUY':
                    trd_portfolio[token]['Direction'] = "Up"
                    trd_portfolio[token]['Target_order'] = "NO"
                    print(trd_portfolio[token]['Direction'])
                    break
            elif item['status'] == "REJECTED":
                print("order got rejected", trd_portfolio[token]['Direction'], trd_portfolio[token]['Target_order'])
                break
        else:
            time.sleep(1)
            order_status(token, orderid, type)
    except Exception as e:
        order_status(token, orderid, type)
        traceback.print_exc()

def target_order_status(orderid):
    try:
        details = kite.order_history(orderid)
        for item in details:
            if item['status'] == "OPEN":
                return "OPEN"
                break
            elif item['status'] == "REJECTED":
                return "REJECTED"
                break
        else:
            time.sleep(1)
            target_order_status(orderid)
    except Excepton as e:
        target_order_status(orderid)
        traceback.print_exc()

def trigger():
    try:
        while day_profit_percent < 10:
            for x in trd_portfolio:
                if (len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']]) >= 1):
                    if (HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 2] == HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 3]) and (HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 2] > HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 5]):
                        if trd_portfolio[x]['Positions'] > 0:
                            kite.modify_order(variety="regular", order_id=trd_portfolio[x]['Target_order_id'],
                                              order_type=kite.ORDER_TYPE_MARKET)
                            time.sleep(2)
                            trd_portfolio[x]['Positions'] = positions(x)
                        elif trd_portfolio[x]['Positions'] == 0:
                            if trd_portfolio[x]['Direction'] != "Down":
                                if trd_portfolio[x]['Tradable_quantity'] > 0:
                                    trd_portfolio[x]['Orderid'] = kite.place_order(variety="regular",
                                                                                       exchange=kite.EXCHANGE_NSE,
                                                                                       tradingsymbol=trd_portfolio[x][
                                                                                           'Symbol'],
                                                                                       transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                                       quantity=trd_portfolio[x][
                                                                                           'Tradable_quantity'],
                                                                                       order_type=kite.ORDER_TYPE_MARKET,
                                                                                       product=kite.PRODUCT_MIS)
                                    print(trd_portfolio[x]['Orderid'])
                                    time.sleep(2)
                                    order_status(x, trd_portfolio[x]['Orderid'], 'SELL')
                                    trd_portfolio[x]['Positions'] = positions(x)
                    if (HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 2] ==
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 4]) and (
                            HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 2] <
                            HA_Final.loc[HA_Final.Symbol == trd_portfolio[x]['Symbol']].iloc[-1, 5]):
                        if trd_portfolio[x]['Positions'] < 0:
                            kite.modify_order(variety="regular", order_id=trd_portfolio[x]['Target_order_id'],
                                              order_type=kite.ORDER_TYPE_MARKET)
                            time.sleep(2)
                            trd_portfolio[x]['Positions'] = positions(x)
                        elif trd_portfolio[x]['Positions'] == 0:
                            if trd_portfolio[x]['Direction'] != "Up":
                                if trd_portfolio[x]['Tradable_quantity'] > 0:
                                    trd_portfolio[x]['Orderid'] = kite.place_order(variety="regular",
                                                                                       exchange=kite.EXCHANGE_NSE,
                                                                                       tradingsymbol=trd_portfolio[x][
                                                                                           'Symbol'],
                                                                                       transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                                       quantity=trd_portfolio[x][
                                                                                           'Tradable_quantity'],
                                                                                       order_type=kite.ORDER_TYPE_MARKET,
                                                                                       product=kite.PRODUCT_MIS)
                                    print(trd_portfolio[x]['Orderid'])
                                    time.sleep(2)
                                    order_status(x, trd_portfolio[x]['Orderid'], 'BUY')
                                    trd_portfolio[x]['Positions'] = positions(x)
                        if trd_portfolio[x]['Positions'] > 0:
                            if trd_portfolio[x]['Target_order'] != "YES":
                                trd_portfolio[x]['Target_order_id'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE, tradingsymbol=trd_portfolio[x]['Symbol'],
                                                 transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=abs(trd_portfolio[x]['Positions']),
                                                 order_type=kite.ORDER_TYPE_LIMIT, price=round(target(trd_portfolio[x]['Orderid'], 'Up'), 1), product=kite.PRODUCT_MIS)
                                if target_order_status(trd_portfolio[x]['Target_order_id']) == "OPEN":
                                    trd_portfolio[x]['Target_order'] = "YES"
                        if trd_portfolio[x]['Positions'] < 0:
                            if trd_portfolio[x]['Target_order'] != "YES":
                                trd_portfolio[x]['Target_order_id'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE, tradingsymbol=trd_portfolio[x]['Symbol'],
                                                 transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=abs(trd_portfolio[x]['Positions']),
                                                 order_type=kite.ORDER_TYPE_LIMIT, price=round_down(target(trd_portfolio[x]['Orderid'], 'Down'), 1), product=kite.PRODUCT_MIS)
                                if target_order_status(trd_portfolio[x]['Target_order_id']) == "OPEN":
                                    trd_portfolio[x]['Target_order'] = "YES"
        quantity()
    except ReadTimeout:
        trigger()
        traceback.print_exc()
        pass
    except exceptions.NetworkException:
        trigger()
        traceback.print_exc()
        pass
    except Exception as e:
        trigger()
        traceback.print_exc()

order_trigger_loop_initiator = threading.Thread(target=trigger())
order_trigger_loop_initiator.start()


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    global ohlc_final_1min, RENKO_Final, final_position, order_quantity, ohlc_temp, candle_thread_running, renko_thread_running
    try:
        for company_data in ticks:
            trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
            if trd_portfolio[company_data['instrument_token']]['Tradable_quantity'] == 0:
                quantity()
            if candle_thread_running != "YES":
                if (company_data['last_trade_time'].time()) > datetime.time(9,00,00) and (company_data['last_trade_time'].time()) < datetime.time(16,45,00):
                    candle = threading.Thread(target=calculate_ohlc_one_minute, args=(company_data,))
                    candle.start()
            else:
                pass
    except Exception as e:
        traceback.print_exc()


def on_connect(ws, response):
    ws.subscribe([x for x in trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in trd_portfolio])

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect()