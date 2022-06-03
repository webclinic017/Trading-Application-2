import datetime
import socket
import threading
import traceback
import time
# from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions
from requests.exceptions import ReadTimeout
import math
import mysql.connector
import usdinr as ds
import pandas as pd
import requests
import json
from kiteconnect import KiteTicker, KiteConnect
import logging


acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="password123",
    database="testdb"
)
my_cursor = mydb.cursor()

opening_margin = kite.margins(segment=None)
print(opening_margin)
# print(opening_margin)
day_margin = opening_margin['equity']['available']['live_balance']
# day_margin = opening_margin['equity']['net']
print(f"margin at the day start {day_margin}")

date = datetime.datetime.today().date()

trade_time = datetime.time(9, 15, 00)
processed_time = datetime.datetime.combine(date, trade_time)
start_time = datetime.datetime.combine(date, trade_time)
duration = '3minute'

instrument_list = kite.instruments()
df = pd.DataFrame(instrument_list)
df.to_csv('instruments_list.csv')
# print(df)
noted_time = ''
from_to_date = ''
to_date = ''

processed_orders = []
unprocessed_order_count = 0
trigger_thread_running = "NO"
positions = ''
position_order_no = 0
position_quantity = 0
position_stop_loss_ord_no = 0
stop_loss_status = ''
position_target_order_status = ''
position_target_order_no = 0
position_buy_price = 0
target_price = 0
target_price_2 = 0
position_order_status = ''
options_to_trade = []
max_quantity = 1000
profit_amount = 0
loss_amount = 0
position_indicator = ''
traded_symbol = ''
stop_loss = 0
other_orders = []
toy = []
highs = []
lows = []
previous_high = None
current_high = None
current_high_loc = None
previous_low = None
current_low = None
current_low_loc = None

CE_order_list = []
PE_order_list = []

CE_target_list = []
PE_target_list = []

CE_stop_loss_list = []
PE_stop_loss_list = []

positive_indications = ['Hammer', "Bullish Marubozu", "Dragonfly Doji", "Hanging Man Green", "Tweezer Bottom", "Bullish Engulfing"]
negative_indications = ['Shooting Star', "Bearish Marubozu", "Gravestone Doji", "Inverted Hammer Red", "Tweezer Top", "Bearish Engulfing"]

carry_forward = 0
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(
    columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])


CE_symbol = ''
CE_ins_tkn = 0
PE_ins_tkn = 0
PE_symbol = ''
nifty_ohlc = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "3MA", "Trend"]
nifty_ohlc_1 = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "3MA", "Trend"]
nifty_ohlc_2 = [0, 0, 0, 0, "Pattern", "Two Candle Pattern", "Three Candle Pattern", "3MA", "Trend"]
nifty_ha_ohlc = [0, 0, 0, 0]
start_time = datetime.time(9, 15, 00)
# processed_time = datetime.time(9, 15, 00)

for x in ds.trd_portfolio:
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]  # ["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"]
    ds.trd_portfolio[x]['DB'] = mysql.connector.connect(host="127.0.0.1", user="root", passwd="password123",database="testdb")
    ds.trd_portfolio[x]['SQL'] = ds.trd_portfolio[x]['DB'].cursor()


def get_previous_close(items):
    my_cursor.execute("select Close from " + str(ds.trd_portfolio[items]['Symbol']) + "_ohlc_final_1min order by time DESC limit 1;")
    data = my_cursor.fetchall()
    mydb.commit()
    if len(data) == 0:
        return 0
    else:
        return float(data[0][0])


headers = {  # header for API request to update circuit limits
    'Authorization': 'token dysoztj41hntm1ma:' + ds.access_token
}

holiday_list = ['2022-04-14', '2022-04-15', '2022-05-03', '2022-04-14', '2022-05-16', '2022-08-09', '2022-08-15', '2022-08-16', '2022-08-31', '2022-10-05', '2022-10-24', '2022-10-26', '2022-11-08']


def expiry_date():
    global holiday_list
    d = datetime.date.today()
    while d.weekday() != 3:
        d += datetime.timedelta(1)

    if d == datetime.date.today():
        d += datetime.timedelta(7)
    for x in pd.to_datetime(holiday_list):
        if d == x.date():
            d = d - datetime.timedelta(1)
    return d


