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
# print(opening_margin)
day_margin = opening_margin['equity']['available']['live_balance']
print(f"margin at the day start {day_margin}")

instrument_list = kite.instruments()
df = pd.DataFrame(instrument_list)
# print(df)
noted_time = ''

processed_orders = []
unprocessed_order_count = 0
trigger_thread_running = "NO"
positions = ''
position_order_no = 0
position_quantity = 0
position_stop_loss_ord_no = 0
stop_loss_status = ''
position_target_order_no = 0
position_buy_price = 0
target_price = 0
position_order_status = ''
options_to_trade = []
max_quantity = 1800
profit_amount = 0
loss_amount = 0
position_indicator = ''

CE_order_list = []
PE_order_list = []

CE_target_list = []
PE_target_list = []

CE_stop_loss_list = []
PE_stop_loss_list = []

positive_indications = ['Hammer', "Bullish Marubozu", "Dragonfly Doji", "Hanging Man Green"]
negative_indications = ['Shooting Star', "Bearish Marubozu", "Gravestone Doji", "Inverted Hammer Red"]

carry_forward = 0
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(
    columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])

positive_indications = ['Hammer', "Bullish Marubozu", "Dragonfly Doji", "Hanging Man Green"]
negative_indications = ['Shooting Star', "Bearish Marubozu", "Gravestone Doji", "Inverted Hammer Red"]
CE_symbol = ''
CE_ins_tkn = 0
PE_ins_tkn = 0
PE_symbol = ''
nifty_ohlc = [0, 0, 0, 0, "Pattern"]

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

def expiry_date():
    d = datetime.date.today()
    while d.weekday() != 3:
        d += datetime.timedelta(1)

    if d == datetime.date.today():
        d += datetime.timedelta(7)
    return d


def cancel_order(order_num):
    try:
        kite.cancel_order(order_num)
    except Exception as a:
        traceback.print_exc(a)


option_expiry_date = expiry_date()


def nifty_spot():
    nifty_ltp = (kite.ltp('NSE:NIFTY 50')).get('NSE:NIFTY 50').get('last_price')
    return round(nifty_ltp / 100) * 100


def options_list():
    global CE_symbol, CE_ins_tkn, PE_ins_tkn, PE_symbol
    closest_strike = nifty_spot()
    valid_options = df.loc[(df['segment'] == 'NFO-OPT') & (df['name'] == 'NIFTY') & (
                df['expiry'].astype(str) == str(option_expiry_date)) & (df['strike'] == closest_strike)]
    CE_ins_tkn = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 0]
    PE_ins_tkn = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 0]
    CE_symbol = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 2]
    PE_symbol = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 2]


nifty_spot()
options_list()


def quantity(option_type):
    try:
        temp_open_margin = kite.margins()
        temp_day_margin = temp_open_margin['equity']['available']['live_balance']
        options_list()
        if option_type == 'CE':
            actual_quantity = temp_day_margin/(kite.ltp("NFO:{}".format(CE_symbol))).get("NFO:{}".format(CE_symbol)).get('last_price')
            print("actual_quantity: {}".format(actual_quantity))
            tradeable_quantity = (round(actual_quantity/50) * 50) - 50
            print("tradeable_quantity: {}".format(tradeable_quantity))
            print(min(tradeable_quantity, max_quantity))
            return min(tradeable_quantity, max_quantity)
        elif option_type == 'PE':
            actual_quantity = temp_day_margin/(kite.ltp("NFO:{}".format(PE_symbol))).get("NFO:{}".format(PE_symbol)).get('last_price')
            print("actual_quantity: {}".format(actual_quantity))
            tradeable_quantity = (round(actual_quantity / 50) * 50) - 50
            print("tradeable_quantity: {}".format(tradeable_quantity))
            print(min(tradeable_quantity, max_quantity))
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
            order_status(orderid)
    except Exception as e:
        order_status(orderid)
        traceback.print_exc(e)


def target_order_status(orderid):
    try:
        details = kite.order_history(orderid)
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


def del_processed_order(order_number):
    my_cursor.execute("delete from order_updates where Order_number = {}".format(order_number))
    mydb.commit()


