from kiteconnect import KiteTicker, KiteConnect
import pandas as pd
import backtrader as bt
import datetime
import traceback
import os.path
import sys
import numpy as np
# import talib
import matplotlib.dates as mpl_dates
import matplotlib.pyplot as plt
import mplfinance as mpf

acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()
CE_symbol = ''
CE_ins_tkn = 0
PE_ins_tkn = 0
PE_symbol = ''
pos = ''
num = 0
percentchange = []
stop_loss = 0
no_of_success_trades = 0
no_of_fail_trades = 0
target_price = 0
profit_amount = 0
expected_profit_amount = 0
loss_amount = 0
streak = []
quantity = 100
bp = 0
sp = 0
toy = []
highs = []
lows = []
previous_high = None
current_high = None
current_high_loc = None
previous_low = None
current_low = None
current_low_loc = None
previous_highs_list = []
previous_lows_list = []
larger_trend = None
candle_body_size = []
average_candle_size = 0
levels = []
last_5_closes = []
resistance = 0
support = 0

transaction_list = []

positive_indications = ['Hammer', "Bullish Marubozu", "Tweezer Bottom", "Bullish Engulfing", "Goutham Bullish", "Bullish Piercing"]
negative_indications = ['Shooting Star', "Bearish Marubozu", "Tweezer Top", "Bearish Engulfing", "Goutham Bearish", "Bearish Piercing"]

nifty_ohlc = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "HL2", "Trend", "Max_Close", "Min_Close"]
#             0, 1, 2, 3,     4    ,           5         ,           6           ,   7  ,     8  ,      9     ,      10
nifty_ohlc_1 = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "HL2", "Trend", "Max_Close", "Min_Close"]
nifty_ohlc_2 = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "HL2", "Trend", "Max_Close", "Min_Close"]

from_date = '2022-06-17 09:15:00'
to_date = '2022-06-17 15:30:00'
duration = '3minute'
date = datetime.date(2022, 6, 17)

historical_data = kite.historical_data(256265, from_date, to_date, duration)
his_df = pd.DataFrame(historical_data)
his_df['date'] = his_df['date'].dt.time
his_df['Single_Candle_Pattern'] = "Pattern"
his_df['Double_Candle_Pattern'] = "Pattern"
his_df['HL2'] = "HL2"
his_df['Trend'] = "Trend"
his_df['max_close'] = "max_close"
his_df['min_close'] = "min_close"
his_df.to_csv("historical_data.csv")
# print(his_df.columns)

# This is for plotting
bf = pd.DataFrame(historical_data)
bf.index = pd.DatetimeIndex(bf['date'])
trades_list = [0]
trades_list = trades_list * len(bf)

def plot_without_trades():
    mpf.plot(bf, type='candle', hlines=levels)

def plot_with_trades():
    apd = mpf.make_addplot(trades_list, type='scatter')
    # mpf.make_addplot(transaction_list, type='scatter', marker='^')]
    mpf.plot(bf, type='candle', hlines=levels, addplot=apd)

def expiry_date():
    d = datetime.date.today()
    while d.weekday() != 3:
        d += datetime.timedelta(1)

    if d == datetime.date.today():
        d += datetime.timedelta(7)
    return d


option_expiry_date = expiry_date()
# The three commented lines below should be called only when the instrument list is out of date and the fourth line should be commented at that moment
instrument_list = kite.instruments()
df = pd.DataFrame(instrument_list)
# df.to_csv('instrument_list.csv')
# df = pd.read_csv('instrument_list.csv')

def nifty_spot():
    nifty_ltp = (kite.ltp('NSE:NIFTY 50')).get('NSE:NIFTY 50').get('last_price')
    return round(nifty_ltp / 100) * 100