def cancel_order(order_num):
    try:
        kite.cancel_order(order_num)
    except Exception as a:
        traceback.print_exc(a)


option_expiry_date = expiry_date()


def nifty_spot():
    try:
        nifty_ltp = (kite.ltp('NSE:NIFTY 50')).get('NSE:NIFTY 50').get('last_price')
        return round(nifty_ltp / 100) * 100
    except Exception as g:
        traceback.print_exc(g)

def options_list():
    try:
        global CE_symbol, CE_ins_tkn, PE_ins_tkn, PE_symbol
        closest_strike = nifty_spot()
        valid_options = df.loc[(df['segment'] == 'NFO-OPT') & (df['name'] == 'NIFTY') & (
                    df['expiry'].astype(str) == str(option_expiry_date)) & (df['strike'] == closest_strike)]
        # print(valid_options.to_string())
        CE_ins_tkn = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 0]
        PE_ins_tkn = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 0]
        CE_symbol = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 2]
        PE_symbol = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 2]
    except Exception as f:
        traceback.print_exc(f)


nifty_spot()
options_list()


def quantity(option_type):
    try:
        temp_open_margin = kite.margins()
        temp_day_margin = temp_open_margin['equity']['available']['live_balance']
        # temp_day_margin = temp_open_margin['equity']['net']
        options_list()
        if option_type == 'CE':
            actual_quantity = temp_day_margin/(kite.ltp("NFO:{}".format(CE_symbol))).get("NFO:{}".format(CE_symbol)).get('last_price')
            tradeable_quantity = (round(actual_quantity/50) * 50) - 50
            return min(tradeable_quantity, max_quantity)
        elif option_type == 'PE':
            actual_quantity = temp_day_margin/(kite.ltp("NFO:{}".format(PE_symbol))).get("NFO:{}".format(PE_symbol)).get('last_price')
            tradeable_quantity = (round(actual_quantity / 50) * 50) - 50
            return min(tradeable_quantity, max_quantity)
    except (ReadTimeout, socket.timeout, TypeError, exceptions.InputException, exceptions.NetworkException, exceptions.NetworkException):
        traceback.print_exc()
        pass
    except Exception as e:
        traceback.print_exc(e)
        pass


def ord_update_count():
    my_cursor.execute("select count(*) from order_updates")
    records = my_cursor.fetchall()
    mydb.commit()
    return records[0][0]


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc(e)


def order_status(orderid):
    global position_order_status, position_buy_price, position_order_no, position_quantity, stop_loss_status
    try:
        order_details = kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                # print(item)
                position_order_status = "COMPLETE"
                stop_loss_status = ''
                position_buy_price = item['average_price']
                position_quantity = item['quantity']
                break
            elif item['status'] == "REJECTED":
                position_order_status = "REJECTED"
                stop_loss_status = ''
                break
        else:
            time.sleep(1)
            order_status(orderid)
    except Exception as e:
        order_status(orderid)
        traceback.print_exc(e)


def stop_loss_order_status(orderid):
    global position_order_status, position_buy_price, position_order_no, position_quantity, stop_loss_status
    try:
        order_details = kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                stop_loss_status = "COMPLETE"
                position_order_status = ''
                break
            elif item['status'] == "REJECTED":
                position_order_status = "REJECTED"
                position_order_status = ''
                break
        else:
            time.sleep(1)
    except Exception as e:
        traceback.print_exc(e)


def target_order_status(orderid):
    global position_target_order_status, position_order_status
    try:
        details = kite.order_history(orderid)
        for item in details:
            if item['status'] == "OPEN":
                position_target_order_status = "OPEN"
            elif item['status'] == "REJECTED":
                position_target_order_status = "REJECTED"
            elif item['status'] == "COMPLETE":
                position_target_order_status = "COMPLETE"
                position_order_status = ''
        else:
            time.sleep(1)
            target_order_status(orderid)
    except Exception as e:
        target_order_status(orderid)
        traceback.print_exc(e)


def del_processed_order(order_number):
    my_cursor.execute("delete from order_updates where Order_number = {}".format(order_number))
    mydb.commit()


