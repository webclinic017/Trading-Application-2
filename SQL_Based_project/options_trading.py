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

opening_margin = ds.kite.margins(segment=None)
# print(opening_margin)
day_margin = opening_margin['equity']['available']['live_balance']
print(f"margin at the day start {day_margin}")

instrument_list = kite.instruments()
df = pd.DataFrame(instrument_list)
print(df)

processed_orders = []
unprocessed_order_count = 0
trigger_thread_running = "NO"
positions = ''
position_order_no = 0
position_quantity = 0
position_stop_loss_ord_no = 0
position_order_status = ''
position_order_price = 0
options_to_trade = []
max_quantity = 1800

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


def cross_verify_orders():
    unprocessed_orders = []
    orders = ds.kite.orders()


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
    CE_symbol = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 2]
    PE_symbol = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 2]
    print(CE_ins_tkn, PE_ins_tkn, CE_symbol, PE_symbol)


nifty_spot()
options_list()
print("CE details {} {}".format(CE_ins_tkn, CE_symbol))
call_ltp = (kite.ltp('NFO:'+CE_symbol))
print(call_ltp)


# def circuit_limits():
#     with requests.session() as s:
#         url = "https://api.kite.trade/quote?i="
#         for entries in ds.trd_portfolio:
#             request_url = url + ds.trd_portfolio[entries]["Market"] + ":" + ds.trd_portfolio[entries]["Symbol"]
#             r = s.get(request_url, headers=headers)
#             result = json.loads(r.content)
#             ds.trd_portfolio[entries]['lower_circuit_limit'] = result['data'][ds.trd_portfolio[entries]["Market"] + ":" + ds.trd_portfolio[entries]["Symbol"]][
#                     'lower_circuit_limit']
#             ds.trd_portfolio[entries]['upper_circuit_limit'] = result['data'][ds.trd_portfolio[entries]["Market"] + ":" + ds.trd_portfolio[entries]["Symbol"]][
#                     'upper_circuit_limit']
#
#
# circuit_limits()


def quantity(option_type):
    try:
        temp_open_margin = kite.margins()
        temp_day_margin = temp_open_margin['equity']['available']['live_balance']
        options_list()
        if option_type == 'CE':
            actual_quantity = temp_day_margin/(kite.ltp("NFO:{}".format(CE_symbol))).get("NFO:{}".format(CE_symbol)).get('last_price')
            tradeable_quantity = round((actual_quantity/50) * 50) - 50
            return min(tradeable_quantity, max_quantity)
        elif option_type == 'PE':
            actual_quantity = temp_day_margin/(kite.ltp("NFO:{}".format(PE_symbol))).get("NFO:{}".format(PE_symbol)).get('last_price')
            tradeable_quantity = round((actual_quantity/50) * 50) - 50
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


def length_table(stock):
    my_cursor.execute("select count(*) from " + str(stock) + "_ohlc_final_1min")
    records = my_cursor.fetchall()
    mydb.commit()
    return records[0][17]


def sum_all_of_stocks():  # function to know the sum of all the stocks that are in place.
    my_cursor.execute("select sum(open) from rblbank_renko_final")
    total_quantity = my_cursor.fetchone()
    return total_quantity[0]


sum_of_quantity = sum_all_of_stocks()


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc(e)


def order_status(orderid):
    global position_order_status, position_order_price
    try:
        order_details = ds.kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                position_order_status = "COMPLETE"
                position_order_price = item['price']
            elif item['status'] == "REJECTED":
                position_order_status = "COMPLETE"
                break
        else:
            time.sleep(1)
            order_status(orderid)
    except Exception as e:
        order_status(orderid)
        traceback.print_exc(e)


def target_order_status(orderid):
    try:
        details = ds.kite.order_history(orderid)
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


def first_order():
    my_cursor.execute("select * from order_updates limit 1")
    data = my_cursor.fetchone()
    mydb.commit()
    return [data[0], data[1], data[2], data[3], data[4], data[5], data[6]]


