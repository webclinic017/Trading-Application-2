from kiteconnect import KiteTicker, KiteConnect
import pandas as pd
import backtrader as bt
import datetime
import os.path
import sys

acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()

historical_data = kite.historical_data(256265, '2022-01-01 09:15:00', '2022-02-02 15:15:00', '3minute')

# print(historical_data)
his_df = pd.DataFrame(historical_data)
# his_df.reset_index(drop=True, inplace=True)
his_df['Single_Candle_Pattern'] = "Pattern"

# print(his_df.to_string())

# method calculating the candle stick patterns
def single_candle_pattern(open, high, low, close):
    if close > open and open-low >= 2*(close-open) and (high == close or high-close < close-open):
        return "Hammer"
    elif open > close and high-open >= 2*(open-close) and (close == low or close-low < open-close):
        return "Shooting Start"
    elif (open == low or (open-low < .2 * close-open)) and open < close and (close == high or (high - close < (.2 * close - open))):
        return "Bullish Marubozu"
    elif (open == high or (high-open < .2 * open - close)) and open > close and (close == low or (close-low < (.2 * open - close))):
        return "Bearish Marubozu"
    else:
        return "None"
    pass


for row in his_df.index:
    # print(row[1]['open'])
    his_df.at[row, 'Single_Candle_Pattern'] = single_candle_pattern(his_df.at[row, 'open'], his_df.at[row, 'high'], his_df.at[row, 'low'], his_df.at[row, 'close'])

    # single_candle_pattern(row[1]['open'], row[1]['high'], row[1]['low'], row[1]['close'])

# his_df = his_df.set_index("date").sort_index()

pos = 0
num = 0
percentchange=[]
stop_loss = 0
no_of_success_trades = 0
no_of_fail_trades = 0
target_amount = 0

for line in his_df.index:

    if pos == 1:
        if his_df.at[line, "high"] >= (bp + target_amount):
            print("target reached")
            sp = bp + target_amount
            print("selling now at {} price during  {}".format(sp, his_df.at[line, "date"]))
            pc = (sp / bp - 1) * 100
            percentchange.append(pc)
            pos = 0
            no_of_success_trades += 1
        elif his_df.at[line, "low"] <= stop_loss:
            print("stop loss hit")
            sp = stop_loss
            print("selling now at {} price during  {}".format(stop_loss, his_df.at[line, "date"]))
            pc = (sp / bp - 1) * 100
            percentchange.append(pc)
            pos = 0
            no_of_fail_trades += 1

    if his_df.at[line, "Single_Candle_Pattern"] == "Hammer":
        # print("hammer occured")
        if pos == 0:
            bp = his_df.at[line, "close"]
            pos = 1
            print("buying now at {}, during {}".format(his_df.at[line, "close"], his_df.at[line, "date"]))
            print("stop loss at {}".format(his_df.at[line, "low"]))
            stop_loss = his_df.at[line, "low"]
            target_amount = 6 * (his_df.at[line, "open"] - his_df.at[line, "low"])
            print(target_amount)

print(sum(percentchange), no_of_success_trades, no_of_fail_trades)