def options_list():
    global CE_symbol, CE_ins_tkn, PE_ins_tkn, PE_symbol
    closest_strike = nifty_spot()
    valid_options = df.loc[(df['segment'] == 'NFO-OPT') & (df['name'] == 'NIFTY') & (
                df['expiry'].astype(str) == str(option_expiry_date)) & (df['strike'] == closest_strike)]
    print(valid_options.to_string())
    CE_ins_tkn = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 0]
    PE_ins_tkn = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 0]
    CE_symbol = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 3]
    PE_symbol = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 3]
    print(CE_ins_tkn, PE_ins_tkn, CE_symbol, PE_symbol)


nifty_spot()
options_list()

call_historical_data = kite.historical_data(CE_ins_tkn, from_date, to_date, duration)
call_his_df = pd.DataFrame(call_historical_data)
call_his_df['date'] = call_his_df['date'].dt.time
call_his_df.to_csv("call_his_df.csv")
put_historical_data = kite.historical_data(PE_ins_tkn, from_date, to_date, duration)
put_his_df = pd.DataFrame(put_historical_data)
put_his_df['date'] = put_his_df['date'].dt.time
put_his_df.to_csv("put_his_df.csv")
nifty_historical_data = kite.historical_data(256265, from_date, to_date, duration)
nifty_his_df = pd.DataFrame(nifty_historical_data)
nifty_his_df['date'] = nifty_his_df['date'].dt.time
nifty_his_df.to_csv("nifty historical data")

# method calculating the candle stick patterns
def single_candle_pattern(open, high, low, close):
    if close > open and open-low >= 2*(close-open) and (high == close or high-close < close-open):
        return "Hammer"
    elif open > close and high-open >= 2*(open-close) and (close == low or close-low < open-close):
        return "Shooting Star"
    elif (open == low or (open-low < (.2 * (close-open)))) and open < close and (close == high or (high - close < (.2 * (close - open)))):
        return "Bullish Marubozu"
    elif (open == high or (high-open < (.2 * (open - close)))) and open > close and (close == low or (close-low < (.2 * (open - close)))):
        return "Bearish Marubozu"
    elif abs(close - open)/(high - low) < 0.1 and (high - max(close, open)) > (3 * abs(close - open)) and (min(close, open) - low) > (3 * abs(close - open)):
        return "Doji"
    elif abs(close - open)/(high - low) < 0.1 and (min(close, open) - low) > (3 * abs(close - open)) and (high - max(close, open)) < abs(close - open):
        return "Dragonfly Doji"
    elif abs(close-open)/(high-low)<0.1 and (high-max(close,open))>(3*abs(close-open)) and (min(close,open)-low)<=abs(close-open):
        return "Gravestone Doji"
    elif close<open and 0.3>abs(close-open)/(high-low)>=0.1 and (min(close,open)-low)>=(2*abs(close-open)) and (high-max(close,open))>(0.25*abs(close-open)):
        return "Hanging Man Red"
    elif close>open and 0.3>abs(close-open)/(high-low)>=0.1 and (min(close,open)-low)>=(2*abs(close-open)) and (high-max(close,open))>(0.25*abs(close-open)):
        return "Hanging Man Green"
    elif close<open and 0.3>abs(close-open)/(high-low)>=0.1 and (high-max(close,open))>=(2*abs(close-open)) and (min(close,open)-low)<=(0.25*abs(close-open)):
        return "Inverted Hammer Red"
    elif close>open and 0.3>abs(close-open)/(high-low)>=0.1 and (high-max(close,open))>=(2*abs(close-open)) and (min(close,open)-low)<=(0.25*abs(close-open)):
        return "Inverted Hammer Green"
    else:
        return "None"
    pass

