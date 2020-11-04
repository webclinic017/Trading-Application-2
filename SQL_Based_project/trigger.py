import traceback
import time
from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions
from kiteconnect.exceptions import DataException
from requests.exceptions import ReadTimeout
import math
import mysql.connector
import datasetup as ds

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="password123",
    database="testdb"
)

my_cursor = mydb.cursor()

opening_margin = ds.kite.margins(segment=None)
print(opening_margin)
day_margin = opening_margin['equity']['net']

carry_forward = 0


def sum_all_of_stocks():
    my_cursor.execute("select sum(open) from rblbank_renko_final")
    total_quantity = my_cursor.fetchone()
    return total_quantity[0]


def ord_update_count():
    my_cursor.execute("select count(*) from order_updates")
    records = my_cursor.fetchall()
    return records[0][0]


print(ord_update_count())


sum_of_quantity = sum_all_of_stocks()


def round_down(n, decimals=0):
    try:
        multiplier = 10 ** decimals
        return math.floor(n * multiplier) / multiplier
    except Exception as e:
        traceback.print_exc(e)


def order_status(token, orderid, trade_type):
    try:
        order_details = kite.order_history(orderid)
        for item in order_details:
            if item['status'] == "COMPLETE":
                if trade_type == 'SELL':
                    trd_portfolio[token]['Direction'] = "Down"
                    trd_portfolio[token]['Target_order'] = "NO"
                    print(trd_portfolio[token]['Direction'])
                    break
                elif trade_type == 'BUY':
                    trd_portfolio[token]['Direction'] = "Up"
                    trd_portfolio[token]['Target_order'] = "NO"
                    print(trd_portfolio[token]['Direction'])
                    break
            elif item['status'] == "REJECTED":
                print("order got rejected", trd_portfolio[token]['Direction'], trd_portfolio[token]['Target_order'])
                break
        else:
            time.sleep(1)
            order_status(token, orderid, type)
    except Exception as e:
        order_status(token, orderid, type)
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