def latest_row_ohlc(stock):
    my_cursor.execute("select * from " + str(stock) + "_ohlc_final_1min order by time DESC limit 1;")
    data = my_cursor.fetchall()
    mydb.commit()
    return [data[0][5], data[0][8], data[0][16]]


def latest_row_renko(stock):
    my_cursor.execute("select * from " + str(stock) + "_renko_final order by time DESC limit 1;")
    data = my_cursor.fetchall()
    mydb.commit()
    return [data[0][2], data[0][3], data[0][6]]


def del_processed_order():
    my_cursor.execute("delete from order_updates limit 1")
    mydb.commit()


def target():
    global carry_forward, profit_temp, profit_Final, profit
    try:
        while ord_update_count() > 0:
            print("order update count " + str(ord_update_count()))
            logging.info("order update count " + str(ord_update_count()))
            order_details = first_order()
            print("order details are: " + order_details[0], order_details[1], order_details[2], order_details[3], order_details[4], order_details[5], order_details[6])
            logging.info("order details are: " + order_details[0], order_details[1], order_details[2], order_details[3], order_details[4], order_details[5], order_details[6])
            price = order_details[4]
            volume = order_details[5]
            symbol = order_details[0]
            instrument_token = order_details[1]
            status = order_details[2]
            transacion_type = order_details[3]
            volume = volume * ds.trd_portfolio[instrument_token]['Quantity_multiplier']
            print("volume before starting calculation: " + str(volume))
            logging.info("volume before starting calculation: " + str(volume))
            if status == "COMPLETE":
                profit[instrument_token][0] = symbol
                if transacion_type == "BUY":
                    if profit[instrument_token][4] + volume == 0:
                        profit[instrument_token][1] = price
                        profit[instrument_token][4] = volume
                    else:
                        profit[instrument_token][1] = ((profit[instrument_token][1] * profit[instrument_token][4]) + (price * volume)) / (profit[instrument_token][4] + volume)
                        profit[instrument_token][4] = profit[instrument_token][4] + volume
                elif transacion_type == "SELL":
                    if profit[instrument_token][4] - volume == 0:
                        profit[instrument_token][2] = price
                        profit[instrument_token][4] = volume
                    else:
                        print(profit[instrument_token][2], profit[instrument_token][4], price, volume)
                        logging.info(profit[instrument_token][2], profit[instrument_token][4], price, volume)
                        profit[instrument_token][2] = ((profit[instrument_token][2] * profit[instrument_token][4]) + (price * volume)) / (profit[instrument_token][4] + volume)
                        profit[instrument_token][4] = profit[instrument_token][4] - volume
                print("profit dictionary after price and volume calculation" + str(profit[instrument_token]))
                logging.info("profit dictionary after price and volume calculation" + str(profit[instrument_token]))
                if (profit[instrument_token][1] != 0) & (profit[instrument_token][2] != 0):
                    buy_brokerage = min((profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['buy_brokerage']), 20)
                    sell_brokerage = min((profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['sell_brokerage']), 20)
                    stt_ctt = profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['stt_ctt']
                    buy_tran = profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['buy_tran']
                    sell_tran = profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['sell_tran']
                    gst = (buy_brokerage + sell_brokerage + buy_tran + sell_tran + stt_ctt) * ds.trd_portfolio[instrument_token][
                        'gst']
                    sebi_total = round((profit[instrument_token][1] + profit[instrument_token][2]) * volume * 0.000001, 0)
                    stamp_charges = profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['stamp']
                    profit[instrument_token][
                        5] = sebi_total + gst + sell_tran + buy_tran + buy_brokerage + sell_brokerage + stamp_charges
                    profit[instrument_token][3] = ((profit[instrument_token][2] - profit[instrument_token][1]) * volume) - profit[instrument_token][5]
                    profit[instrument_token][6] = profit[instrument_token][3] - profit[instrument_token][5]
                    profit_temp = pd.DataFrame([profit[instrument_token]],
                                               columns=["Symbol", "BUY Price", "SELL Price", "profit", "Volume", "Charges",
                                                        "final_profit"])
                    profit_Final = profit_Final.append(profit_temp)
                    profit_Final.drop_duplicates(keep='first', inplace=True)
                    print(str(carry_forward) + " - carry foward amount")
                    logging.info(str(carry_forward) + " - carry foward amount")
                    carry_forward = carry_forward + profit[instrument_token][6]
                    print(profit_Final.to_string())
                    logging.info(profit_Final.to_string())
                    print("Amount made till now: " + str(carry_forward))
                    logging.info("Amount made till now: " + str(carry_forward))
                    profit[instrument_token] = ["Symbol", 0, 0, "profit", 0, 0, 0]
                    print("the profit list after both buy and sell order update" + str(profit[instrument_token]))
                    logging.info("the profit list after both buy and sell order update" + str(profit[instrument_token]))
                for entries in ds.trd_portfolio:
                    if profit[entries][4] != 0:
                        traded_price = max(profit[entries][1], profit[entries][2])
                        traded_quantity = abs(profit[entries][4])
                        Brokerage = min(((traded_price * traded_quantity) * ds.trd_portfolio[entries]['buy_brokerage']) * 2, 40)
                        STT = (traded_price * traded_quantity) * ds.trd_portfolio[entries]['stt_ctt']
                        TNXChrgs = ((traded_price * traded_quantity) * 2) * ds.trd_portfolio[entries]['buy_tran']
                        GST = (Brokerage + TNXChrgs) * ds.trd_portfolio[entries]['gst']
                        SEBIChrgs = ((traded_price * 2) * traded_quantity) * 0.000001
                        StampDuty = ((traded_price * 2) * traded_quantity) * ds.trd_portfolio[entries]['stamp']
                        order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty + STT
                        print("trade price for calculation: " + str(traded_price), "traded quantity: " + str(traded_quantity), "Brokerage: " + str(Brokerage), "STT: " + str(STT), "TNXCharges: " + str(TNXChrgs), "GST: " + str(GST), "SEBI Charges: " + str(SEBIChrgs), "Stamp: " + str(StampDuty), "Order_Charges" + str(order_charges))
                        logging.info("trade price for calculation: " + str(traded_price), "traded quantity: " + str(traded_quantity), "Brokerage: " + str(Brokerage), "STT: " + str(STT), "TNXCharges: " + str(TNXChrgs), "GST: " + str(GST), "SEBI Charges: " + str(SEBIChrgs), "Stamp: " + str(StampDuty), "Order_Charges" + str(order_charges))
                        if carry_forward < 0:
                            target_amount = abs((order_charges * -2) + carry_forward) / traded_quantity
                            print("amount to gain in this trade when carry forward is negative" + str(target_amount))
                            logging.info("amount to gain in this trade when carry forward is negative" + str(target_amount))
                        else:
                            target_amount = abs(order_charges * 2) / abs(traded_quantity)
                            print("amount to gain in this trade when carry forward is positive " + str(target_amount))
                            logging.info("amount to gain in this trade when carry forward is positive " + str(target_amount))
                        if profit[entries][4] > 0:
                            ds.trd_portfolio[entries]['Target_amount'] = min(((traded_price + target_amount) - (
                                    (traded_price + target_amount) % ds.trd_portfolio[entries]['tick_size'])) + ds.trd_portfolio[entries]['tick_size'], ds.trd_portfolio[entries]['upper_circuit_limit'])
                            print(ds.trd_portfolio[entries]['Target_amount'])
                            logging.info(ds.trd_portfolio[entries]['Target_amount'])
                        elif profit[entries][4] < 0:
                            ds.trd_portfolio[entries]['Target_amount'] = max((traded_price - target_amount) - (
                                    (traded_price - target_amount) % ds.trd_portfolio[entries]['tick_size']), ds.trd_portfolio[entries]['lower_circuit_limit'])
                        print("final target price " + str(ds.trd_portfolio[entries]['Target_amount']))
                        logging.info("final target price " + str(ds.trd_portfolio[entries]['Target_amount']))
            print(profit[instrument_token])
            logging.info(profit[instrument_token])
            my_cursor.execute("insert into processed_orders values (" + str(order_details[6]) + ")")
            mydb.commit()
            del_processed_order()
        quantity()
    except Exception as e:
        traceback.print_exc(e)