def double_candle_pattern(open, high, low, close, open1, high1, low1, close1):
    global average_candle_size
    '''
    if close1<open1 and abs(close1 - open1)/(high1 - low1)>=0.7 and close<open and 0.3>abs(close - open)/(high - low)>=0.1 and abs(low / low1 - 1)<0.05 and abs(close - open)<2*(min(close, open) - low):
        return "Tweezer Bottom"
    elif close1>open1 and abs(close1-open1)/(high1-low1)>=0.7 and close>open and 0.3>abs(close-open)/(high-low)>=0.1 and abs(high/high1-1)<0.05 and abs(close1-open1)<2*(high1-max(close1,open1)):
        return "Tweezer Top"
    elif close1<open1 and 0.3>abs(close1-open1)/(high1-low1)>=0.1 and close>open and abs(close-open)/(high-low)>=0.7 and high1<close and low1>open:
        return "Bullish Engulfing"
    elif close1>open1 and 0.3>abs(close1-open1)/(high1-low1)>=0.1 and close<open and abs(close-open)/(high-low)>=0.7 and high1<open and low1>close:
        return "Bearish Engulfing"
        '''
    if average_candle_size is not None and (close1 >= open) and (open1 <= close) and (close > open) and (close1 < open1):
        return "Bullish Engulfing"
    elif average_candle_size is not None and (close1 <= open) and (open1 >= close) and (close < open) and (close1 > open1):
        return "Bearish Engulfing"
    elif average_candle_size is not None and (close1 < open1) and ((open1+close1)/2 > open > close1) and close > open1:
        return "Goutham Bullish"
    elif average_candle_size is not None and (close1 > open1) and ((open1+close1)/2 < open < close1) and close < open1:
        return "Goutham Bearish"
    elif open1 > close1 > open and close > (close1 + open1)/2 and open < close:
        return "Bullish Piercing"
    elif open1 < close1 < open and close < (close1 + open1)/2 and open > close:
        return "Bearish Piercing"
    else:
        return "None"


def distance_from_mean(level):
    return np.sum([abs(level - y) < average_candle_size for y in levels]) == 0


def low_high(high, low):
    global levels, toy, current_low, current_high, current_low_loc, current_high_loc, previous_high, previous_low, previous_highs_list, larger_trend, candle_body_size, average_candle_size
    try:
        highs.append(high)
        lows.append(low)
        if previous_high is None:
            if current_high is None:
                current_high = high
                current_high_loc = len(highs)
            if current_high is not None and high > current_high:
                current_high = high
                current_high_loc = len(highs)
            elif current_high is not None and high < current_high and len(highs) - current_high_loc >= 4:
                previous_high = current_high
                current_high = 0
                previous_highs_list.append(previous_high)
                if distance_from_mean(previous_high):
                    levels.append(previous_high)
                # print(f'previous high: {previous_high}')
        elif previous_high is not None:
            if current_high == 0:
                if high >= max(highs[-3:]):
                    current_high = high
                    current_high_loc = len(highs)
            elif current_high != 0:
                if high >= current_high:
                    current_high = high
                    current_high_loc = len(highs)
                if len(highs[current_high_loc:]) == 3:
                    previous_high = current_high
                    current_high = 0
                    previous_highs_list.append(previous_high)
                    if distance_from_mean(previous_high):
                        levels.append(previous_high)
                    # print(f'previous high: {previous_high}')

        if previous_low is None:
            if current_low is None:
                current_low = low
                current_low_loc = len(lows)
            if current_low is not None and low < current_low:
                current_low = low
                current_low_loc = len(lows)
            elif current_low is not None and low > current_low and len(lows) - current_low_loc >= 4:
                previous_low = current_low
                current_low = 0
                previous_lows_list.append(previous_low)
                if distance_from_mean(previous_low):
                    levels.append(previous_low)
                # print(f'previous low: {previous_low}')
        elif previous_low is not None:
            if current_low == 0:
                if low >= min(lows[-3:]):
                    current_low = low
                    current_low_loc = len(lows)
            elif current_low != 0:
                if low <= current_low:
                    current_low = low
                    current_low_loc = len(lows)
                if len(lows[current_low_loc:]) == 3:
                    previous_low = current_low
                    current_low = 0
                previous_lows_list.append(previous_low)
                if distance_from_mean(previous_low):
                    levels.append(previous_low)
                # print(f'previous low: {previous_low}')
        if len(previous_lows_list) >= 2 and len(previous_highs_list) >= 1 and previous_lows_list[-2] < previous_lows_list[-1]:
            larger_trend = 'UP'
        elif len(previous_lows_list) >= 1 and len(previous_highs_list) >= 2 and previous_highs_list[-2] > previous_highs_list[-1]:
            larger_trend = "DOWN"
        candle_body_size.append(abs(toy[1]-toy[2]))
        average_candle_size = sum(candle_body_size)/len(candle_body_size)
    except Exception as e:
        traceback.print_exc(e)


