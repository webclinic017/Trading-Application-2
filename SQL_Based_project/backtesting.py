from kiteconnect import KiteTicker, KiteConnect
import pandas as pd
import backtrader as bt
import datetime
import traceback
import os.path
import sys
# import talib

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
quantity = 1000
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

positive_indications = ['Hammer', "Bullish Marubozu", "Dragonfly Doji", "Hanging Man Green", "Tweezer Bottom", "Bullish Engulfing"]
negative_indications = ['Shooting Star', "Bearish Marubozu", "Gravestone Doji", "Inverted Hammer Red", "Tweezer Top", "Bearish Engulfing"]

nifty_ohlc = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "MA", "Trend"]
nifty_ohlc_1 = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "2MA", "Trend"]
nifty_ohlc_2 = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "3MA", "Trend"]

from_date = '2022-06-02 09:15:00'
to_date = '2022-06-02 15:30:00'
duration = '3minute'
date = datetime.date(2022, 6, 2)

historical_data = kite.historical_data(256265, from_date, to_date, duration)
his_df = pd.DataFrame(historical_data)
his_df['date'] = his_df['date'].dt.time
his_df['Single_Candle_Pattern'] = "Pattern"
his_df['Double_Candle_Pattern'] = "Pattern"
his_df.to_csv("historical_data.csv")

def expiry_date():
    d = datetime.date.today()
    while d.weekday() != 3:
        d += datetime.timedelta(1)

    if d == datetime.date.today():
        d += datetime.timedelta(7)
    return d


option_expiry_date = expiry_date()
instrument_list = kite.instruments()
df = pd.DataFrame(instrument_list)

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
    if close1<open1 and abs(close1 - open1)/(high1 - low1)>=0.7 and close<open and 0.3>abs(close - open)/(high - low)>=0.1 and abs(low / low1 - 1)<0.05 and abs(close - open)<2*(min(close, open) - low):
        return "Tweezer Bottom"
    elif close1>open1 and abs(close1-open1)/(high1-low1)>=0.7 and close>open and 0.3>abs(close-open)/(high-low)>=0.1 and abs(high/high1-1)<0.05 and abs(close1-open1)<2*(high1-max(close1,open1)):
        return "Tweezer Top"
    elif close1<open1 and 0.3>abs(close1-open1)/(high1-low1)>=0.1 and close>open and abs(close-open)/(high-low)>=0.7 and high1<close and low1>open:
        return "Bullish Engulfing"
    elif close1>open1 and 0.3>abs(close1-open1)/(high1-low1)>=0.1 and close<open and abs(close-open)/(high-low)>=0.7 and high1<open and low1>close:
        return "Bearish Engulfing"
    else:
        return "None"


def low_high():
    global toy, current_low, current_high, current_low_loc, current_high_loc, previous_high, previous_low
    try:
        highs.append(toy[1])
        lows.append(toy[2])
        if previous_high is None:
            if current_high is None:
                current_high = toy[1]
                current_high_loc = len(highs)
            if current_high is not None and toy[1] > current_high:
                current_high = toy[1]
                current_high_loc = len(highs)
            elif current_high is not None and toy[1] < current_high and len(highs) - current_high_loc >= 4:
                previous_high = current_high
                current_high = 0
        elif previous_high is not None:
            if current_high == 0:
                if toy[1] >= max(highs[-3:]):
                    current_high = toy[1]
                    current_high_loc = len(highs)
            elif current_high != 0:
                if toy[1] >= current_high:
                    current_high = toy[1]
                    current_high_loc = len(highs)
                if len(highs[current_high_loc:]) == 3:
                    previous_high = current_high
                    current_high = 0

        if previous_low is None:
            if current_low is None:
                current_low = toy[2]
                current_low_loc = len(lows)
            if current_low is not None and toy[2] < current_low:
                current_low = toy[2]
                current_low_loc = len(lows)
            elif current_low is not None and toy[2] > current_low and len(lows) - current_low_loc >= 4:
                previous_low = current_low
                current_low = 0
        elif previous_low is not None:
            if current_low == 0:
                if toy[2] >= min(lows[-3:]):
                    current_low = toy[2]
                    current_low_loc = len(lows)
            elif current_low != 0:
                if toy[2] <= current_low:
                    current_low = toy[2]
                    current_low_loc = len(lows)
                if len(lows[current_low_loc:]) == 3:
                    previous_low = current_low
                    current_low = 0
        # print(highs, lows)
    except Exception as e:
        traceback.print_exc(e)