def get_previous_minute_low(direction):
    global processed_time, duration, from_to_date, to_date
    try:
        # current_time = datetime.datetime.now()
        # actual_time = current_time - datetime.timedelta(minutes=1)
        # his_time = actual_time.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        if direction == 'CE':
            # print(CE_ins_tkn)
            temp_historical_data = kite.historical_data(CE_ins_tkn, from_to_date, to_date, duration)
            return temp_historical_data[0]['low']
        if direction == 'PE':
            # print(PE_ins_tkn)
            temp_historical_data = kite.historical_data(PE_ins_tkn, from_to_date, to_date, duration)
            return temp_historical_data[0]['low']
    except Exception as m:
        traceback.print_exc(m)

def get_previous_minute_close(direction):
    try:
        current_time = datetime.datetime.now()
        actual_time = current_time - datetime.timedelta(minutes=1)
        his_time = actual_time.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        if direction == 'CE':
            # print(CE_ins_tkn)
            temp_historical_data = kite.historical_data(CE_ins_tkn, from_to_date, to_date, duration)
            return temp_historical_data[0]['close']
        if direction == 'PE':
            # print(PE_ins_tkn)
            temp_historical_data = kite.historical_data(CE_ins_tkn, from_to_date, to_date, duration)
            return temp_historical_data[0]['close']
    except Exception as m:
        traceback.print_exc(m)


def get_previous_minute_open(direction):
    try:
        current_time = datetime.datetime.now()
        actual_time = current_time - datetime.timedelta(minutes=1)
        his_time = actual_time.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        if direction == 'CE':
            # print(CE_ins_tkn)
            temp_historical_data = kite.historical_data(CE_ins_tkn, from_to_date, to_date, duration)
            return temp_historical_data[0]['open']
        if direction == 'PE':
            # print(PE_ins_tkn)
            temp_historical_data = kite.historical_data(CE_ins_tkn, from_to_date, to_date, duration)
            return temp_historical_data[0]['open']
    except Exception as m:
        traceback.print_exc(m)


def process_orders():
    global other_orders, position_order_no, stop_loss_status, position_stop_loss_ord_no, position_target_order_no,position_target_order_status, positions, position_buy_price, position_quantity, loss_amount, profit_amount, position_order_status
    try:
        my_cursor.execute("select * from order_updates limit 1")
        data = my_cursor.fetchone()
        mydb.commit()
        # order_number = data[6]
        # price = data[4]
        position_quantity = data[5]
        if int(data[6]) == int(position_order_no):
            position_buy_price = data[4]
            del_processed_order(data[6])
            position_order_status = "COMPLETE"
        elif int(data[6]) == int(position_stop_loss_ord_no):
            position_target_order_no = 0

            del_processed_order(data[6])
            positions = ''
            stop_loss_status = "COMPLETE"
            temp_profit = (data[4] - position_buy_price) * position_quantity
            if loss_amount < 0 or temp_profit < 0:
                loss_amount += temp_profit
            profit_amount += temp_profit
            print("Sell Price: {}, Temp Profit: {}, Final Profit: {}".format(data[4], temp_profit, profit_amount))
            print("-----------------------------------------------------------------------------------------------")
        else:
            other_orders.append(data[6])
            del_processed_order(data[6])
        # elif order_number == position_target_order_no:
        #     cancel_order(position_stop_loss_ord_no)
        #     position_stop_loss_ord_no = 0
        #     position_target_order_no = 0
        #     positions = ''
        #     position_order_status = ''
        #     temp_profit = (price - position_buy_price) * position_quantity
        #     if loss_amount + temp_profit >= 0:
        #         profit_amount += loss_amount + temp_profit
        #     else:
        #         loss_amount += temp_profit

    except Exception as e:
        traceback.print_exc(e)