def get_nifty_onlc(date, open, high, low, close):
    global last_5_closes, nifty_ohlc, nifty_ohlc_1, nifty_ohlc_2, duration, to_date, highs, current_high, current_high_loc, previous_high, current_low, previous_low, current_low_loc, toy
    try:
        nifty_ohlc_2 = nifty_ohlc_1
        nifty_ohlc_1 = nifty_ohlc
        if nifty_ohlc_1[0] != 0:
            toy = [open, high, low, close, single_candle_pattern(open, high, low, close), double_candle_pattern(open, high, low, close, nifty_ohlc[0], nifty_ohlc[1], nifty_ohlc[2],  nifty_ohlc[3]), 'Three Candle Pattern', 'HL2', 'Trend', 0, 0]
        else:
            toy = [open, high, low, close, single_candle_pattern(open, high, low, close),"Double Candle Pattern", 'Three Candle Pattern', 'HL2', 'Trend', 0, 0]
        nifty_ohlc = toy
        nifty_ohlc[7] = (nifty_ohlc[0] + nifty_ohlc[3])/2
        if nifty_ohlc_2[7] != "HL2":
            if nifty_ohlc_2[7] > nifty_ohlc_1[7] > nifty_ohlc[7]:
                nifty_ohlc[8] = "Down"
            elif nifty_ohlc_2[7] < nifty_ohlc_1[7] < nifty_ohlc[7]:
                nifty_ohlc[8] = "Up"
            else:
                nifty_ohlc[8] = "Flat"
        last_5_closes.append(nifty_ohlc[3])
        if len(last_5_closes) > 5:
            last_5_closes.pop(0)
            nifty_ohlc[9] = max(last_5_closes)
            nifty_ohlc[10] = min(last_5_closes)

        # Hieken ashi table which we can ignore as of now
        '''
        if nifty_ha_ohlc[0] == 0:
            # open
            nifty_ha_ohlc[0] = round((nifty_ohlc[0] + nifty_ohlc[3])/2, 4)
            # high
            nifty_ha_ohlc[1] = nifty_ohlc[1]
            # low
            nifty_ha_ohlc[2] = nifty_ohlc[2]
            # close
            nifty_ha_ohlc[3] = round((nifty_ohlc[0] + nifty_ohlc[1] + nifty_ohlc[2] + nifty_ohlc[3])/4, 4)
        else:
            # open
            nifty_ha_ohlc[0] = round((nifty_ha_ohlc[0] + nifty_ha_ohlc[3]) / 2, 4)
            # close
            nifty_ha_ohlc[3] = round((nifty_ohlc[0] + nifty_ohlc[1] + nifty_ohlc[2] + nifty_ohlc[3])/4, 4)
            # high
            nifty_ha_ohlc[1] = max(nifty_ohlc[1], nifty_ha_ohlc[0], nifty_ha_ohlc[3])
            # low
            nifty_ha_ohlc[2] = min(nifty_ohlc[2], nifty_ha_ohlc[0], nifty_ha_ohlc[3])
            '''
        print(f'Nifty last minute - {date}, Close: {nifty_ohlc[3]}, Pattern: {nifty_ohlc[4]}, Two Candle Pattern: {nifty_ohlc[5]}, Trend: {nifty_ohlc[8]}, Max_Close: {nifty_ohlc[9]}, Min_Close: {nifty_ohlc[10]}')
    except Exception as r:
        traceback.print_exc(r)

