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

api_k = "dysoztj41hntm1ma";  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94";  # api_secret
access_token = "qn7QMYiNPwJwDDTnDDgXUKjX68flC3Bo"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

opening_margin = KiteConnect.margins(kite)
day_margin = opening_margin['equity']['net']

candle_thread_running = ""
renko_thread_running = ""

trd_portfolio = {779521: {"Symbol": "SBIN", "max_quantity": 10000, 'Direction': "", 'Orderid': 0, 'Target_order': '', 'Target_order_id': 0}}


ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"])
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(columns=["Symbol", "SELL Price", "BUY Price", "Profit", "Volume", "Charges", "final_profit"])

'''
# for loop to order history for all the stocks
for x, y in trd_portfolio.items():
    for z in y:
        if z == "Symbol":
            history(y[z])
            time.sleep(15)
'''
for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]


def positions(token):
    pos = kite.positions()
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
            return current_pos

def day_positions():
    pos = kite.positions()
    day_pos = pos['day']
    posdf = pd.DataFrame(day_pos)
    if posdf.empty:
        return 0
    else:
        return posdf['quantity'].sum()


def attained_profit():
    global day_margin, profit_Final, profit_temp
    current_profit = 0
    orders = kite.orders()
    for x in orders:
        price = x['average_price']
        symbol = x['tradingsymbol']
        type = x['transaction_type']
        token = x['instrument_token']
        volume = x['quantity']
        if type == 'BUY':
            profit[token][1] = price
        elif type == 'SELL':
            profit[token][2] = price
        profit[token][0] = symbol
        profit[token][4] = volume
        if (profit[token][1] != 0) & (profit[token][2] != 0):
            buy_brookerage = min((profit[token][1] * volume * 0.0001), 20)
            sell_brookerage = min((profit[token][2] * volume * 0.0001), 20)
            stt_ctt = profit[token][2] * volume * 0.00025
            buy_tran = profit[token][1] * volume * 0.0000325
            sell_tran = profit[token][2] * volume * 0.0000325
            gst = (buy_brookerage + sell_brookerage + buy_tran + sell_tran) * 0.18
            sebi_total = round((profit[token][1] + profit[token][2]) * 0.000001, 0)
            total_charges = sebi_total + gst + sell_tran + buy_tran + stt_ctt + buy_brookerage + sell_brookerage
            profit[token][3] = ((profit[token][2] - profit[token][1]) * volume) - total_charges
            current_profit = current_profit + profit[token][3]
            profit[token][1] = 0
            profit[token][2] = 0
    return (current_profit / day_margin) * 100


def quantity(ltp, token):
    mar = KiteConnect.margins(kite)
    equity_mar = mar['equity']['net']
    if ((equity_mar / ltp) * 12.5)-10 < 1:
        return 0
    else:
        return int(round(min(((equity_mar / ltp) * 12.5)-10, trd_portfolio[token]['max_quantity']), 0))

    '''maxquantity = min(equity_mar/ltp,5000)
    multiplier = 0
    while (multiplier * 75) < maxquantity:
        multiplier = multiplier+1
    else:
        return (multiplier-1) * 75'''


def target(Orderid, direction):
    global profit_Final, profit_temp
    day_profit = 0
    carry_forward = 0
    trade_profit = 0
    orders = kite.orders()
    for x in orders:
        price = x['average_price']
        symbol = x['tradingsymbol']
        type = x['transaction_type']
        token = x['instrument_token']
        volume = x['quantity']
        if type == 'BUY':
            profit[token][1] = price
        elif type == 'SELL':
            profit[token][2] = price
        profit[token][0] = symbol
        profit[token][4] = volume
        if (profit[token][1] != 0) & (profit[token][2] != 0):
            buy_brookerage = min((profit[token][1] * volume * 0.0001), 20)
            sell_brookerage = min((profit[token][2] * volume * 0.0001), 20)
            stt_ctt = profit[token][2] * volume * 0.00025
            buy_tran = profit[token][1] * volume * 0.0000325
            sell_tran = profit[token][2] * volume * 0.0000325
            gst = (buy_brookerage + sell_brookerage + buy_tran + sell_tran) * 0.18
            sebi_total = round((profit[token][1] + profit[token][2]) * 0.000001, 0)
            profit[token][5] = sebi_total + gst + sell_tran + buy_tran + stt_ctt + buy_brookerage + sell_brookerage
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
            traded_quantity = item['quantity']
            Brokerage = min(((traded_price * traded_quantity) * (.01 / 100))*2, 40)
            STT = (traded_price * traded_quantity) * (.03 / 100)
            TNXChrgs = ((traded_price * traded_quantity) * 2) * (.00325 / 100)
            GST = (Brokerage + TNXChrgs) * (18 / 100)
            SEBIChrgs = ((traded_price * 2) * traded_quantity) * (.0000015 / 100)
            StampDuty = ((traded_price * 2) * traded_quantity) * (.003 / 100)
            order_charges = Brokerage + STT + TNXChrgs + GST + SEBIChrgs + StampDuty
            if carry_forward < 0:
                target_amount = abs(order_charges * -2 + carry_forward) / traded_quantity
            else:
                target_amount = abs(order_charges * 2)/traded_quantity
            if direction == "Up":
                return traded_price + target_amount
            elif direction == "Down":
                return traded_price - target_amount