def lowest_low(direction):
    global processed_time, trigger_thread_running
    try:
        temp_low = all_time_low = get_previous_minute_low(direction)
        # print("temp_low: {}, all_time_low: {}".format(temp_low, all_time_low))
        prev_from_datetime = processed_time
        while all_time_low <= temp_low:
            temp_low = all_time_low
            prev_from_datetime = prev_from_datetime - datetime.timedelta(minutes=3)
            prev_to_datetime = prev_from_datetime
                               # + datetime.timedelta(minutes=3)
            if prev_from_datetime.time() < datetime.time(9, 18, 00):
                return all_time_low
            elif direction == 'CE':
                # print(CE_ins_tkn)
                lowest_historical_data = kite.historical_data(CE_ins_tkn, prev_from_datetime, prev_to_datetime, duration)
                # print(lowest_historical_data)
                all_time_low = lowest_historical_data[0]['low']

            elif direction == 'PE':
                # print(PE_ins_tkn)
                lowest_historical_data = kite.historical_data(PE_ins_tkn, prev_from_datetime, prev_to_datetime, duration)
                # print(lowest_historical_data)
                all_time_low = lowest_historical_data[0]['low']
            # print("temp_low: {}, all_time_low: {}".format(temp_low, all_time_low))
        return temp_low
    except exceptions.InputException as error:
        trigger_thread_running = "NO"
        trade()
    except Exception as e:
        trigger_thread_running = "NO"
        traceback.print_exc(e)


def fresh_trade(position_direction):
    global position_order_no, traded_symbol, positions, stop_loss, target_price, target_price_2, position_stop_loss_ord_no, trigger_thread_running
    try:
        options_list()
        if position_direction == 'CE':
            traded_symbol = CE_symbol
        else:
            traded_symbol = PE_symbol
        tradeable_quantity = quantity(position_direction)
        if tradeable_quantity > 0:
            position_order_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                 tradingsymbol=traded_symbol, transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                 quantity=tradeable_quantity,
                                                 order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_MIS)
            print(position_order_no)
            time.sleep(2)
            while position_order_status not in ('COMPLETE', 'REJETED'):
                order_status(position_order_no)
            if position_order_status == "COMPLETE":
                process_orders()
                positions = position_direction
                print(
                    "Entry - Signal: {}, Quantity: {}, Instrument: {}".format(nifty_ohlc[4], position_quantity, traded_symbol))
                print("Buy Price: {}".format(position_buy_price))
                stop_loss = lowest_low(position_direction)
                target_price = math.ceil((((position_buy_price * 1.01) + abs(loss_amount) / position_quantity) * 10) / 10)
                target_price_2 = math.ceil(position_buy_price+(2*(target_price-position_buy_price)))
                # target_price = min(
                #     math.ceil((((position_buy_price * 1.01) + abs(loss_amount) / position_quantity) * 10) / 10),
                #     math.ceil(position_buy_price + (position_buy_price - stop_loss)))
                # target_price_2 = max(
                #     math.ceil((((position_buy_price * 1.01) + abs(loss_amount) / position_quantity) * 10) / 10),
                #     math.ceil(position_buy_price + (position_buy_price - stop_loss)))
                # print(position_buy_price)
                # position_target_order_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                #                                      tradingsymbol=CE_symbol,
                #                                      transaction_type=kite.TRANSACTION_TYPE_SELL,
                #                                      quantity=position_quantity,
                #                                      order_type=kite.ORDER_TYPE_LIMIT,
                #                                      product=kite.PRODUCT_MIS, price=target_price)
                # print("Placed target at a price of {} and order no - {}".format(target_price, position_target_ord_no))
                print("Stop Loss: {}, Target: {},Target 2: {} target_ord_no: {}".format(stop_loss, target_price, target_price_2,
                                                                                        position_target_order_no))
                position_stop_loss_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                             tradingsymbol=traded_symbol,
                                                             transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                             quantity=position_quantity,
                                                             order_type=kite.ORDER_TYPE_SL,
                                                             product=kite.PRODUCT_MIS, price=stop_loss - 0.05,
                                                             trigger_price=stop_loss)
        else:
            print("not sufficient margin")
    except exceptions.InputException as error:
        trigger_thread_running = "NO"
        trade()
    except Exception as e:
        trigger_thread_running = "NO"
        traceback.print_exc(e)


def exit_positions():
    global position_stop_loss_ord_no, stop_loss_status
    try:
        kite.modify_order(variety="regular", order_id=position_stop_loss_ord_no,
                          order_type=kite.ORDER_TYPE_MARKET)
        time.sleep(2)
        while stop_loss_status not in ('COMPLETE', 'REJETED'):
            stop_loss_order_status(position_stop_loss_ord_no)
        if ord_update_count() > 0:
            process_orders()
    except Exception as c:
        traceback.print_exc(c)