def get_previous_minute_details(direction):
    temp_historical_min = int(datetime.datetime.now().strftime("%M"))-1
    his_time = datetime.datetime.today().replace(minute=temp_historical_min, second=0,microsecond=0)
    if direction == 'CE':
        temp_historical_data = kite.historical_data(CE_ins_tkn,his_time,his_time,'minute')
        return temp_historical_data[0]['low']
    if direction == 'PE':
        temp_historical_data = kite.historical_data(PE_ins_tkn,his_time,his_time,'minute')
        return temp_historical_data[0]['low']


def options_trigger():
    global positions, position_order_no, position_order_status, position_quantity, position_stop_loss_ord_no
    try:
        for token in ds.trd_portfolio:
            if length_table(ds.trd_portfolio[token]['Symbol']) >= 1:  # length of the Nifty 1_min final table
                # entry orders when quantity is 0
                ohlc_row = latest_row_ohlc(ds.trd_portfolio[token]['Symbol'])
                if ohlc_row[17] in positive_indications:
                    if positions == '':
                        options_list()
                        position_quantity = quantity('CE')
                        position_order_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE,
                                                    tradingsymbol=CE_symbol, transaction_type=ds.kite.TRANSACTION_TYPE_BUY,quantity=quantity('CE'),
                                                    order_type=ds.kite.ORDER_TYPE_MARKET, product=ds.kite.PRODUCT_MIS)
                        print("taken CE entry at {} at a price of ")
                        time.sleep(2)
                        while position_order_status not in ('COMPLETE', 'REJETED'):
                            order_status(position_order_no)
                        if position_order_status == "COMPLETE":
                            positions = 'CE'
                            target_price = math.ceil(((position_order_price * 1.005)*10)/10)
                            position_target_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE,
                                                                 tradingsymbol=CE_symbol,
                                                                 transaction_type=ds.kite.TRANSACTION_TYPE_BUY,
                                                                 quantity=position_quantity,
                                                                 order_type=ds.kite.ORDER_TYPE_LIMIT,
                                                                 product=ds.kite.PRODUCT_MIS, price=stop_loss)
                            print("Placed target at a price of {} and order no - {}".format(target_price, position_target_ord_no))
                            stop_loss = get_previous_minute_details('CE')
                            position_stop_loss_ord_no = kite.place_order(variety="regular", exchange=kite.EXCHANGE_NSE,
                                                                 tradingsymbol=CE_symbol,
                                                                 transaction_type=ds.kite.TRANSACTION_TYPE_BUY,
                                                                 quantity=position_quantity,
                                                                 order_type=ds.kite.ORDER_TYPE_LIMIT,
                                                                 product=ds.kite.PRODUCT_MIS, price=stop_loss)




    except Exception as e:
        print(e)