def calcpsoitions(Token, quantity, Last_price, Signal):
    global profit_Final, profit_temp, profit, overall_profit
    profit[Token][0] = trd_portfolio[Token]
    if Signal == "SELL":
        profit[Token][1] = Last_price
    elif Signal == "BUY":
        profit[Token][2] = Last_price
    if profit[Token][1]!=0 and profit[Token][2]!=0:
        BuyBrokerage = min((((profit[Token][2])*quantity)*(.01/100)),20)
        SellBrokerage = min((((profit[Token][1]) * quantity) * (.01 / 100)), 20)
        STT = ((profit[Token][2])*quantity) * (.025/100)
        TNXChrgs = ((profit[Token][2])*quantity) * (.00325/100)
        GST = (STT + TNXChrgs) * (18/100)
        SEBIChrgs = ((profit[Token][2] + profit[Token][1]) * quantity) * (.0000015/100)
        StampDuty = ((profit[Token][2] + profit[Token][1]) * quantity) * (.003/100)
        profit[Token][3] = ((profit[Token][1] - profit[Token][2]) * quantity) - (BuyBrokerage + SellBrokerage + STT + TNXChrgs + GST + SEBIChrgs + StampDuty)
        profit_temp = pd.DataFrame([profit[x]], columns=["Symbol", "SELL Price", "BUY Price", "Profit"])
        profit_Final = profit_Final.append(profit_temp, sort=False)
        overall_profit += profit_Final.iloc[-1, 3]
        profit[Token][1] = 0
        profit[Token][2] = 0
        print(profit_Final.tail(3))
        print(overall_profit)


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
    global RENKO_Final, ohlc_final_1min
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


def calculate_ohlc_one_minute(company_data):
    global ohlc_final_1min, ohlc_temp, RENKO_temp, RENKO_Final, candle_thread_running
    try:
        # below if condition is to check the data being received, and the data present are of the same minute or not
        candle_thread_running = "YES"
        if (str(((company_data["timestamp"]).replace(second=0))) != ohlc[company_data['instrument_token']][1]) and (ohlc[company_data['instrument_token']][1]!= "Time"):
            ohlc_temp = pd.DataFrame([ohlc[company_data['instrument_token']]], columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
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

            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) == 13:
                a = [ohlc_temp.iloc[-1, 6], ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 6],
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
                ohlc_temp.iloc[-1, 7] = round(sum(a)/13, 2)

            elif len(ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 13:
                ohlc_temp.iloc[-1, 7] = round(((ohlc_final_1min.loc[ohlc_final_1min.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 7]*13) + ohlc_temp.iloc[-1, 6])/14, 2)
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
                        print(RENKO_temp.to_string())
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
                        print(RENKO_temp.to_string())
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
                        print(RENKO_temp.to_string())
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
                        print(RENKO_temp.to_string())
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
                        print(RENKO_temp.to_string())
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
                        print(RENKO_temp.to_string())
                        RENKO[company_data['instrument_token']][1] = RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 2]
        candle_thread_running = "NO"
    except Exception as e:
        traceback.print_exc()


def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier

def order_status(token, orderid, type):
    order_details = kite.order_history(orderid)
    for item in order_details:
        if item['status'] == "COMPLETE":
            if type == 'SELL':
                trd_portfolio[token]['Direction'] = "Down"
                trd_portfolio[token]['Target_order'] = "NO"
                print(trd_portfolio[token]['Direction'], trd_portfolio[token]['Target_order'])
                break
            elif type == 'BUY':
                trd_portfolio[token]['Direction'] = "Up"
                trd_portfolio[token]['Target_order'] = "NO"
                print(trd_portfolio[token]['Direction'], trd_portfolio[token]['Target_order'])
                break
        elif item['status'] == "REJECTED":
            print("order got rejected", trd_portfolio[token]['Direction'], trd_portfolio[token]['Target_order'])
            break
    else:
        time.sleep(1)
        order_status(token, orderid, type)

def target_order_status(orderid):
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