def trend_continuation():
    global target_price, target_price_2, stop_loss, trigger_thread_running
    try:
        prev_close = get_previous_minute_close(positions)
        if prev_close > max(target_price, lowest_low(positions)):
            stop_loss = max(target_price, lowest_low(positions))
            kite.modify_order(variety="regular", order_id=position_stop_loss_ord_no, price=stop_loss - 0.05,
                              trigger_price=stop_loss)
            # target_price = min(math.ceil(((get_previous_minute_close(positions) * .01) * 10) / 10), math.ceil(
            #     get_previous_minute_close(positions) + (
            #             get_previous_minute_close(positions) - get_previous_minute_open(positions))))
            # target_price_2 = max(math.ceil(((get_previous_minute_close(positions) * .01) * 10) / 10), math.ceil(
            #     get_previous_minute_close(positions) + (
            #             get_previous_minute_close(positions) - get_previous_minute_open(positions))))
        # kite.modify_order(variety="regular", order_id=position_target_order_no,
        #                   price=target_price)
            print("Stop Loss: {}, Target: {}, Target 2: {}".format(stop_loss, target_price, target_price_2))
        # if ord_update_count() > 0:
        #     process_orders()
        # stop_loss_order_status(int(position_stop_loss_ord_no))
        # if stop_loss_status not in ('COMPLETE', 'REJETED'):
    except exceptions.InputException as error:
        trigger_thread_running = "NO"
        trade()
    except Exception as e:
        trigger_thread_running = "NO"
        traceback.print_exc(e)


def options_trigger():
    global positions, position_order_no, position_order_status, position_quantity, position_stop_loss_ord_no, target_price, nifty_ohlc, loss_amount, trigger_thread_running, noted_time, traded_symbol, stop_loss, position_target_order_no, position_target_order_status, nifty_ha_ohlc, target_price_2, nifty_ohlc_1
    try:
        while ord_update_count() > 0:
            process_orders()
        if (((nifty_ohlc_1[8] == "Down" or nifty_ohlc_1[8] == "Flat") and (nifty_ohlc[8] == "Down" or nifty_ohlc[8] == "Flat")) and ((nifty_ohlc_1[0] < nifty_ohlc_1[3]) and (nifty_ohlc[0] < nifty_ohlc[3])))\
                or (nifty_ohlc_1[4] in positive_indications and nifty_ohlc[4] in positive_indications):
            if positions == '':
                fresh_trade('CE')
            elif positions == 'CE':
                trend_continuation()
            elif positions == 'PE':
                exit_positions()
                fresh_trade('CE')
        elif (((nifty_ohlc_1[8] == "Up" or nifty_ohlc_1[8] == "Flat") and (nifty_ohlc[8] == "Up" or nifty_ohlc[8] == "Flat")) and ((nifty_ohlc_1[0] > nifty_ohlc_1[3]) and (nifty_ohlc[0] > nifty_ohlc[3])))\
                or (nifty_ohlc_1[4] in negative_indications and nifty_ohlc[4] in negative_indications):
            if positions == '':
                fresh_trade('PE')
            elif positions == 'PE':
                trend_continuation()
            elif positions == 'CE':
                exit_positions()
                fresh_trade('PE')
        elif positions != "" :
            trend_continuation()
        low_high()
        while noted_time == processed_time:
        #     if ord_update_count() > 0:
        #         process_orders()
        #     if positions != '':
        #         latest_LTP = (kite.ltp('NFO:{}'.format(traded_symbol))).get('NFO:{}'.format(traded_symbol)).get('last_price')
        #         # if latest_LTP > float(target_price):
        #         #     position_stop_loss_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
        #         #                                      tradingsymbol=traded_symbol,
        #         #                                      transaction_type=kite.TRANSACTION_TYPE_SELL,
        #         #                                      quantity=position_quantity,
        #         #                                      order_type=kite.ORDER_TYPE_MARKET,
        #         #                                      product=kite.PRODUCT_MIS)
        #         if latest_LTP <= stop_loss:
        #
        #             if position_target_order_status not in ('COMPLETE', 'REJETED'):
        #                 print("stop loss hit: {}".format(position_order_status))
        #                 kite.modify_order(variety="regular", order_id=position_target_order_no,
        #                                   order_type=kite.ORDER_TYPE_MARKET)
        #             time.sleep(2)
        #         if ord_update_count() > 0:
        #             process_orders()
            update_processed_time()
        trigger_thread_running = "NO"
    except exceptions.InputException as error:
        trigger_thread_running = "NO"
        trade()
    except Exception as e:
        trigger_thread_running = "NO"
        traceback.print_exc(e)


