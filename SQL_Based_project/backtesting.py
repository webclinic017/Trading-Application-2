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
df = pd.read_csv('instruments_list')
positive_indications = ['Hammer', "Bullish Marubozu", "Dragonfly Doji", "Hanging Man Green"]
negative_indications = ['Shooting Star', "Bearish Marubozu", "Gravestone Doji", "Inverted Hammer Red"]

from_date = '2022-03-17 09:15:00'
to_date = '2022-03-17 15:30:00'
date = datetime.date(2022, 3, 17)

historical_data = kite.historical_data(256265, from_date, to_date, '5minute')
his_df = pd.DataFrame(historical_data)
print(his_df)
his_df['date'] = his_df['date'].dt.time
his_df['Single_Candle_Pattern'] = "Pattern"
his_df.to_csv("historical_data.csv")

def expiry_date():
    d = datetime.date.today()
    while d.weekday() != 3:
        d += datetime.timedelta(1)

    if d == datetime.date.today():
        d += datetime.timedelta(7)
    return d


option_expiry_date = expiry_date()


def nifty_spot():
    nifty_ltp = (kite.ltp('NSE:NIFTY 50')).get('NSE:NIFTY 50').get('last_price')
    return round(nifty_ltp / 100) * 100

def options_list():
    global CE_symbol, CE_ins_tkn, PE_ins_tkn, PE_symbol
    closest_strike = nifty_spot()
    valid_options = df.loc[(df['segment'] == 'NFO-OPT') & (df['name'] == 'NIFTY') & (
                df['expiry'].astype(str) == str(option_expiry_date)) & (df['strike'] == closest_strike)]
    print(valid_options.to_string())
    CE_ins_tkn = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 1]
    PE_ins_tkn = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 1]
    CE_symbol = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 3]
    PE_symbol = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 3]
    print(CE_ins_tkn, PE_ins_tkn, CE_symbol, PE_symbol)


nifty_spot()
options_list()

call_historical_data = kite.historical_data(CE_ins_tkn, from_date, to_date, 'minute')
call_his_df = pd.DataFrame(call_historical_data)
call_his_df['date'] = call_his_df['date'].dt.time
call_his_df.to_csv("call_his_df.csv")
put_historical_data = kite.historical_data(PE_ins_tkn, from_date, to_date, 'minute')
put_his_df = pd.DataFrame(put_historical_data)
put_his_df['date'] = put_his_df['date'].dt.time
put_his_df.to_csv("put_his_df.csv")
nifty_historical_data = kite.historical_data(256265, from_date, to_date, 'minute')
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


for row in range(len(his_df)):
    his_df.iloc[row, 6] = single_candle_pattern(his_df.iloc[row, 1], his_df.iloc[row, 2], his_df.iloc[row, 3], his_df.iloc[row, 4])

    # single_candle_pattern(row[1]['open'], row[1]['high'], row[1]['low'], row[1]['close'])

# his_df = his_df.set_index("date").sort_index()

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


def get_prev_low(token,from_to_date):
    combined_datetime = datetime.datetime.combine(date, from_to_date)
    temp_his_data = kite.historical_data(token, combined_datetime, combined_datetime, 'minute')
    return temp_his_data[0]['low']


def single_min_backtesting():
    global pos, target_price, profit_amount, quantity, bp, sp, loss_amount, stop_loss
    try:
        for x in range(len(his_df)):
            if x <= len(his_df)-5:
                if his_df.iloc[x, 6] in positive_indications:
                    if pos == '':
                        bp = call_his_df.iloc[x + 1, 1]
                        pos = 'CE'
                        target_price = bp + (bp * .005)
                        stop_loss = get_prev_low(CE_ins_tkn, his_df.iloc[x, 0])
                        if call_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print("A Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6], his_df.iloc[x, 0], bp, sp, (sp-bp)*quantity, profit_amount))
                            print("----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif call_his_df.iloc[x + 1, 3] <= stop_loss:
                            sp = stop_loss
                            profit_amount += (sp - bp) * quantity
                            print(
                                "B Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                    if pos == 'CE':
                        target_price += bp*.01
                        stop_loss = get_prev_low(CE_ins_tkn, his_df.iloc[x, 0])
                        if call_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print(
                                "C Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif call_his_df.iloc[x + 1, 3] <= stop_loss:
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
                        stop_loss = get_prev_low(CE_ins_tkn, his_df.iloc[x, 0])
                        if call_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print(
                                "F Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif call_his_df.iloc[x + 1, 3] <= stop_loss:
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
                elif his_df.iloc[x, 6] in negative_indications:
                    if pos == '':
                        bp = put_his_df.iloc[x + 1, 1]
                        pos = 'PE'
                        target_price = bp + (bp * .005)
                        stop_loss = get_prev_low(PE_ins_tkn, his_df.iloc[x, 0])
                        if put_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print(
                                "H Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif put_his_df.iloc[x + 1, 3] <= stop_loss:
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
                        target_price += bp * .005
                        stop_loss = get_prev_low(PE_ins_tkn, his_df.iloc[x, 0])
                        if put_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print(
                                "J Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif put_his_df.iloc[x + 1, 3] <= stop_loss:
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
                        target_price = bp + (bp * .005)
                        stop_loss = get_prev_low(PE_ins_tkn, his_df.iloc[x, 0])
                        if put_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print(
                                "M Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif put_his_df.iloc[x + 1, 3] <= stop_loss:
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
                        if call_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print(
                                "O Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif call_his_df.iloc[x + 1, 3] <= stop_loss:
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
                        if put_his_df.iloc[x + 1, 2] >= target_price:
                            sp = target_price
                            profit_amount += (sp - bp) * quantity
                            print(
                                "Q Pattern: {}, Time: {}, Buying Price: {}, Selling Price: {}, temp Profit: {}, Final Profit: {}".format(his_df.iloc[x, 6],
                                    his_df.iloc[x, 0], bp, sp, (sp - bp) * quantity, profit_amount))
                            print(
                                "----------------------------------------------------------------------------------------------------------------------------------------------------")
                            pos = ''
                            bp = 0
                            target_price = 0
                            stop_loss = 0
                        elif put_his_df.iloc[x + 1, 3] <= stop_loss:
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
    except Exception as e:
        traceback.print_exc(e)

# three_min_backtesting()


single_min_backtesting()

print(sum(percentchange), no_of_success_trades, no_of_fail_trades)
print("profit amount is {}, and the loss amount is {}".format(profit_amount, loss_amount))
