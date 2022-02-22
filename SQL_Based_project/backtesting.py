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
CE_symbol = ''
CE_ins_tkn = 0
PE_ins_tkn = 0
PE_symbol = ''
df = pd.read_csv('instruments_list')

historical_data = kite.historical_data(256265, '2022-02-21 09:15:00', '2022-02-21 15:30:00', '3minute')
# print(historical_data)
his_df = pd.DataFrame(historical_data)
# his_df.reset_index(drop=True, inplace=True)
his_df['Single_Candle_Pattern'] = "Pattern"


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
    global CE_symbol,CE_ins_tkn, PE_ins_tkn, PE_symbol
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

call_historical_data = kite.historical_data(CE_ins_tkn, '2022-02-21 09:15:00', '2022-02-21 15:30:00', '3minute')
call_his_df = pd.DataFrame(call_historical_data)
put_historical_data = kite.historical_data(PE_ins_tkn, '2022-02-21 09:15:00', '2022-02-21 15:30:00', '3minute')
put_his_df = pd.DataFrame(put_historical_data)

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

pos = ''
num = 0
percentchange = []
stop_loss = 0
no_of_success_trades = 0
no_of_fail_trades = 0
target_amount = 0
profit_amount = 0
streak = []

def backtesting():
    global pos, no_of_fail_trades, no_of_success_trades, target_amount, profit_amount, stop_loss

    for line in his_df.index:
        if pos == 'CE':
            if (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 2] >= (bp + target_amount):
                print("target reached")
                sp = bp + target_amount
                print("selling now at {} price during  {}".format(sp, his_df.at[line, "date"]))
                pc = (sp / bp - 1) * 100
                percentchange.append(pc)
                pos = ''
                no_of_success_trades += 1
                target_amount = 0
                profit_amount = profit_amount + (sp - bp)
                streak.append(1)
            elif (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 2] < (bp + target_amount) and his_df.at[line, "close"] > his_df.at[line, "open"]:
                print("CE continuation")
                # sp = (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 4]
                print("CE position continued & target updated")
                # pc = (sp / bp - 1) * 100
                # percentchange.append(pc)
                pos = 'CE'
                # no_of_fail_trades += 1
                # profit_amount = profit_amount + (sp - bp)
                # target_amount = target_amount + abs(sp-bp)
                target_amount = target_amount + ((call_his_df[call_his_df['date'] == his_df.at[line+1, "date"]]).iloc[0, 1] * 0.01)
            elif (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 2] < (bp + target_amount) and his_df.at[line, "close"] < his_df.at[line, "open"]:
                print("CE exit")
                sp = (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 4]
                print("CE position exited and target carry forwarded")
                # pc = (sp / bp - 1) * 100
                # percentchange.append(pc)
                pos = 'PE'
                # no_of_fail_trades += 1
                # profit_amount = profit_amount + (sp - bp)
                # target_amount = target_amount + abs(sp-bp)
                target_amount = target_amount + ((put_his_df[put_his_df['date'] == his_df.at[line+1, "date"]]).iloc[0, 1] * 0.01) + ((call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 1] - (call_his_df[call_his_df['date'] == his_df.at[line, "date"]]).iloc[0, 4])

        if pos == '':
            if his_df.at[line, "close"] > his_df.at[line, "open"]:
                # HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5]
                bp = (call_his_df[call_his_df['date'] == his_df.at[line+1, "date"]]).iloc[0, 1]
                pos = 'CE'
                print("buying now at price {}, during {}".format((call_his_df[call_his_df['date'] == his_df.at[line+1, "date"]]).iloc[0, 1], his_df.at[line, "date"]))
                # print("stop loss at {}".format(his_df.at[line, "low"]))
                # stop_loss = his_df.at[line, "low"]
                target_amount = target_amount + (bp*0.01)
                print("target amount is: {}".format(target_amount))

            if his_df.at[line, "open"] > his_df.at[line, "close"]:
                # HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 5]
                bp = (put_his_df[put_his_df['date'] == his_df.at[line+1, "date"]]).iloc[0, 1]
                pos = 'PE'
                print("buying now at price {}, during {}".format((put_his_df[call_his_df['date'] == his_df.at[line+1, "date"]]).iloc[0, 4], his_df.at[line, "date"]))
                # print("stop loss at {}".format(his_df.at[line, "low"]))
                # stop_loss = his_df.at[line, "low"]
                target_amount = target_amount + (bp*0.01)
                print("target amount is: {}".format(target_amount))


backtesting()

print(sum(percentchange), no_of_success_trades, no_of_fail_trades)
print("profit amount is {}".format(profit_amount))
