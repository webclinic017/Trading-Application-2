import socket
import traceback
import time
from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions
# from kiteconnect.exceptions import DataException
from requests.exceptions import ReadTimeout
import math
import mysql.connector
import usdinr as ds
import pandas as pd

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="password123",
    database="testdb"
)
my_cursor = mydb.cursor()

opening_margin = ds.kite.margins(segment=None)
# print(opening_margin)
day_margin = opening_margin['equity']['net']


carry_forward = 0
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(
    columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])

for x in ds.trd_portfolio:
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]  # ["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"]


def get_previous_close(items):
    my_cursor.execute("select Close from " + str(ds.trd_portfolio[items]['Symbol']) + "_renko_final order by time DESC limit 1;")
    data = my_cursor.fetchall()
    return float(data[0][0])


def quantity():
    try:
        temp_open_margin = ds.KiteConnect.margins(ds.kite)
        temp_day_margin = temp_open_margin['equity']['net']
        for items in ds.trd_portfolio:
            if ds.trd_portfolio[items]['Segment'] == "Options":  # calculating quantity for options
                maxquantity = min(temp_day_margin / ds.trd_portfolio[items]['LTP'], ds.trd_portfolio[items]['max_quantity'])
                multiplier = 0
                while (multiplier * 75) < maxquantity:  # ds.trd_portfolio[items]['max_quantity']:
                    multiplier = multiplier + 1
                else:
                    ds.trd_portfolio[items]['Tradable_quantity'] = (multiplier - 1) * 75
            elif ds.trd_portfolio[items]['Segment'] != "Options":  # calculating quantity for equities
                previous_close = get_previous_close(items)
                if previous_close != 0:
                    if ((temp_day_margin * ds.trd_portfolio[items]['margin_multiplier']) / (previous_close * ds.trd_portfolio[items]['Quantity_multiplier'])) - ds.trd_portfolio[items]['buffer_quantity'] < 1:
                        ds.trd_portfolio[items]['Tradable_quantity'] = 0
                        print("a")
                    else:
                        ds.trd_portfolio[items]['Tradable_quantity'] = int(round(min(((day_margin * ds.trd_portfolio[items]['margin_multiplier']) / (previous_close * ds.trd_portfolio[items][
                            'Quantity_multiplier'])) - ds.trd_portfolio[items]['buffer_quantity'],
                                                                                  ds.trd_portfolio[items]['max_quantity']), 0))
                        print("b", ds.trd_portfolio[items]['Tradable_quantity'])
            my_cursor.execute("update trd_portfolio set Tradable_quantity = " + str(ds.trd_portfolio[items]['Tradable_quantity']) + " where token = " + str(items))
            mydb.commit()
    except ReadTimeout:
        traceback.print_exc()
        print("positions read timeout exception")
        trigger_thread_running = "NO"
        pass
    except socket.timeout:
        traceback.print_exc()
        print("positions socket timeout exception")
        trigger_thread_running = "NO"
        pass
    except TypeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.InputException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.NetworkException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except Exception as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass
    except WantReadError as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass


def ord_update_count():
    my_cursor.execute("select count(*) from order_updates")
    records = my_cursor.fetchall()
    mydb.commit()
    return records[0][0]


def length_table(stock):
    my_cursor.execute("select count(*) from " + str(stock) + "_renko_final")
    records = my_cursor.fetchall()
    mydb.commit()
    return records[0][0]


def sum_all_of_stocks(): # function to know the sum of all the stocks that are in place.
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


def order_status(token, orderid, trade_type):
    try:
        order_details = ds.kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                if trade_type == 'SELL':
                    ds.trd_portfolio[token]['Direction'] = "Down"
                    ds.trd_portfolio[token]['Target_order'] = "NO"
                    print(ds.trd_portfolio[token]['Direction'])
                    break
                elif trade_type == 'BUY':
                    ds.trd_portfolio[token]['Direction'] = "Up"
                    ds.trd_portfolio[token]['Target_order'] = "NO"
                    print(ds.trd_portfolio[token]['Direction'])
                    break
            elif item['status'] == "REJECTED":
                print("order got rejected", ds.trd_portfolio[token]['Direction'], ds.trd_portfolio[token]['Target_order'])
                break
        else:
            time.sleep(1)
            order_status(token, orderid, type)
    except Exception as e:
        order_status(token, orderid, type)
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
    return [data[0], data[1], data[2], data[3], data[4], data[5]]


def latest_row(stock):
    my_cursor.execute("select * from " + str(stock) + "_renko_final order by time DESC limit 1;")
    data = my_cursor.fetchone()
    mydb.commit()
    return [data[2], data[3], data[5]]


def del_processed_order():
    my_cursor.execute("delete from order_updates limit 1")
    mydb.commit()