# print(his_df.columns)
# his_df = his_df.set_index("date").sort_index()

def reisitance_and_support(close):
    global levels, support, resistance
    levels.sort()
    idx = np.searchsorted(levels, 600)
    # support = [_ for _ in levels if _ < close][-1]
    # resistance = [_ for _ in levels if _ > close][0]
    support = levels[idx-1]
    resistance = levels[idx]


def lowest_low(put_call, row_num):
    temp_low = all_time_low = get_prev_low(put_call, row_num)
    while all_time_low <= temp_low:
        temp_low = all_time_low
        if his_df.iloc[row_num, 0] < datetime.time(9,18,00):
            return all_time_low
        else:
            row_num = row_num- 1
            all_time_low = get_prev_low(put_call, row_num)

    return temp_low


def get_prev_low(token, row_num):
    # combined_from_datetime = datetime.datetime.combine(date, from_to_date)
    # # added_time = combined_from_datetime + datetime.timedelta(minutes=3)
    # combined_to_datetime = combined_from_datetime + datetime.timedelta(minutes=3)
    # temp_his_data = kite.historical_data(token, combined_from_datetime, combined_to_datetime, '3minute')
    if token == 'CE':
        return call_his_df.iloc[row_num, 3]
    elif token == 'PE':
        return put_his_df.iloc[row_num, 3]