def target(price, symbol, transacion_type, volume, status, instrument_token):
    try:
        print("values before target module exe starts: " + str(ds.profit[instrument_token]))
        volume = volume * ds.trd_portfolio[instrument_token]['Quantity_multiplier']
        if status == "COMPLETE":
            ds.profit[instrument_token][0] = symbol
            if transacion_type == "BUY":
                if ds.profit[instrument_token][4] + volume == 0:
                    ds.profit[instrument_token][1] = price
                    ds.profit[instrument_token][4] = volume
                else:
                    ds.profit[instrument_token][1] = ((ds.profit[instrument_token][1] * ds.profit[instrument_token][4]) + (price * volume)) / (ds.profit[instrument_token][4] + volume)
                    ds.profit[instrument_token][4] = ds.profit[instrument_token][4] + volume
            elif transacion_type == "SELL":
                if ds.profit[instrument_token][4] - volume == 0:
                    ds.profit[instrument_token][2] = price
                    ds.profit[instrument_token][4] = volume
                else:
                    ds.profit[instrument_token][2] = ((ds.profit[instrument_token][2] * ds.profit[instrument_token][4]) + (price * volume)) / (ds.profit[instrument_token][4] + volume)
                    ds.profit[instrument_token][4] = ds.profit[instrument_token][4] - volume
            print(ds.profit[instrument_token])
            if (ds.profit[instrument_token][1] != 0) & (ds.profit[instrument_token][2] != 0):
                buy_brokerage = min((ds.profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['buy_brokerage']), 20)
                sell_brokerage = min((ds.profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['sell_brokerage']), 20)
                stt_ctt = ds.profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['stt_ctt']
                buy_tran = ds.profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['buy_tran']
                sell_tran = ds.profit[instrument_token][2] * volume * ds.trd_portfolio[instrument_token]['sell_tran']
                gst = (buy_brokerage + sell_brokerage + buy_tran + sell_tran + stt_ctt) * ds.trd_portfolio[instrument_token][
                    'gst']
                sebi_total = round((ds.profit[instrument_token][1] + ds.profit[instrument_token][2]) * volume * 0.000001, 0)
                stamp_charges = ds.profit[instrument_token][1] * volume * ds.trd_portfolio[instrument_token]['stamp']
                ds.profit[instrument_token][
                    5] = sebi_total + gst + sell_tran + buy_tran + buy_brokerage + sell_brokerage + stamp_charges
                ds.profit[instrument_token][3] = ((ds.profit[instrument_token][2] - ds.profit[instrument_token][1]) * volume) - ds.profit[instrument_token][5]
                ds.profit[instrument_token][6] = ds.profit[instrument_token][3] - ds.profit[instrument_token][5]
                ds.profit_temp = pd.DataFrame([ds.profit[instrument_token]],
                                           columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges",
                                                    "final_profit"])
                ds.profit_Final = ds.profit_Final.append(ds.profit_temp)
                ds.profit_Final.drop_duplicates(keep='first', inplace=True)
                ds.carry_forward = ds.carry_forward + ds.profit[instrument_token][6]
                print(ds.profit_Final.to_string())
                print("Amount made till now: " + str(ds.carry_forward))
                ds.profit[instrument_token] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
                print("the profit list after an order update" + str(ds.profit[instrument_token]))
            for entries in ds.trd_portfolio:
                if ds.profit[entries][4] != 0:
                    traded_price = max(ds.profit[entries][1], ds.profit[entries][2])
                    traded_quantity = abs(ds.profit[entries][4]) * ds.trd_portfolio[entries]['Quantity_multiplier']
                    Brokerage = min(((traded_price * traded_quantity) * ds.trd_portfolio[entries]['buy_brokerage']) * 2, 40)
                    STT = (traded_price * traded_quantity) * ds.trd_portfolio[entries]['stt_ctt']
                    TNXChrgs = ((traded_price * traded_quantity) * 2) * ds.trd_portfolio[entries]['buy_tran']
                    GST = (Brokerage + TNXChrgs) * ds.trd_portfolio[entries]['gst']
                    SEBIChrgs = ((traded_price * 2) * traded_quantity) * 0.000001
                    StampDuty = ((traded_price * 2) * traded_quantity) * ds.trd_portfolio[entries]['stamp']
                    order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty + STT
                    if ds.carry_forward < 0:
                        target_amount = abs((order_charges * -2) + ds.carry_forward) / traded_quantity
                        print("amount to gain in this trade" + str(target_amount))
                    else:
                        target_amount = abs(order_charges * 2) / abs(traded_quantity)
                        print("amount to gain in this trade" + str(target_amount))
                    if ds.profit[entries][4] > 0:
                        ds.trd_portfolio[entries]['Target_amount'] = min(((traded_price + target_amount) - (
                                (traded_price + target_amount) % ds.trd_portfolio[entries]['tick_size'])) + ds.trd_portfolio[entries]['tick_size'], ds.trd_portfolio[entries]['upper_circuit_limit'])
                    elif ds.profit[entries][4] < 0:
                        ds.trd_portfolio[entries]['Target_amount'] = max((traded_price - target_amount) - (
                                (traded_price - target_amount) % ds.trd_portfolio[entries]['tick_size']), ds.trd_portfolio[entries]['upper_circuit_limit'])
                    print("final target price" + str(ds.trd_portfolio[entries]['Target_amount']))
    except Exception as e:
        traceback.print_exc(e)


