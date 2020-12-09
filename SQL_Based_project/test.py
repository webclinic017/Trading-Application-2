

opening_margin = kite.margins(segment=None)
# print(opening_margin)
day_margin = opening_margin['equity']['net']


trigger_thread_running = ""
day_profit_percent = 0
last_order_id = 0
last_order_type = ''
last_order_status = ''
tick_count = 0
order_count = 0
carry_forward = 0

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="password123",
    database="testdb"
)

my_cursor = mydb.cursor()



ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol", "Open", "Close", "Direction", "Position", "SMA", "TMA"])
HA = {}  # python dictionary to store the ohlc data in it
HA_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
HA_Final = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
profit = {}
profit_temp = pd.DataFrame(columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])
profit_Final = pd.DataFrame(
    columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"])

for x in trd_portfolio:
    ohlc[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0,
               0]  # [Symbol, Traded Time, Open, High, Low, Close, True Range, Average True Range, Simple Moving Average, Triangular moving average, positions ]
    RENKO[x] = ["Symbol", 0, 0, "Signal", "None", 0, 0]
    HA[x] = ["Symbol", "Time", 0, 0, 0, 0, 0, 0, 0, 0]
    profit[x] = ["Symbol", 0, 0, "Profit", 0, 0, 0]  # ["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges", "final_profit"]


def ord_update_count():
    my_cursor.execute("select count(*) from order_updates")
    records = my_cursor.fetchall()
    return records[0][0]


def first_order():
    my_cursor.execute("select * from order_updates limit 1")
    data = my_cursor.fetchone()
    return [data[0], data[1], data[2], data[3], data[4], data[5]]


def del_processed_order():
    my_cursor.execute("delete from order_updates limit 1")
    mydb.commit("select count(*) from processed ")


def target():
    global carry_forward, profit_temp, profit_Final
    try:
        while ord_update_count() > 0:
            order_details = first_order()
            print(order_details[0], order_details[1], order_details[2], order_details[3], order_details[4], order_details[5])
            price = order_details[4]
            volume = order_details[5]
            symbol = order_details[0]
            instrument_token = order_details[1]
            status = order_details[2]
            transacion_type = order_details[3]
            volume = volume * trd_portfolio[instrument_token]['Quantity_multiplier']
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
                        profit[instrument_token][2] = ((profit[instrument_token][2] * profit[instrument_token][4]) + (price * volume)) / (profit[instrument_token][4] + volume)
                        profit[instrument_token][4] = profit[instrument_token][4] - volume
                print(profit[instrument_token])
                if (profit[instrument_token][1] != 0) & (profit[instrument_token][2] != 0):
                    buy_brokerage = min((profit[instrument_token][1] * volume * trd_portfolio[instrument_token]['buy_brokerage']), 20)
                    sell_brokerage = min((profit[instrument_token][2] * volume * trd_portfolio[instrument_token]['sell_brokerage']), 20)
                    stt_ctt = profit[instrument_token][2] * volume * trd_portfolio[instrument_token]['stt_ctt']
                    buy_tran = profit[instrument_token][1] * volume * trd_portfolio[instrument_token]['buy_tran']
                    sell_tran = profit[instrument_token][2] * volume * trd_portfolio[instrument_token]['sell_tran']
                    gst = (buy_brokerage + sell_brokerage + buy_tran + sell_tran + stt_ctt) * trd_portfolio[instrument_token][
                        'gst']
                    sebi_total = round((profit[instrument_token][1] + profit[instrument_token][2]) * volume * 0.000001, 0)
                    stamp_charges = profit[instrument_token][1] * volume * trd_portfolio[instrument_token]['stamp']
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
                    print("the profit list after an order update" + str(profit[instrument_token]))
                for entries in trd_portfolio:
                    if profit[entries][4] != 0:
                        traded_price = max(profit[entries][1], profit[entries][2])
                        traded_quantity = abs(profit[entries][4]) * trd_portfolio[entries]['Quantity_multiplier']
                        Brokerage = min(((traded_price * traded_quantity) * trd_portfolio[entries]['buy_brokerage']) * 2, 40)
                        STT = (traded_price * traded_quantity) * trd_portfolio[entries]['stt_ctt']
                        TNXChrgs = ((traded_price * traded_quantity) * 2) * trd_portfolio[entries]['buy_tran']
                        GST = (Brokerage + TNXChrgs) * trd_portfolio[entries]['gst']
                        SEBIChrgs = ((traded_price * 2) * traded_quantity) * 0.000001
                        StampDuty = ((traded_price * 2) * traded_quantity) * trd_portfolio[entries]['stamp']
                        order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty + STT
                        if carry_forward < 0:
                            target_amount = abs((order_charges * -2) + carry_forward) / traded_quantity
                            print("amount to gain in this trade" + str(target_amount))
                        else:
                            target_amount = abs(order_charges * 2) / abs(traded_quantity)
                            print("amount to gain in this trade" + str(target_amount))
                        if profit[entries][4] > 0:
                            trd_portfolio[entries]['Target_amount'] = min(((traded_price + target_amount) - (
                                    (traded_price + target_amount) % trd_portfolio[entries]['tick_size'])) + trd_portfolio[entries]['tick_size'], trd_portfolio[entries]['upper_circuit_limit'])
                        elif profit[entries][4] < 0:
                            trd_portfolio[entries]['Target_amount'] = max((traded_price - target_amount) - (
                                    (traded_price - target_amount) % trd_portfolio[entries]['tick_size']), trd_portfolio[entries]['upper_circuit_limit'])
                        print("final target price" + str(trd_portfolio[entries]['Target_amount']))
            del_processed_order()
        quantity()
    except Exception as e:
        traceback.print_exc(e)






def quantity():
    try:
        temp_open_margin = KiteConnect.margins(kite)
        temp_day_margin = temp_open_margin['equity']['net']
        for items in trd_portfolio:
            if trd_portfolio[items]['Segment'] == "Options":  # calculating quantity for options
                maxquantity = min(temp_day_margin / trd_portfolio[items]['LTP'], trd_portfolio[items]['max_quantity'])
                multiplier = 0
                while (multiplier * 75) < maxquantity: # trd_portfolio[items]['max_quantity']:
                    multiplier = multiplier + 1
                else:
                    trd_portfolio[items]['Tradable_quantity'] = (multiplier - 1) * 75
            elif trd_portfolio[items]['Segment'] != "Options":  # calculating quantity for equities
                if trd_portfolio[items]['LTP'] != 0:
                    if ((temp_day_margin * trd_portfolio[items]['margin_multiplier']) / (trd_portfolio[items]['LTP'] * trd_portfolio[items]['Quantity_multiplier'])) - trd_portfolio[items]['buffer_quantity'] < 1:
                        trd_portfolio[items]['Tradable_quantity'] = 0
                        print("a")
                    else:
                        trd_portfolio[items]['Tradable_quantity'] = int(round(min(((day_margin * trd_portfolio[items]['margin_multiplier']) / (trd_portfolio[items]['LTP'] * trd_portfolio[items][
                            'Quantity_multiplier'])) - trd_portfolio[items]['buffer_quantity'],
                                                                                  trd_portfolio[items]['max_quantity']), 0))
                        print("b", trd_portfolio[items]['Tradable_quantity'])
                        # print(str(day_margin) + "*" + str(trd_portfolio[items]['margin_multiplier']) + "/" + str(trd_portfolio[items]['LTP']) + "*" + str(trd_portfolio[items][
                        #     'Quantity_multiplier']) + "-" + str(trd_portfolio[items]['buffer_quantity']), str(trd_portfolio[items]['max_quantity']))
            my_cursor.execute("update trd_portfolio set Tradable_quantity = trd_portfolio[items]['Tradable_quantity'] where token = trd_portfolio[items]")
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
    except Exception as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass
    except WantReadError as e:
        traceback.print_exc(e)
        trigger_thread_running = "NO"
        pass


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
                print("quantity validation before ordering", str(profit[token][4]))
                if profit[token][4] > 0:
                    kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                      order_type=kite.ORDER_TYPE_MARKET)
                    time.sleep(3)
                    print("exiting current positions")
                elif profit[token][4] == 0:
                    if trd_portfolio[token]['Direction'] != "Down":
                        if trd_portfolio[token]['Tradable_quantity'] > 0:
                            print("Fresh order")
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
                print("quantity validation before ordering", str(profit[token][4]))
                if profit[token][4] < 0:
                    kite.modify_order(variety="regular", order_id=trd_portfolio[token]['Target_order_id'],
                                      order_type=kite.ORDER_TYPE_MARKET)
                    time.sleep(2)
                    print("exiting current positions")
                elif profit[token][4] == 0:
                    if trd_portfolio[token]['Direction'] != "Up":
                        if trd_portfolio[token]['Tradable_quantity'] > 0:
                            print("Fresh order")
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
            print("quantity validation before target set", str(profit[token][4]))
            print(profit[token])
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