def sell_action(x):
    global average_candle_size, pos, target_price, profit_amount, quantity, bp, sp, loss_amount, stop_loss, CE_ins_tkn, positive_indications, negative_indications
    try:
        if pos == '':
            bp = put_his_df.iloc[x + 1, 1]
            trades_list[x+1] = bp
            transaction_list.append('PE BUY')
            pos = 'PE'
            target_price = bp + (bp * .005)
            stop_loss = lowest_low('PE', x)
            print(f'PE - Time: {his_df.iloc[x, 0],}, Previous Double Pattern: {his_df.iloc[x - 1, 7]}')
            # if put_his_df.iloc[x + 1, 2] >= target_price:
            #     sp = target_price
            #     profit_amount += (sp - bp) * quantity
            #     print(
            #         "H Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
            #             his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
            #     print(
            #         "----------------------------------------------------------------------------------------------------------------------------------------------------")
            #     pos = ''
            #     bp = 0
            #     target_price = 0
            #     stop_loss = 0
            if put_his_df.iloc[x + 1, 3] <= stop_loss:
                sp = stop_loss
                profit_amount += (sp - bp) * quantity
                print(
                    "I PTime: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                        his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                print(
                    "----------------------------------------------------------------------------------------------------------------------------------------------------")
                pos = ''
                bp = 0
                target_price = 0
                stop_loss = 0
        if pos == 'PE':
            # target_price += bp * .005
            stop_loss = lowest_low('PE', x)
            print(f'Updated stop loss: {stop_loss}')
            # if put_his_df.iloc[x + 1, 2] >= target_price:
            #     sp = target_price
            #     profit_amount += (sp - bp) * quantity
            #     print(
            #         "J Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
            #             his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
            #     print(
            #         "----------------------------------------------------------------------------------------------------------------------------------------------------")
            #     pos = ''
            #     bp = 0
            #     target_price = 0
            #     stop_loss = 0
            if put_his_df.iloc[x + 1, 3] <= stop_loss:
                sp = stop_loss
                trades_list[x+1] = sp
                transaction_list.append('PE SELL')
                profit_amount += (sp - bp) * quantity
                print(
                    "K Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                        his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                print(
                    "----------------------------------------------------------------------------------------------------------------------------------------------------")
                pos = ''
                bp = 0
                target_price = 0
                stop_loss = 0
        if pos == 'CE':
            sp = call_his_df.iloc[x + 1, 1]
            profit_amount += (sp - bp) * quantity
            print(
                "L Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                    his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
            print(
                "----------------------------------------------------------------------------------------------------------------------------------------------------")
            bp = put_his_df.iloc[x + 1, 1]
            trades_list[x+1]=bp
            transaction_list.append('PE BUY')
            pos = 'PE'
            target_price = bp + (bp * .01)
            stop_loss = lowest_low('PE', x)
            print(f'PE - Time: {his_df.iloc[x, 0],}, Previous Double Pattern: {his_df.iloc[x - 1, 7]}')
            # if put_his_df.iloc[x + 1, 2] >= target_price:
            #     sp = target_price
            #     profit_amount += (sp - bp) * quantity
            #     print(
            #         "M Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
            #             his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
            #     print(
            #         "----------------------------------------------------------------------------------------------------------------------------------------------------")
            #     pos = ''
            #     bp = 0
            #     target_price = 0
            #     stop_loss = 0
            if put_his_df.iloc[x + 1, 3] <= stop_loss:
                sp = stop_loss
                profit_amount += (sp - bp) * quantity
                print(
                    "N Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                        his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                print(
                    "----------------------------------------------------------------------------------------------------------------------------------------------------")
                pos = ''
                bp = 0
                target_price = 0
                stop_loss = 0
    except Exception as e:
        traceback.print_exc(e)


def buy_action(x):
    global transaction_list, trades_list, average_candle_size, pos, target_price, profit_amount, quantity, bp, sp, loss_amount, stop_loss, CE_ins_tkn, positive_indications, negative_indications
    try:
        if pos == '':
            bp = call_his_df.iloc[x + 1, 1]
            trades_list[x+1] = bp
            transaction_list.append('CE BUY')
            pos = 'CE'
            target_price = bp + (bp * .01)
            stop_loss = lowest_low('CE', x)
            print(f'CE - Buying Price: {bp},Stop Loss: {stop_loss}')
            # if call_his_df.iloc[x + 1, 2] >= target_price:
            #     sp = target_price
            #     profit_amount += (sp - bp) * quantity
            #     print("A Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6], his_df.iloc[x, 0], bp, sp, (sp-bp)*quantity, profit_amount))
            #     print("----------------------------------------------------------------------------------------------------------------------------------------------------")
            #     pos = ''
            #     bp = 0
            #     target_price = 0
            #     stop_loss = 0
            if call_his_df.iloc[x + 1, 3] <= stop_loss:
                sp = stop_loss
                profit_amount += (sp - bp) * quantity
                print(
                    "B Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                        his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                print(
                    "----------------------------------------------------------------------------------------------------------------------------------------------------")
                pos = ''
                bp = 0
                target_price = 0
                stop_loss = 0
        if pos == 'CE':
            # target_price += bp*.01
            stop_loss = lowest_low('CE', x)
            print(f'Updated stop loss: {stop_loss}')
            # # if call_his_df.iloc[x + 1, 2] >= target_price:
            # #     sp = target_price
            # #     profit_amount += (sp - bp) * quantity
            # #     print(
            # #         "C Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
            # #             his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
            # #     print(
            # #         "----------------------------------------------------------------------------------------------------------------------------------------------------")
            # #     pos = ''
            # #     bp = 0
            # #     target_price = 0
            #     stop_loss = 0
            if call_his_df.iloc[x + 1, 3] <= stop_loss:
                sp = stop_loss
                trades_list[x+1]= sp
                transaction_list.append('CE SELL')
                profit_amount += (sp - bp) * quantity
                print(
                    "D Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                        his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                print(
                    "----------------------------------------------------------------------------------------------------------------------------------------------------")
                pos = ''
                bp = 0
                target_price = 0
                stop_loss = 0
        if pos == 'PE':
            sp = put_his_df.iloc[x + 1, 1]
            profit_amount += (sp - bp) * quantity
            print(
                "E Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                    his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
            print(
                "----------------------------------------------------------------------------------------------------------------------------------------------------")
            bp = call_his_df.iloc[x + 1, 1]
            trades_list[x+1]=bp
            transaction_list.append('CE BUY')
            pos = 'CE'
            target_price = bp + (bp * .005)
            stop_loss = lowest_low('CE', x)
            print(f'CE - Time: {his_df.iloc[x, 0],},Buying Price: {bp},Stop Loss: {stop_loss}')
            # if call_his_df.iloc[x + 1, 2] >= target_price:
            #     sp = target_price
            #     profit_amount += (sp - bp) * quantity
            #     print(
            #         "F Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
            #             his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
            #     print(
            #         "----------------------------------------------------------------------------------------------------------------------------------------------------")
            #     pos = ''
            #     bp = 0
            #     target_price = 0
            #     stop_loss = 0
            if call_his_df.iloc[x + 1, 3] <= stop_loss:
                sp = stop_loss
                profit_amount += (sp - bp) * quantity
                print(
                    "G Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                        his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                print(
                    "----------------------------------------------------------------------------------------------------------------------------------------------------")
                pos = ''
                bp = 0
                target_price = 0
                stop_loss = 0
    except Exception as e:
        traceback.print_exc(e)

'''
1
CE_condition = (nifty_ohlc_1[4] in positive_indications or nifty_ohlc_1[5] in positive_indications) and ((nifty_ohlc_1[2] < support) or (nifty_ohlc_1[2] < (support + average_candle_size)) or
    ((nifty_ohlc_2[2] < support) or (nifty_ohlc_2[2] < (support + average_candle_size)))) and nifty_ohlc[0] < nifty_ohlc[3]
PE_condition = ((resistance - support) > average_candle_size * 2) and((nifty_ohlc_1[4] in positive_indications or nifty_ohlc_1[5] in positive_indications) and ((nifty_ohlc_1[2] < support) or (nifty_ohlc_1[2] < (support + average_candle_size)) or
    ((nifty_ohlc_2[2] < support) or (nifty_ohlc_2[2] < (support + average_candle_size))))) and nifty_ohlc[0] < nifty_ohlc[3]:
2
CE Condition - (nifty_ohlc_1[8] == 'Up' and (nifty_ohlc[4] in positive_indications or nifty_ohlc[5] in positive_indications)) or (nifty_ohlc_1[8] == 'Down' and ((nifty_ohlc_1[4] in positive_indications or nifty_ohlc_1[5] in positive_indications) and (nifty_ohlc[4] in positive_indications or nifty_ohlc[5] in positive_indications)))
PE Condition - (nifty_ohlc_1[8] == 'Down' and (nifty_ohlc[4] in negative_indications or nifty_ohlc[5] in negative_indications)) or (nifty_ohlc_1[8] == 'Up' and ((nifty_ohlc_1[4] in negative_indications or nifty_ohlc_1[5] in negative_indications) and (nifty_ohlc[4] in negative_indications or nifty_ohlc[5] in negative_indications)))
'''


def call_buy_condition():
    if (nifty_ohlc_1[8] == 'Up' and (nifty_ohlc[4] in positive_indications or nifty_ohlc[5] in positive_indications)) or (nifty_ohlc_1[8] == 'Down' and ((nifty_ohlc_1[4] in positive_indications or nifty_ohlc_1[5] in positive_indications) and (nifty_ohlc[4] in positive_indications or nifty_ohlc[5] in positive_indications))):
        return True


def put_buy_condition():
    if(nifty_ohlc_1[8] == 'Down' and (nifty_ohlc[4] in negative_indications or nifty_ohlc[5] in negative_indications)) or (nifty_ohlc_1[8] == 'Up' and ((nifty_ohlc_1[4] in negative_indications or nifty_ohlc_1[5] in negative_indications) and (nifty_ohlc[4] in negative_indications or nifty_ohlc[5] in negative_indications))):
        return True


def single_min_backtesting():
    global support, resistance, average_candle_size, pos, target_price, profit_amount, quantity, bp, sp, loss_amount, stop_loss, CE_ins_tkn, positive_indications, negative_indications, his_df
    try:
        for x in range(len(his_df)):
            if his_df.iloc[x, 0] < datetime.time(15, 27, 00):
                get_nifty_onlc(his_df.iloc[x, 0], his_df.iloc[x, 1], his_df.iloc[x, 2], his_df.iloc[x, 3], his_df.iloc[x, 4])
                if (resistance and support) != 0:
                    if call_buy_condition():
                        print(f'CE occured at : {his_df.iloc[x, 0]}')
                        buy_action(x)
                    elif put_buy_condition():
                        print(f'PE occured at : {his_df.iloc[x, 0]}')
                        sell_action(x)
                    elif pos == 'CE':
                        # if call_his_df.iloc[x + 1, 2] >= target_price:
                        #     sp = target_price
                        #     profit_amount += (sp - bp) * quantity
                        #     print(
                        #         "O Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                        #             his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                        #     print(
                        #         "----------------------------------------------------------------------------------------------------------------------------------------------------")
                        #     pos = ''
                        #     bp = 0
                        #     target_price = 0
                        #     stop_loss = 0
                        if call_his_df.iloc[x + 1, 3] <= stop_loss:
                            sp = stop_loss
                            trades_list[x+1]=sp
                            transaction_list.append('CE SELL')
                            profit_amount += (sp - bp) * quantity
                            print(
                                "P Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                                    his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                    elif pos == 'PE':
                        # if put_his_df.iloc[x + 1, 2] >= target_price:
                        #     sp = target_price
                        #     profit_amount += (sp - bp) * quantity
                        #     print(
                        #         "Q Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                        #             his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                        #     print(
                        #         "----------------------------------------------------------------------------------------------------------------------------------------------------")
                        #     pos = ''
                        #     bp = 0
                        #     target_price = 0
                        #     stop_loss = 0
                        if put_his_df.iloc[x + 1, 3] <= stop_loss:
                            sp = stop_loss
                            trades_list[x+1] = sp
                            transaction_list.append('PE SELL')
                            profit_amount += (sp - bp) * quantity
                            print(
                                "R Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                                    his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
            elif his_df.iloc[x, 0] >= datetime.time(15, 27, 00):
                if pos == 'CE':
                    sp = call_his_df.iloc[x, 3]
                    trades_list[x-1] = sp
                    transaction_list.append('CE SELL')
                    profit_amount += (sp - bp) * quantity
                    print(
                        "P Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                            his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                    print(
                        "----------------------------------------------------------------------------------------------------------------------------------------------------")
                    pos = ''
                    bp = 0
                    target_price = 0
                    stop_loss = 0
                elif pos == 'PE':
                    sp = put_his_df.iloc[x, 3]
                    trades_list[x - 1] = sp
                    transaction_list.append('PE SELL')
                    profit_amount += (sp - bp) * quantity
                    print(
                        "R Time: {}, Buying Price: {}, Selling Price: {}, Stop Loss: {}, temp Profit: {}, Final Profit: {}".format(
                            his_df.iloc[x, 0], bp, sp, stop_loss, (sp - bp) * quantity, profit_amount))
                    print(
                        "----------------------------------------------------------------------------------------------------------------------------------------------------")
                    pos = ''
                    bp = 0
                    target_price = 0
                    stop_loss = 0
            low_high(his_df.iloc[x, 2], his_df.iloc[x, 3])
            if len(levels) >= 2:
                reisitance_and_support(nifty_ohlc[3])
        print(f'levels: {levels}')

    except Exception as e:
        traceback.print_exc(e)

# three_min_backtesting()


single_min_backtesting()

# print(sum(percentchange), no_of_success_trades, no_of_fail_trades)
print("profit amount is {}, and the loss amount is {}".format(profit_amount, loss_amount))
print(f'average candle size: {average_candle_size}')
plot_with_trades()