def trigger():
    global trigger_thread_running
    try:
        trigger_thread_running = "YES"
        for token in ds.trd_portfolio:
            if ds.trd_portfolio[token]['Trade'] == 'YES':
                if ord_update_count() > 0:
                    target()
                else:
                    if ((carry_forward / day_margin) * 100) <= 1:
                        if length_table(ds.trd_portfolio[token]['Symbol']) >= 1:  # length of the RENKO final table
                            ohlc_row = latest_row_ohlc(ds.trd_portfolio[token]['Symbol'])
                            renko_row = latest_row_renko(ds.trd_portfolio[token]['Symbol'])
                            # entry orders when quantity is 0
                            if profit[token][4] == 0:
                                if renko_row[2] != 0:
                                    if renko_row[1] == "SELL" and ds.trd_portfolio[token]['LTP'] < renko_row[0]:
                                        if ds.trd_portfolio[token]['Direction'] != "Down":
                                            if ds.trd_portfolio[token]['Tradable_quantity'] > 0:
                                                ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular", exchange=ds.trd_portfolio[token]['exchange'],
                                                    tradingsymbol=ds.trd_portfolio[token]['Symbol'], transaction_type=ds.kite.TRANSACTION_TYPE_SELL,quantity=ds.trd_portfolio[token]['Tradable_quantity'],
                                                    order_type=ds.kite.ORDER_TYPE_MARKET, product=ds.kite.PRODUCT_MIS)
                                                print(ds.trd_portfolio[token]['Orderid'])
                                                logging.info(ds.trd_portfolio[token]['Orderid'])
                                                time.sleep(2)
                                                quantity()
                                                order_status(token, ds.trd_portfolio[token]['Orderid'], 'SELL')
                                                target()
                                    elif renko_row[1] == "BUY" and ds.trd_portfolio[token]['LTP'] > renko_row[0]:
                                        if ds.trd_portfolio[token]['Direction'] != "Up":
                                            if ds.trd_portfolio[token]['Tradable_quantity'] > 0:
                                                ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular", exchange=ds.trd_portfolio[token]['exchange'],
                                                    tradingsymbol=ds.trd_portfolio[token]['Symbol'],transaction_type=ds.kite.TRANSACTION_TYPE_BUY,quantity=ds.trd_portfolio[token]['Tradable_quantity'],
                                                    order_type=ds.kite.ORDER_TYPE_MARKET, product=ds.kite.PRODUCT_MIS)
                                                print(ds.trd_portfolio[token]['Orderid'])
                                                logging.info(ds.trd_portfolio[token]['Orderid'])
                                                time.sleep(2)
                                                quantity()
                                                order_status(token, ds.trd_portfolio[token]['Orderid'], 'BUY')
                                                target()
                                # else:
                                #     print(str(ds.trd_portfolio[token]['Symbol']) + " - no condition met - Close: " + str(ohlc_row[0]) + ", SMA: " + str(ohlc_row[1]) + ", PSAR: " + str(ohlc_row[2]) + ", Renko: " + str(renko_row[0]))
                            # exit orders when quantity is not 0
                            elif profit[token][4] > 0 and renko_row[1] == "SELL":
                                print(profit[token][4])
                                ''' Below is a exit order when we do not have a target
                                ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular",
                                                                                         exchange=
                                                                                         ds.trd_portfolio[token][
                                                                                             'exchange'],
                                                                                         tradingsymbol=
                                                                                         ds.trd_portfolio[token][
                                                                                             'Symbol'],
                                                                                         transaction_type=ds.kite.TRANSACTION_TYPE_SELL,
                                                                                         quantity=
                                                                                         abs(profit[token][4]),
                                                                                         order_type=ds.kite.ORDER_TYPE_MARKET,
                                                                                         product=ds.kite.PRODUCT_MIS)
                                '''
                                # below lines for modifying an target order to exit position
                                ds.kite.modify_order(variety="regular", order_id=ds.trd_portfolio[token]['Target_order_id'], order_type=ds.kite.ORDER_TYPE_MARKET)
                                print(ds.trd_portfolio[token]['Orderid'])
                                logging.info(ds.trd_portfolio[token]['Orderid'])
                                time.sleep(2)
                                quantity()
                            elif profit[token][4] < 0 and renko_row[1] == "BUY":
                                print(profit[token][4])
                                ''' Below is a exit order when we do not have a target
                                ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular",
                                                                                         exchange=
                                                                                         ds.trd_portfolio[token][
                                                                                             'exchange'],
                                                                                         tradingsymbol=
                                                                                         ds.trd_portfolio[token][
                                                                                             'Symbol'],
                                                                                         transaction_type=ds.kite.TRANSACTION_TYPE_BUY,
                                                                                         quantity=
                                                                                         abs(profit[token][4]),
                                                                                         order_type=ds.kite.ORDER_TYPE_MARKET,
                                                                                         product=ds.kite.PRODUCT_MIS)
                                '''
                                # below lines for modifying an target order to exit position
                                ds.kite.modify_order(variety="regular", order_id=ds.trd_portfolio[token]['Target_order_id'], order_type=ds.kite.ORDER_TYPE_MARKET)
                                logging.info(ds.trd_portfolio[token]['Orderid'])
                                time.sleep(2)
                                quantity()

                            # Below ones are target orders
                            if profit[token][4] > 0 and ds.trd_portfolio[token]['Target_order'] != "YES":
                                time.sleep(2)
                                ds.trd_portfolio[token]['Target_order_id'] = ds.kite.place_order(variety="regular",
                                                                                           exchange=ds.trd_portfolio[token][
                                                                                               'exchange'],
                                                                                           tradingsymbol=ds.trd_portfolio[token][
                                                                                               'Symbol'],
                                                                                           transaction_type=ds.kite.TRANSACTION_TYPE_SELL,
                                                                                           quantity=max(abs(
                                                                                               ds.trd_portfolio[token]['Positions']), abs(profit[token][4])),
                                                                                           order_type=ds.kite.ORDER_TYPE_LIMIT,
                                                                                           price=round(
                                                                                               ds.trd_portfolio[token]['Target_amount'], 4), product=ds.kite.PRODUCT_MIS)
                                if target_order_status(ds.trd_portfolio[token]['Target_order_id']) == "OPEN":
                                    ds.trd_portfolio[token]['Target_order'] = "YES"
                                    quantity()
                                    time.sleep(2)
                            if profit[token][4] < 0 and ds.trd_portfolio[token]['Target_order'] != "YES":
                                time.sleep(2)
                                ds.trd_portfolio[token]['Target_order_id'] = ds.kite.place_order(variety="regular",
                                                                                           exchange=ds.trd_portfolio[token][
                                                                                               'exchange'],
                                                                                           tradingsymbol=ds.trd_portfolio[token][
                                                                                               'Symbol'],
                                                                                           transaction_type=ds.kite.TRANSACTION_TYPE_BUY,
                                                                                           quantity=max(abs(
                                                                                               ds.trd_portfolio[token]['Positions']), abs(profit[token][4])),
                                                                                           order_type=ds.kite.ORDER_TYPE_LIMIT,
                                                                                           price=round_down(
                                                                                               ds.trd_portfolio[token]['Target_amount'], 4),
                                                                                           product=ds.kite.PRODUCT_MIS)
                                if target_order_status(ds.trd_portfolio[token]['Target_order_id']) == "OPEN":
                                    ds.trd_portfolio[token]['Target_order'] = "YES"
                                    quantity()
                                    time.sleep(2)
                    else:
                        print("target acheived")
        trigger_thread_running = "NO"
    except (TypeError, exceptions.InputException, ReadTimeout, exceptions.NetworkException, AttributeError):
        traceback.print_exc()
        pass
    except Exception as e:
        traceback.print_exc(e)
        pass