for row in range(len(his_df)):
    if row >= 2:
        his_df.iloc[row, 6] = single_candle_pattern(his_df.iloc[row, 1], his_df.iloc[row, 2], his_df.iloc[row, 3], his_df.iloc[row, 4])
        his_df.iloc[row, 7] = double_candle_pattern(his_df.iloc[row, 1], his_df.iloc[row, 2], his_df.iloc[row, 3],
                                                    his_df.iloc[row, 4], his_df.iloc[row-1, 1], his_df.iloc[row-1, 2], his_df.iloc[row-1, 3],
                                                    his_df.iloc[row-1, 4])
        nifty_ohlc_2 = nifty_ohlc_1
        nifty_ohlc_1 = nifty_ohlc
        toy = [his_df.iloc[row, 1], his_df.iloc[row, 2], his_df.iloc[row, 3], his_df.iloc[row, 4], single_candle_pattern(his_df.iloc[row, 1], his_df.iloc[row, 2], his_df.iloc[row, 3], his_df.iloc[row, 4]), double_candle_pattern(his_df.iloc[row, 1], his_df.iloc[row, 2], his_df.iloc[row, 3],
                                                    his_df.iloc[row, 4], his_df.iloc[row-1, 1], his_df.iloc[row-1, 2], his_df.iloc[row-1, 3],
                                                    his_df.iloc[row-1, 4]), 'Three Candle Pattern', 'MA', 'Trend']
        nifty_ohlc = toy
        # nifty_ohlc[0] = his_df.iloc[row, 1]
        # nifty_ohlc[1] = his_df.iloc[row, 2]
        # nifty_ohlc[2] = his_df.iloc[row, 3]
        # nifty_ohlc[3] = his_df.iloc[row, 4]
        # nifty_ohlc[4] = single_candle_pattern(nifty_ohlc[0], nifty_ohlc[1], nifty_ohlc[2], nifty_ohlc[3])
        if nifty_ohlc_2[3] != 0:
            nifty_ohlc[7] = (nifty_ohlc[3] + nifty_ohlc_1[3] + nifty_ohlc_2[3]) / 3
        if nifty_ohlc_2[7] != "3MA" and nifty_ohlc_2[7] != "2MA" and nifty_ohlc_2[7] != "MA":
            if nifty_ohlc_2[7] > nifty_ohlc_1[7] > nifty_ohlc[7]:
                nifty_ohlc[8] = "Down"
            elif nifty_ohlc_2[7] < nifty_ohlc_1[7] < nifty_ohlc[7]:
                nifty_ohlc[8] = "Up"
            else:
                nifty_ohlc[8] = "Flat"
        # print(nifty_ohlc_2)
        # print(nifty_ohlc_1)
        # print(nifty_ohlc)
        # print("__________________________")

        # single_candle_pattern(row[1]['open'], row[1]['high'], row[1]['low'], row[1]['close'])

# his_df = his_df.set_index("date").sort_index()