def close_business():
    order_present = kite.orders()
    for order in order_present:
        if order['status'] == 'OPEN':
            kite.modify_order(variety="regular", order_id=order['order_id'], order_type=kite.ORDER_TYPE_MARKET)
            time.sleep(1)


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


def get_nifty_onlc():
    global nifty_ohlc, nifty_ohlc_1, nifty_ohlc_2, processed_time, duration, nifty_ha_ohlc, from_to_date, to_date, highs, current_high, current_high_loc, previous_high, current_low, previous_low, current_low_loc, toy
    try:
        current_time = datetime.datetime.now()
        actual_time = current_time - datetime.timedelta(minutes=3)
        # from_to_date = actual_time.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        from_to_date = processed_time
        to_date = from_to_date + datetime.timedelta(minutes=3)
        temp_historical_data = kite.historical_data(256265, from_to_date, to_date, duration)
        nifty_ohlc_2 = nifty_ohlc_1
        nifty_ohlc_1 = nifty_ohlc
        toy = [temp_historical_data[0]['open'], temp_historical_data[0]['high'], temp_historical_data[0]['low'],
               temp_historical_data[0]['close'],
               single_candle_pattern(temp_historical_data[0]['open'], temp_historical_data[0]['high'],
                                     temp_historical_data[0]['low'], temp_historical_data[0]['close']),
               double_candle_pattern(temp_historical_data[0]['open'], temp_historical_data[0]['high'],
                                     temp_historical_data[0]['low'], temp_historical_data[0]['close'], nifty_ohlc[0], nifty_ohlc[1], nifty_ohlc[2],  nifty_ohlc[3]), 'Three Candle Pattern', '3MA', 'Trend']

        nifty_ohlc = toy
        if nifty_ohlc_2[3] != 0:
            nifty_ohlc[7] = (nifty_ohlc[3] + nifty_ohlc_1[3] + nifty_ohlc_2[3]) / 3
        if nifty_ohlc_2[7] != "3MA":
            if nifty_ohlc_2[7] > nifty_ohlc_1[7] > nifty_ohlc[7]:
                nifty_ohlc[8] = "Down"
            elif nifty_ohlc_2[7] < nifty_ohlc_1[7] < nifty_ohlc[7]:
                nifty_ohlc[8] = "Up"
            else:
                nifty_ohlc[8] = "Flat"
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
        print("Nifty last minute - {}, Close: {}, Pattern: {}, MA: {}, Trend: {}".format(from_to_date, nifty_ohlc[3], nifty_ohlc[4], nifty_ohlc[7], nifty_ohlc[8]))
    except Exception as r:
        traceback.print_exc(r)


def update_processed_time():
    global processed_time
    try:
        while processed_time < datetime.datetime.now():
            if processed_time + datetime.timedelta(minutes=6) > datetime.datetime.now():
                break
            else:
                processed_time = processed_time + datetime.timedelta(minutes=3)
    except Exception as e:
        traceback.print_exc(e)


def trade():  # retrieve continuous ticks in JSON format
    global trigger_thread_running, noted_time, processed_time
    try:
        update_processed_time()
        while datetime.datetime.now().time() < datetime.time(15, 30, 00):
            get_nifty_onlc()
            if ord_update_count() > 0:
                process_orders()
            if datetime.time(9, 18, 00) < datetime.datetime.now().time() < datetime.time(15, 26, 00) and profit_amount/day_margin < 1:
                # update_processed_time()
                if noted_time != processed_time:
                    noted_time = processed_time
                    if trigger_thread_running == "NO":
                        trigger_thread_running = "YES"
                        options_trigger()
            elif profit_amount/day_margin >= 1:
                print("target acheived")
                break
            while noted_time == processed_time:
                update_processed_time()

    except Exception as error:
        traceback.print_exc(error)


if __name__ == '__main__':
    try:
        trade()
    except Exception as e:
        traceback.print_exc(e)