def close_business():
    order_present = ds.kite.orders()
    for order in order_present:
        if order['status'] == 'OPEN':
            ds.kite.modify_order(variety="regular", order_id=order['order_id'], order_type=ds.kite.ORDER_TYPE_MARKET)
            time.sleep(1)


def on_ticks(ws, ticks):  # retrieve continuous ticks in JSON format
    global trigger_thread_running
    try:
        for company_data in ticks:
            ds.trd_portfolio[company_data['instrument_token']]['LTP'] = company_data['last_price']
        if datetime.time(9, 30, 00) < company_data['timestamp'].time() < datetime.time(15, 19, 00):
            if trigger_thread_running == "NO":
                trigger_thread_running = "YES"
                options_trigger()
                # trigger_thread = threading.Thread(target=trigger)
                # trigger_thread.start()
            if ((carry_forward / day_margin) * 100) >= 1:
                print("target reached")
                logging.info("target reached")
        # elif company_data['timestamp'].time() > datetime.time(15, 19, 00):
        #     close_business()
    except Exception as error:
        traceback.print_exc(error)


def on_connect(ws, response):
    ws.subscribe([x for x in ds.trd_portfolio])
    ws.set_mode(ws.MODE_FULL, [x for x in ds.trd_portfolio])


if __name__ == '__main__':
    try:
        kws.on_ticks = on_ticks
        kws.on_connect = on_connect
        kws.connect()
    except Exception as e:
        traceback.print_exc(e)