def RENKO_TRIMA(company_data):
    global ohlc_final_1min, RENKO_Final, final_position, order_quantity, RENKO, RENKO_temp, Direction, Orderid, Target_order, Target_order_id, renko_thread_running
    try:
        renko_thread_running = "YES"
        if len(RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) > 0:
            if attained_profit() < 4:
                if (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 3] == "SELL"):
                    if positions(company_data['instrument_token']) > 0:
                        kite.modify_order(variety="regular", order_id=trd_portfolio[company_data['instrument_token']]['Target_order_id'], order_type=kite.ORDER_TYPE_MARKET)
                        time.sleep(5)
                    if trd_portfolio[company_data['instrument_token']]['Direction'] != "Down":
                        if positions(company_data['instrument_token']) == 0:
                            if quantity(company_data['last_price'], company_data['instrument_token']) > 0:
                                trd_portfolio[company_data['instrument_token']]['Orderid'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE, tradingsymbol=trd_portfolio[company_data['instrument_token']]['Symbol'],
                                             transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=quantity(company_data['last_price'], company_data['instrument_token']), order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_MIS)
                                print(trd_portfolio[company_data['instrument_token']]['Orderid'])
                                time.sleep(1)
                                order_status(company_data['instrument_token'], trd_portfolio[company_data['instrument_token']]['Orderid'], 'SELL')
                elif (RENKO_Final.loc[RENKO_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 3] == "BUY"):
                    if (positions(company_data['instrument_token']) < 0):
                        kite.modify_order(variety="regular", order_id=trd_portfolio[company_data['instrument_token']]['Target_order_id'], order_type=kite.ORDER_TYPE_MARKET)
                        time.sleep(5)
                    if trd_portfolio[company_data['instrument_token']]['Direction'] != "Up":
                        if positions(company_data['instrument_token']) == 0:
                            if quantity(company_data['last_price'], company_data['instrument_token']) > 0:
                                trd_portfolio[company_data['instrument_token']]['Orderid'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE, tradingsymbol=trd_portfolio[company_data['instrument_token']]['Symbol'],
                                             transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=quantity(company_data['last_price'], company_data['instrument_token']), order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_MIS)
                                print(trd_portfolio[company_data['instrument_token']]['Orderid'])
                                time.sleep(1)
                                order_status(company_data['instrument_token'], trd_portfolio[company_data['instrument_token']]['Orderid'], 'BUY')
                if (positions(company_data['instrument_token']) > 0):
                    if trd_portfolio[company_data['instrument_token']]['Target_order'] != "YES":
                        trd_portfolio[company_data['instrument_token']]['Target_order_id'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE, tradingsymbol=trd_portfolio[company_data['instrument_token']]['Symbol'],
                                         transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=abs(positions(company_data['instrument_token'])),
                                         order_type=kite.ORDER_TYPE_LIMIT, price=round(target(trd_portfolio[company_data['instrument_token']]['Orderid'], 'Up'), 1), product=kite.PRODUCT_MIS)
                        if target_order_status(trd_portfolio[company_data['instrument_token']]['Target_order_id']) == "OPEN":
                            trd_portfolio[company_data['instrument_token']]['Target_order'] = "YES"
                if ((positions(company_data['instrument_token'])) < 0):
                    if trd_portfolio[company_data['instrument_token']]['Target_order'] != "YES":
                        trd_portfolio[company_data['instrument_token']]['Target_order_id'] = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE, tradingsymbol=trd_portfolio[company_data['instrument_token']]['Symbol'],
                                         transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=abs(positions(company_data['instrument_token'])),
                                         order_type=kite.ORDER_TYPE_LIMIT, price=round_down(target(trd_portfolio[company_data['instrument_token']]['Orderid'], 'Down'), 1), product=kite.PRODUCT_MIS)
                        if target_order_status(trd_portfolio[company_data['instrument_token']]['Target_order_id']) == "OPEN":
                            trd_portfolio[company_data['instrument_token']]['Target_order'] = "YES"
        renko_thread_running = "NO"
    except ReadTimeout:
        pass
    except exceptions.NetworkException:
        pass
    except Exception as e:
        traceback.print_exc()

def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    global ohlc_final_1min, RENKO_Final, final_position, order_quantity, ohlc_temp, candle_thread_running, renko_thread_running
    try:
        for company_data in ticks:
            if (candle_thread_running != "YES") and (renko_thread_running != "YES"):
                if (company_data['last_trade_time'].time()) > datetime.time(9,15,00) and (company_data['last_trade_time'].time()) < datetime.time(15,20,00):
                    candle = threading.Thread(target=calculate_ohlc_one_minute, args=(company_data,))
                    candle.start()
                    renko = threading.Thread(target=RENKO_TRIMA, args=(company_data,))
                    renko.start()
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