def get_previous_minute_details(direction):
    try:
        current_time = datetime.datetime.now()
        actual_time = current_time - datetime.timedelta(minutes=1)
        his_time = actual_time.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        if direction == 'CE':
            print(CE_ins_tkn)
            temp_historical_data = kite.historical_data(CE_ins_tkn,his_time,his_time,'minute')
            return temp_historical_data[0]['low']
        if direction == 'PE':
            print(PE_ins_tkn)
            temp_historical_data = kite.historical_data(PE_ins_tkn,his_time,his_time,'minute')
            return temp_historical_data[0]['low']
    except Exception as m:
        traceback.print_exc(m)


def process_orders():
    global position_order_no, position_stop_loss_ord_no, position_target_order_no, positions, position_buy_price, position_quantity, loss_amount, profit_amount, position_order_status
    try:
        my_cursor.execute("select * from order_updates limit 1")
        data = my_cursor.fetchone()
        mydb.commit()
        order_number = data[6]
        price = data[4]
        position_quantity = data[5]
        if order_number == position_order_no:
            position_buy_price = price
            del_processed_order(order_number)
        elif order_number == position_stop_loss_ord_no:
            position_stop_loss_ord_no = 0
            # cancel_order(position_target_order_no)
            # position_target_order_no = 0
            positions = ''
            position_order_status = ''
            temp_profit = (price - position_buy_price) * position_quantity
            profit_amount += temp_profit
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
        del_processed_order(order_number)
    except Exception as e:
        traceback.print_exc(e)