def trigger(token):
    try:
        if ord_update_count() > 0:
            target()
        else:
            trigger_thread_running = "YES"
            if len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']]) >= 1:
                if ((HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2]) == (
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 3])) and (
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] >
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5]) and (
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 8] > (
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5])):
                    if profit[token][4] > 0:
                        kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                          order_type=kite.ORDER_TYPE_MARKET)
                        time.sleep(3)
                    elif profit[token][4] == 0:
                        if trd_portfolio[token]['Direction'] != "Down":
                            if trd_portfolio[token]['Tradable_quantity'] > 0:
                                trd_portfolio[token]['Orderid'] = kite.place_order(variety="regular",
                                                                                   exchange=trd_portfolio[token][
                                                                                       'exchange'],
                                                                                   tradingsymbol=trd_portfolio[token][
                                                                                       'Symbol'],
                                                                                   transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                                   quantity=trd_portfolio[token][
                                                                                       'Tradable_quantity'],
                                                                                   order_type=kite.ORDER_TYPE_MARKET,
                                                                                   product=kite.PRODUCT_MIS)
                                print(trd_portfolio[token]['Orderid'])
                                time.sleep(3)
                                order_status(token, trd_portfolio[token]['Orderid'], 'SELL')
                # BUY Condition
                if (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] ==
                    HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 4]) and (
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 2] <
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5]) \
                        and (HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 8] < (
                        HA_Final.loc[HA_Final.Symbol == trd_portfolio[token]['Symbol']].iloc[-1, 5])):
                    if profit[token][4] < 0:
                        kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                          order_type=kite.ORDER_TYPE_MARKET)
                        time.sleep(2)
                    elif profit[token][4] == 0:
                        if trd_portfolio[token]['Direction'] != "Up":
                            if trd_portfolio[token]['Tradable_quantity'] > 0:
                                trd_portfolio[token]['Orderid'] = kite.place_order(variety="regular",
                                                                                   exchange=trd_portfolio[token][
                                                                                       'exchange'],
                                                                                   tradingsymbol=trd_portfolio[token][
                                                                                       'Symbol'],
                                                                                   transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                                   quantity=trd_portfolio[token][
                                                                                       'Tradable_quantity'],
                                                                                   order_type=kite.ORDER_TYPE_MARKET,
                                                                                   product=kite.PRODUCT_MIS)
                                print(trd_portfolio[token]['Orderid'])
                                time.sleep(2)
                                order_status(token, trd_portfolio[token]['Orderid'], 'BUY')
                # Below ones are target orders
                if profit[token][4] > 0:
                    if trd_portfolio[token]['Target_order'] != "YES":
                        trd_portfolio[token]['Target_order_id'] = kite.place_order(variety="regular",
                                                                                   exchange=trd_portfolio[token][
                                                                                       'exchange'],
                                                                                   tradingsymbol=trd_portfolio[token][
                                                                                       'Symbol'],
                                                                                   transaction_type=kite.TRANSACTION_TYPE_SELL,
                                                                                   quantity=abs(
                                                                                       trd_portfolio[token]['Positions']),
                                                                                   order_type=kite.ORDER_TYPE_LIMIT,
                                                                                   price=round(
                                                                                       trd_portfolio[token]['Target_amount'], 4), product=kite.PRODUCT_MIS)
                        if target_order_status(trd_portfolio[token]['Target_order_id']) == "OPEN":
                            trd_portfolio[token]['Target_order'] = "YES"
                if profit[token][4] < 0:
                    if trd_portfolio[token]['Target_order'] != "YES":
                        trd_portfolio[token]['Target_order_id'] = kite.place_order(variety="regular",
                                                                                   exchange=trd_portfolio[token][
                                                                                       'exchange'],
                                                                                   tradingsymbol=trd_portfolio[token][
                                                                                       'Symbol'],
                                                                                   transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                                                   quantity=abs(
                                                                                       trd_portfolio[token]['Positions']),
                                                                                   order_type=kite.ORDER_TYPE_LIMIT,
                                                                                   price=round_down(
                                                                                       trd_portfolio[token]['Target_amount'], 4),
                                                                                   product=kite.PRODUCT_MIS)
                        if target_order_status(trd_portfolio[token]['Target_order_id']) == "OPEN":
                            trd_portfolio[token]['Target_order'] = "YES"
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


# if __name__ == '__main__':
#     while sum_of_quantity != 0 and ((carry_forward/day_margin) * 100) < 2:
#         for instrument in ds.trd_portfolio:
#             trigger(instrument)
    # while ((carry_forward/day_margin) * 100) < 2:
    #     my_cursor.execute("select * from order_updates")
    #     records = my_cursor.fetchall()
    #     if my_cursor.rowcount != 0:
    #         target()
    #     else:
    #         trigger()

    #     for instrument in trd_portfolio:
    #         trigger(instrument)