def three_min_backtesting():
    global pos, no_of_fail_trades, no_of_success_trades, target_price, profit_amount, stop_loss, loss_amount, quantity
    try:
        bp = 0
        for x in range(len(his_df)):
            if x < 124:
                if pos == 'CE':
                    if (put_his_df.iloc[x, 2] or call_his_df.iloc[x, 2]) >= (bp + target_price):
                        print("call target reached")
                        sp = bp + target_price
                        print("selling now at {} price during  {}".format(sp, his_df.iloc[x, 0]))
                        print("---------------------------------------------------------------------------------")
                        pc = (sp / bp - 1) * 100
                        percentchange.append(pc)
                        pos = ''
                        no_of_success_trades += 1
                        target_price = 0
                        profit_amount = profit_amount + ((sp - bp) * quantity)
                        streak.append(1)
                    elif call_his_df.iloc[x, 2] < (bp + target_price) and his_df.iloc[x, 4] > his_df.iloc[x, 1]:
                        # sp = (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 4]
                        print("CE position continued & target updated")
                        pos = 'CE'
                        if x < 124:
                            target_price = target_price + (call_his_df.iloc[x+1, 1] * 0.01)
                            print("updated target price is {}".format(target_price))
                        elif x >= 124:
                            sp = call_his_df.iloc[x, 4]
                            loss_amount = loss_amount + ((target_price - sp) * quantity)
                            no_of_fail_trades += 1
                            profit_amount = profit_amount + ((sp - bp) * quantity)
                        print("---------------------------------------------------------------------------------")
                    elif call_his_df.iloc[x, 2] < (bp + target_price) and his_df.iloc[x, 4] < his_df.iloc[x, 1]:
                        sp = call_his_df.iloc[x, 4]
                        profit_amount = profit_amount + ((sp - bp) * quantity)
                        loss_amount = loss_amount + ((target_price - sp) * quantity)
                        pos = 'PE'
                        no_of_fail_trades += 1

                        if x < 124:
                            bp = put_his_df.iloc[x+1, 1]
                            target_price = (bp*1.01) + (loss_amount/quantity)
                            print("CE position exited and loss carry forwarded, bought PE at {}, and target at {}".format(bp, target_price))
                        else:
                            print("End of day's trade")
                    print("---------------------------------------------------------------------------------")
                if pos == 'PE':
                    if (put_his_df.iloc[x, 2] or call_his_df.iloc[x, 2]) >= (bp + target_price):
                        print("put target reached")
                        sp = bp + target_price
                        print("selling now at {} price during  {}".format(sp, his_df.iloc[x, 0]))
                        print("---------------------------------------------------------------------------------")
                        pc = (sp / bp - 1) * 100
                        percentchange.append(pc)
                        pos = ''
                        no_of_success_trades += 1
                        target_price = 0
                        profit_amount = profit_amount + ((sp - bp) * quantity)
                        streak.append(1)
                    elif put_his_df.iloc[x, 2] < (bp + target_price) and his_df.iloc[x, 4] < his_df.iloc[x, 1]:
                        # sp = (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 4]
                        print("PE position continued & target updated")
                        pos = 'PE'
                        if x < 124:
                            target_price = target_price + (put_his_df.iloc[x+1, 1] * 0.01)
                            print("updated target price is {}".format(target_price))
                        elif x >= 124:
                            sp = put_his_df.iloc[x, 4]
                            print("PE exit at {}".format(sp))
                            profit_amount = profit_amount + ((sp - bp) * quantity)
                            loss_amount = loss_amount + ((target_price - sp) * quantity)
                            pos = 'CE'
                            no_of_fail_trades += 1
                        print("---------------------------------------------------------------------------------")
                    elif put_his_df.iloc[x, 2] < (bp + target_price) and his_df.iloc[x, 4] > his_df.iloc[x, 1]:
                        sp = put_his_df.iloc[x, 4]
                        print("PE exit at {}".format(sp))
                        loss_amount = loss_amount + ((target_price - sp) * quantity)
                        pos = 'CE'
                        no_of_fail_trades += 1
                        profit_amount = profit_amount + ((sp - bp) * quantity)
                        print(his_df.iloc[x, 0], datetime.time(hour=15, minute=28), his_df.iloc[x, 0], call_his_df.iloc[x, 1])
                        if x < 124:
                            bp = call_his_df.iloc[x+1, 1]
                            target_price = (bp * 1.01) + (loss_amount / quantity)
                            print("PE position exited and loss carry forwarded, bought CE at {}, and target at {}".format(bp,
                                                                                                                          target_price))
                        print("---------------------------------------------------------------------------------")

                if pos == '':
                    if his_df.iloc[x, 4] > his_df.iloc[x, 1]:
                        print(his_df.iloc[x, 0])
                        if his_df.iloc[x, 0] < datetime.time(hour=15, minute=28):
                            # HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5]
                            print(call_his_df.iloc[x+1, 0])
                            bp = call_his_df.iloc[x+1, 1]
                            pos = 'CE'
                            print("buying CE now at price {}, during {}".format(call_his_df.iloc[x, 1], his_df.iloc[x, 0]))
                            # print("stop loss at {}".format(his_df.at[line, "low"]))
                            # stop_loss = his_df.at[line, "low"]
                            target_price = target_price + (bp * 1.01)
                            print("target amount is: {}".format(target_price))

                            print("---------------------------------------------------------------------------------")

                    if his_df.iloc[x, 1] > his_df.iloc[x, 4]:
                        if his_df.iloc[x, 0] < datetime.time(hour=15, minute=28):
                            # HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5]
                            bp = put_his_df.iloc[x+1, 1]
                            pos = 'PE'
                            print("buying PE now at price {}, during {}".format((put_his_df.iloc[x+1, 1], his_df.iloc[x, 0])))
                            # print("stop loss at {}".format(his_df.at[line, "low"]))
                            # stop_loss = his_df.at[line, "low"]
                            print("target buy price {}".format((bp/100)))
                            target_price = target_price + (bp * 1.01)
                            print("target amount is: {}".format(target_price))
                            print("---------------------------------------------------------------------------------")

    except Exception as e:
        traceback.print_exc(e)


def lowest_low(token, time):
    temp_low = all_time_low = get_prev_low(token, time)
    current_timeframe = time
    while all_time_low <= temp_low:
        temp_low = all_time_low
        print(type(current_timeframe))
        current_timeframe = datetime.datetime.combine(date, current_timeframe) - datetime.timedelta(minutes=3)
        if current_timeframe.time() < datetime.time(9,18,00):
            return all_time_low
        else:
            all_time_low = get_prev_low(token, current_timeframe.time())
    return temp_low


