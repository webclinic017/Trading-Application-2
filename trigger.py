import traceback
from datasetup import *
import time
from OpenSSL.SSL import WantReadError
from kiteconnect import exceptions
from kiteconnect.exceptions import DataException
from requests.exceptions import ReadTimeout
import math
from subprocess import *


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


def trigger(token):
    try:
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
#     print("Trigger started")
#     while ((carry_forward/day_margin) * 100) < 2:
#         for instrument in trd_portfolio:
#             trigger(instrument)