def target():
    global carry_forward, profit_temp, profit_Final, profit
    try:
        while ord_update_count() > 0:
            print("order update count " + str(ord_update_count()))
            order_details = first_order()
            print("order details are: " + order_details[0], order_details[1], order_details[2], order_details[3], order_details[4], order_details[5])
            price = order_details[4]
            volume = order_details[5]
            symbol = order_details[0]
            instrument_token = order_details[1]
            status = order_details[2]
            transacion_type = order_details[3]
            volume = volume * ds.trd_portfolio[instrument_token]['Quantity_multiplier']
            print("volume before starting calculation" + str(volume))
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
                        profit[instrument_token][2] = ((profit[instrument_token][2] * profit[instrument_token][4]) + (price * volume)) / (profit[instrument_token][4] + volume)
                        profit[instrument_token][4] = profit[instrument_token][4] - volume
                print("profit dictionary after price and volume calculation" + str(profit[instrument_token]))
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
                    carry_forward = carry_forward + profit[instrument_token][6]
                    print(profit_Final.to_string())
                    print("Amount made till now: " + str(carry_forward))
                    profit[instrument_token] = ["Symbol", 0, 0, "profit", 0, 0, 0]
                    print("the profit list after both buy and sell order update" + str(profit[instrument_token]))
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
                        if carry_forward < 0:
                            target_amount = abs((order_charges * -2) + carry_forward) / traded_quantity
                            print("amount to gain in this trade when carry forward is negative" + str(target_amount))
                        else:
                            target_amount = abs(order_charges * 2) / abs(traded_quantity)
                            print("amount to gain in this trade when carry forward is positive " + str(target_amount))
                        if profit[entries][4] > 0:
                            ds.trd_portfolio[entries]['Target_amount'] = ((traded_price + target_amount) - (
                                    (traded_price + target_amount) % ds.trd_portfolio[entries]['tick_size'])) + ds.trd_portfolio[entries]['tick_size']
                            print(ds.trd_portfolio[entries]['Target_amount'])
                        elif profit[entries][4] < 0:
                            ds.trd_portfolio[entries]['Target_amount'] = (traded_price - target_amount) - (
                                    (traded_price - target_amount) % ds.trd_portfolio[entries]['tick_size'])
                        print("final target price " + str(ds.trd_portfolio[entries]['Target_amount']))
            print(profit[instrument_token])
            del_processed_order()
        quantity()
    except Exception as e:
        traceback.print_exc(e)


def trigger(token):
    try:
        if ord_update_count() > 0:
            target()
        else:
            trigger_thread_running = "YES"
            if length_table(ds.trd_portfolio[token]['Symbol']) >= 1:  # length of the RENKO final table
                validation_row = latest_row(ds.trd_portfolio[token]['Symbol'])
                # print(validation_row[0], validation_row[1], validation_row[2], validation_row[3], validation_row[4])
                if validation_row[2] != 0:
                    if validation_row[1] == "SELL" and validation_row[2] > (validation_row[0]):
                        if profit[token][4] > 0:
                            print(profit[token][4])
                            ds.kite.modify_order(variety="regular", order_id=ds.trd_portfolio[token]['Target_order_id'],
                                              order_type=ds.kite.ORDER_TYPE_MARKET)
                            time.sleep(3)
                        elif profit[token][4] == 0:
                            if ds.trd_portfolio[token]['Direction'] != "Down":
                                if ds.trd_portfolio[token]['Tradable_quantity'] > 0:
                                    ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular",
                                                                                       exchange=ds.trd_portfolio[token][
                                                                                           'exchange'],
                                                                                       tradingsymbol=ds.trd_portfolio[token][
                                                                                           'Symbol'],
                                                                                       transaction_type=ds.kite.TRANSACTION_TYPE_SELL,
                                                                                       quantity=ds.trd_portfolio[token][
                                                                                           'Tradable_quantity'],
                                                                                       order_type=ds.kite.ORDER_TYPE_MARKET,
                                                                                       product=ds.kite.PRODUCT_MIS)
                                    print(ds.trd_portfolio[token]['Orderid'])
                                    time.sleep(3)
                                    order_status(token, ds.trd_portfolio[token]['Orderid'], 'SELL')
                    # BUY Condition
                    if validation_row[1] == "BUY" and validation_row[2] < (validation_row[0]):
                        if profit[token][4] < 0:
                            ds.kite.modify_order(variety="regular", order_id=ds.trd_portfolio[token]['Target_order_id'],
                                              order_type=ds.kite.ORDER_TYPE_MARKET)
                            time.sleep(2)
                        elif profit[token][4] == 0:
                            if ds.trd_portfolio[token]['Direction'] != "Up":
                                if ds.trd_portfolio[token]['Tradable_quantity'] > 0:
                                    ds.trd_portfolio[token]['Orderid'] = ds.kite.place_order(variety="regular",
                                                                                       exchange=ds.trd_portfolio[token][
                                                                                           'exchange'],
                                                                                       tradingsymbol=ds.trd_portfolio[token][
                                                                                           'Symbol'],
                                                                                       transaction_type=ds.kite.TRANSACTION_TYPE_BUY,
                                                                                       quantity=ds.trd_portfolio[token][
                                                                                           'Tradable_quantity'],
                                                                                       order_type=ds.kite.ORDER_TYPE_MARKET,
                                                                                       product=ds.kite.PRODUCT_MIS)
                                    print(ds.trd_portfolio[token]['Orderid'])
                                    time.sleep(2)
                                    order_status(token, ds.trd_portfolio[token]['Orderid'], 'BUY')
                    # Below ones are target orders
                    if profit[token][4] > 0:
                        if ds.trd_portfolio[token]['Target_order'] != "YES":
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
                    if profit[token][4] < 0:
                        if ds.trd_portfolio[token]['Target_order'] != "YES":
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
            trigger_thread_running = "NO"
    except TypeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.InputException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except ReadTimeout:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except exceptions.NetworkException:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except AttributeError:
        traceback.print_exc()
        trigger_thread_running = "NO"
        pass
    except Exception as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass
    except WantReadError as e:
        trigger_thread_running = "NO"
        pass


if __name__ == '__main__':
    quantity()
    while 10 > 2:
        while ((carry_forward/day_margin) * 100) < 2:
            for instrument in ds.trd_portfolio:
                trigger(instrument)
    # while ((carry_forward/day_margin) * 100) < 2:
    #     my_cursor.execute("select * from order_updates")
    #     records = my_cursor.fetchall()
    #     if my_cursor.rowcount != 0:
    #         target()
    #     else:
    #         trigger()

    #     for instrument in ds.trd_portfolio:
    #         trigger(instrument)