def get_prev_low(token,from_to_date):
    combined_from_datetime = datetime.datetime.combine(date, from_to_date)
    # added_time = combined_from_datetime + datetime.timedelta(minutes=3)
    combined_to_datetime = combined_from_datetime + datetime.timedelta(minutes=3)
    temp_his_data = kite.historical_data(token, combined_from_datetime, combined_to_datetime, '3minute')
    return temp_his_data[0]['low']


def single_min_backtesting():
    global pos, target_price, profit_amount, quantity, bp, sp, loss_amount, stop_loss, CE_ins_tkn
    try:
        for x in range(len(his_df)):
            print(his_df.iloc[x,2], his_df.iloc[x,3])
            # low_high()
            if x <= len(his_df)-5 and his_df.iloc[x, 6] != "Pattern" and previous_low is not None and previous_high is not None:
                if his_df.iloc[x, 6] in positive_indications and ((his_df.iloc[x, 2] > previous_high) or (his_df.iloc[x, 2] > previous_low)) and ((his_df.iloc[x, 3] > previous_high) or (his_df.iloc[x, 3] > previous_low)):
                # if (his_df.iloc[x, 6] in positive_indications and his_df.iloc[x-1, 6] in positive_indications) or his_df.iloc[x, 7] in positive_indications:
                    print(f'CE - Time: {his_df.iloc[x, 0],}, Pattern: {his_df.iloc[x, 6]}, Double Pattern: {his_df.iloc[x, 7]}')
                    '''
                    if pos == '':
                        bp = call_his_df.iloc[x + 1, 1]
                        pos = 'CE'
                        target_price = bp + (bp * .01)
                        stop_loss = max(target_price, lowest_low(CE_ins_tkn, his_df.iloc[x, 0]))
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
                                "B Pattern: {},Double Candle Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6], his_df.iloc[x, 7],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                    if pos == 'CE':
                        # target_price += bp*.01
                        stop_loss = stop_loss = max(target_price, lowest_low(CE_ins_tkn, his_df.iloc[x, 0]))
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
                            profit_amount += (sp - bp) * quantity
                            print(
                                "D Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
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
                            "E Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                        print(
                            "----------------------------------------------------------------------------------------------------------------------------------------------------")
                        bp = call_his_df.iloc[x + 1, 1]
                        pos = 'CE'
                        target_price = bp + (bp * .005)
                        stop_loss = stop_loss = max(target_price, lowest_low(CE_ins_tkn, his_df.iloc[x, 0]))
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
                                "G Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                            '''
                elif his_df.iloc[x, 6] in negative_indications and ((his_df.iloc[x, 2] > previous_high) or (his_df.iloc[x, 2] > previous_low)) and ((his_df.iloc[x, 3] > previous_high) or (his_df.iloc[x, 3] > previous_low)):
                # elif (his_df.iloc[x, 6] in negative_indications and his_df.iloc[x-1, 6] in negative_indications) or his_df.iloc[x, 7] in negative_indications:
                    print(f'PE - Time: {his_df.iloc[x, 0],}, Pattern: {his_df.iloc[x, 6]}, Double Pattern: {his_df.iloc[x, 7]}')
                    '''
                    if pos == '':
                        bp = put_his_df.iloc[x + 1, 1]
                        pos = 'PE'
                        target_price = bp + (bp * .005)
                        stop_loss = max(target_price, lowest_low(PE_ins_tkn, his_df.iloc[x, 0]))
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
                                "I Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                    if pos == 'PE':
                        # target_price += bp * .005
                        stop_loss = stop_loss = max(target_price, lowest_low(PE_ins_tkn, his_df.iloc[x, 0]))
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
                            profit_amount += (sp - bp) * quantity
                            print(
                                "K Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
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
                            "L Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                        print(
                            "----------------------------------------------------------------------------------------------------------------------------------------------------")
                        bp = put_his_df.iloc[x + 1, 1]
                        pos = 'PE'
                        target_price = bp + (bp * .01)
                        stop_loss = max(target_price, lowest_low(PE_ins_tkn, his_df.iloc[x, 0]))
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
                                "N Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                else:
                    if pos == 'CE':
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
                            profit_amount += (sp - bp) * quantity
                            print(
                                "P Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                    if pos == 'PE':
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
                            profit_amount += (sp - bp) * quantity
                            print(
                                "R Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                            '''

    except Exception as e:
        traceback.print_exc(e)

# three_min_backtesting()


single_min_backtesting()

print(sum(percentchange), no_of_success_trades, no_of_fail_trades)
print("profit amount is {}, and the loss amount is {}".format(profit_amount, loss_amount))