def options_trigger():
    global positions, position_order_no, position_order_status, position_quantity, position_stop_loss_ord_no, target_price, nifty_ohlc, loss_amount, trigger_thread_running, noted_time
    try:
        while ord_update_count() > 0:
            process_orders()
        if nifty_ohlc[4] in positive_indications:
            if positions == '':
                options_list()
                tradeable_quantity = quantity('CE')
                position_order_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                            tradingsymbol=CE_symbol, transaction_type=kite.TRANSACTION_TYPE_BUY,quantity=tradeable_quantity,
                                            order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_MIS)
                time.sleep(2)
                while position_order_status not in ('COMPLETE', 'REJETED'):
                    order_status(position_order_no)
                if position_order_status == "COMPLETE":
                    traded_symbol = CE_symbol
                    positions = 'CE'
                    print("Entry - Signal: {}, Quantity: {}, Instrument: {}".format(nifty_ohlc[4], position_quantity, traded_symbol))
                    print("Buy Price: {}".format(position_buy_price))
                    target_price = math.ceil((((abs(loss_amount)/tradeable_quantity) + (position_buy_price * 1.005))*10)/10)
                    # print(position_buy_price)
                    # position_target_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                    #                                      tradingsymbol=CE_symbol,
                    #                                      transaction_type=kite.TRANSACTION_TYPE_SELL,
                    #                                      quantity=position_quantity,
                    #                                      order_type=kite.ORDER_TYPE_LIMIT,
                    #                                      product=kite.PRODUCT_MIS, price=target_price)
                    # print("Placed target at a price of {} and order no - {}".format(target_price, position_target_ord_no))
                    stop_loss = get_previous_minute_details('CE')
                    print("Stop Loss: {}".format(stop_loss))
                    position_stop_loss_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                         tradingsymbol=traded_symbol,
                                                         transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                         quantity=position_quantity,
                                                         order_type=kite.ORDER_TYPE_SL,
                                                         product=kite.PRODUCT_MIS, price=stop_loss-0.05, trigger_price=stop_loss)
            elif positions == 'CE':
                target_price = math.ceil(((target_price+(position_buy_price * .005))*10)/10)
                # kite.modify_order(variety="regular", order_id=position_target_order_no,
                #                   price=target_price)
                stop_loss = get_previous_minute_details('CE')
                print("Stop Loss: {}".format(stop_loss))
                kite.modify_order(variety="regular", order_id=position_stop_loss_ord_no, price=stop_loss-0.05, trigger_price=stop_loss)
            elif positions == 'PE':
                kite.modify_order(variety="regular", order_id=position_stop_loss_ord_no,
                            order_type=kite.ORDER_TYPE_MARKET)
                time.sleep(2)
                while stop_loss_status not in ('COMPLETE', 'REJETED'):
                    stop_loss_order_status(position_stop_loss_ord_no)
                if ord_update_count() > 0:
                    process_orders()
                options_list()
                tradeable_quantity = quantity('CE')
                position_order_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                     tradingsymbol=CE_symbol,
                                                     transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                     quantity=tradeable_quantity,
                                                     order_type=kite.ORDER_TYPE_MARKET,
                                                     product=kite.PRODUCT_MIS)
                time.sleep(2)
                while position_order_status not in ('COMPLETE', 'REJETED'):
                    order_status(position_order_no)
                if position_order_status == "COMPLETE":
                    traded_symbol = CE_symbol
                    positions = 'CE'
                    print("Entry - Signal: {}, Quantity: {}, Instrument: {}".format(nifty_ohlc[4], position_quantity,
                                                                                    traded_symbol))
                    print("Buy Price: {}".format(position_buy_price))
                    # target_price = math.ceil(
                    #     (((abs(loss_amount) / tradeable_quantity) + (position_buy_price * 1.005)) * 10) / 10)
                    # position_target_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                    #                                           tradingsymbol=PE_symbol,
                    #                                           transaction_type=kite.TRANSACTION_TYPE_SELL,
                    #                                           quantity=position_quantity,
                    #                                           order_type=kite.ORDER_TYPE_LIMIT,
                    #                                           product=kite.PRODUCT_MIS, price=target_price)
                    # print("Placed target at a price of {} and order no - {}".format(target_price,
                    #                                                                 position_target_ord_no))
                    stop_loss = get_previous_minute_details('CE')
                    print("Stop Loss: {}".format(stop_loss))
                    position_stop_loss_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                                 tradingsymbol=traded_symbol,
                                                                 transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                 quantity=position_quantity,
                                                                 order_type=kite.ORDER_TYPE_SL,
                                                                 product=kite.PRODUCT_MIS, price=stop_loss-0.05, trigger_price=stop_loss)
        if nifty_ohlc[4] in negative_indications:
            if positions == '':
                options_list()
                tradeable_quantity = quantity('PE')
                position_order_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                            tradingsymbol=PE_symbol, transaction_type=kite.TRANSACTION_TYPE_BUY,quantity=tradeable_quantity,
                                            order_type=kite.ORDER_TYPE_MARKET, product=kite.PRODUCT_MIS)
                time.sleep(2)
                while position_order_status not in ('COMPLETE', 'REJETED'):
                    order_status(position_order_no)
                if position_order_status == "COMPLETE":
                    traded_symbol = PE_symbol
                    positions = 'PE'
                    print("Entry - Signal: {}, Quantity: {}, Instrument: {}".format(nifty_ohlc[4], position_quantity,
                                                                                    traded_symbol))
                    print("Buy Price: {}".format(position_buy_price))
                    target_price = math.ceil((((abs(loss_amount)/position_quantity) + (position_buy_price * 1.005))*10)/10)
                    # position_target_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                    #                                      tradingsymbol=PE_symbol,
                    #                                      transaction_type=kite.TRANSACTION_TYPE_SELL,
                    #                                      quantity=position_quantity,
                    #                                      order_type=kite.ORDER_TYPE_LIMIT,
                    #                                      product=kite.PRODUCT_MIS, price=target_price)
                    # print("Placed target at a price of {} and order no - {}".format(target_price, position_target_ord_no))
                    stop_loss = get_previous_minute_details('PE')
                    print("Stop Loss: {}".format(stop_loss))
                    position_stop_loss_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                         tradingsymbol=traded_symbol,
                                                         transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                         quantity=position_quantity,
                                                         order_type=kite.ORDER_TYPE_SL,
                                                         product=kite.PRODUCT_MIS, price=stop_loss-0.05, trigger_price=stop_loss)
            elif positions == 'PE':
                target_price = math.ceil(((target_price + (position_buy_price * .005))*10)/10)
                # kite.modify_order(variety="regular", order_id=position_target_order_no,
                #                   price=target_price)
                stop_loss = get_previous_minute_details('PE')
                print("Stop Loss: {}".format(stop_loss))
                kite.modify_order(variety="regular", order_id=position_stop_loss_ord_no,
                                  price=stop_loss - 0.05, trigger_price=stop_loss)
            elif positions == 'CE':
                kite.modify_order(variety="regular", order_id=position_stop_loss_ord_no,
                            order_type=kite.ORDER_TYPE_MARKET)
                time.sleep(2)
                while stop_loss_status not in ('COMPLETE', 'REJETED'):
                    stop_loss_order_status(position_stop_loss_ord_no)
                if ord_update_count() > 0:
                    process_orders()
                options_list()
                tradeable_quantity = quantity('PE')
                position_order_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                     tradingsymbol=PE_symbol,
                                                     transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                     quantity=tradeable_quantity,
                                                     order_type=kite.ORDER_TYPE_MARKET,
                                                     product=kite.PRODUCT_MIS)
                time.sleep(2)
                while position_order_status not in ('COMPLETE', 'REJETED'):
                    order_status(position_order_no)
                if position_order_status == "COMPLETE":
                    traded_symbol = PE_symbol
                    positions = 'PE'
                    print("Entry - Signal: {}, Quantity: {}, Instrument: {}".format(nifty_ohlc[4], position_quantity,
                                                                                    traded_symbol))
                    print("Buy Price: {}".format(position_buy_price))
                    target_price = math.ceil(
                        (((abs(loss_amount) / tradeable_quantity) + (position_buy_price * 1.005)) * 10) / 10)
                    # position_target_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                    #                                           tradingsymbol=CE_symbol,
                    #                                           transaction_type=kite.TRANSACTION_TYPE_SELL,
                    #                                           quantity=position_quantity,
                    #                                           order_type=kite.ORDER_TYPE_LIMIT,
                    #                                           product=kite.PRODUCT_MIS, price=target_price)
                    # print("Placed target at a price of {} and order no - {}".format(target_price,
                    #                                                                 position_target_ord_no))
                    stop_loss = get_previous_minute_details('PE')
                    position_stop_loss_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NFO,
                                                                 tradingsymbol=PE_symbol,
                                                                 transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                 quantity=position_quantity,
                                                                 order_type=kite.ORDER_TYPE_SL,
                                                                 product=kite.PRODUCT_MIS, price=stop_loss-0.05, trigger_price=stop_loss)

                    print("Stop Loss: {}".format(stop_loss))
        while noted_time == datetime.datetime.now().replace(second=0).strftime("%H:%M:%S"):
            if ord_update_count() > 0:
                process_orders()
                time.sleep(2)
            while stop_loss_status not in ('COMPLETE', 'REJETED'):
                latest_LTP = (kite.ltp('NFO:{}'.format(traded_symbol))).get('NFO:{}'.format(traded_symbol)).get('last_price')
                if latest_LTP > target_price:
                    stop_loss = latest_LTP
                    kite.modify_order(variety="regular", order_id=position_stop_loss_ord_no,
                                      price=stop_loss - 0.05, trigger_price=stop_loss)
        trigger_thread_running = "NO"
    except Exception as e:
        print(e)


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


def get_nifty_onlc():
    global nifty_ohlc
    try:
        current_time = datetime.datetime.now()
        actual_time = current_time - datetime.timedelta(minutes=1)
        from_to_date = actual_time.replace(second=0).strftime("%Y-%m-%d %H:%M:%S")
        temp_historical_data = kite.historical_data(256265, from_to_date, from_to_date, 'minute')
        nifty_ohlc[0] = temp_historical_data[0]['open']
        nifty_ohlc[1] = temp_historical_data[0]['high']
        nifty_ohlc[2] = temp_historical_data[0]['low']
        nifty_ohlc[3] = temp_historical_data[0]['close']
        nifty_ohlc[4] = single_candle_pattern(nifty_ohlc[0], nifty_ohlc[1], nifty_ohlc[2], nifty_ohlc[3])
        print("Nifty last minute - {} OHLC is Open: {}, High: {}, Low: {}, Close: {}, Pattern: {}".format(from_to_date,nifty_ohlc[0],nifty_ohlc[1],nifty_ohlc[2],nifty_ohlc[3],nifty_ohlc[4]))
    except Exception as r:
        traceback.print_exc(r)


def trade():  # retrieve continuous ticks in JSON format
    global trigger_thread_running, noted_time
    try:
        print()
        while datetime.datetime.now().time() < datetime.time(15, 30, 00):
            if datetime.time(9, 30, 00) < datetime.datetime.now().time() < datetime.time(15, 19, 00):
                if noted_time != datetime.datetime.now().replace(second=0).strftime("%H:%M:%S"):
                    noted_time = datetime.datetime.now().replace(second=0, microsecond=0).strftime("%H:%M:%S")
                    get_nifty_onlc()
                    if trigger_thread_running == "NO":
                        trigger_thread_running = "YES"
                        options_trigger()
                    # trigger_thread = threading.Thread(target=trigger)
                    # trigger_thread.start()
    except Exception as error:
        traceback.print_exc(error)


if __name__ == '__main__':
    try:
        trade()
    except Exception as e:
        traceback.print_exc(e)
