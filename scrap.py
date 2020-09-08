'''
def attained_profit():
    try:
        global day_margin, profit_Final, profit_temp, day_profit_percent
        for stock in trd_portfolio:
            profit[stock] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
        current_profit = 0
        orders = kite.orders()
        for line in orders:
            price = line['average_price']
            symbol = line['tradingsymbol']
            transaction_type = line['transaction_type']
            token = line['instrument_token']
            status = line['status']
            volume = line['quantity'] * trd_portfolio[token]['Quantity_multiplier']
            if transaction_type == 'BUY' and status == 'COMPLETE':
                profit[token][1] = price
            elif transaction_type == 'SELL' and status == 'COMPLETE':
                profit[token][2] = price
            profit[token][0] = symbol
            profit[token][4] = volume
            if (profit[token][1] != 0) & (profit[token][2] != 0):
                buy_brokerage = min((profit[token][1] * volume * trd_portfolio[token]['buy_brokerage']), 20)
                sell_brokerage = min((profit[token][2] * volume * trd_portfolio[token]['sell_brokerage']), 20)
                stt_ctt = profit[token][2] * volume * trd_portfolio[token]['stt_ctt']
                buy_tran = profit[token][1] * volume * trd_portfolio[token]['buy_tran']
                sell_tran = profit[token][2] * volume * trd_portfolio[token]['sell_tran']
                gst = (buy_brokerage + sell_brokerage + buy_tran + sell_tran + stt_ctt) * trd_portfolio[token]['gst']
                sebi_total = round((profit[token][1] + profit[token][2]) * volume * 0.000001, 0)
                stamp_charges = profit[token][1] * volume * trd_portfolio[token]['stamp']
                total_charges = sebi_total + gst + sell_tran + buy_tran + buy_brokerage + sell_brokerage + stamp_charges
                profit[token][3] = ((profit[token][2] - profit[token][1]) * volume) - total_charges
                current_profit = current_profit + profit[token][3]
                profit[token][1] = 0
                profit[token][2] = 0
        day_profit_percent = (current_profit / day_margin) * 100
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


def target(orderid, direction):
    global profit_Final, profit_temp
    try:
        for stock in trd_portfolio:
            profit[stock] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
        carry_forward = 0
        orders = kite.orders()
        for order in orders:
            price = order['average_price']
            symbol = order['tradingsymbol']
            transaction_type = order['transaction_type']
            stock_token = order['instrument_token']
            volume = order['quantity'] * trd_portfolio[stock_token]['Quantity_multiplier']
            status = order['status']
            if transaction_type == 'BUY' and status == 'COMPLETE':
                profit[stock_token][1] = price
            elif transaction_type == 'SELL' and status == 'COMPLETE':
                profit[stock_token][2] = price
            profit[stock_token][0] = symbol
            profit[stock_token][4] = volume
            if (profit[stock_token][1] != 0) & (profit[stock_token][2] != 0):
                buy_brokerage = min((profit[stock_token][1] * volume * trd_portfolio[stock_token]['buy_brokerage']), 20)
                sell_brokerage = min((profit[stock_token][2] * volume * trd_portfolio[stock_token]['sell_brokerage']),
                                     20)
                stt_ctt = profit[stock_token][2] * volume * trd_portfolio[stock_token]['stt_ctt']
                buy_tran = profit[stock_token][1] * volume * trd_portfolio[stock_token]['buy_tran']
                sell_tran = profit[stock_token][2] * volume * trd_portfolio[stock_token]['sell_tran']
                gst = (buy_brokerage + sell_brokerage + buy_tran + sell_tran + stt_ctt) * trd_portfolio[stock_token][
                    'gst']
                sebi_total = round((profit[stock_token][1] + profit[stock_token][2]) * volume * 0.000001, 0)
                stamp_charges = profit[stock_token][1] * volume * trd_portfolio[stock_token]['stamp']
                profit[stock_token][
                    5] = sebi_total + gst + sell_tran + buy_tran + buy_brokerage + sell_brokerage + stamp_charges
                profit[stock_token][3] = ((profit[stock_token][2] - profit[stock_token][1]) * volume) - \
                                         profit[stock_token][5]
                profit[stock_token][6] = profit[stock_token][3] - profit[stock_token][5]
                profit_temp = pd.DataFrame([profit[stock_token]],
                                           columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges",
                                                    "final_profit"])
                profit_Final = profit_Final.append(profit_temp)
                profit_Final.drop_duplicates(keep='first', inplace=True)
                profit[stock_token][1] = 0
                profit[stock_token][2] = 0
        print(profit_Final.to_string())
        for amount in range(len(profit_Final)):
            carry_forward = carry_forward + profit_Final.iloc[-(amount + 1), 6]
        print(carry_forward)

        Order_data = kite.order_history(orderid)
        for item in Order_data:
            if item['status'] == "COMPLETE":
                profit[item['instrument_token']] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
                traded_price = item['average_price']
                traded_quantity = item['quantity'] * trd_portfolio[item['instrument_token']]['Quantity_multiplier']
                Brokerage = min(
                    ((traded_price * traded_quantity) * trd_portfolio[item['instrument_token']]['buy_brokerage']) * 2,
                    40)
                STT = (traded_price * traded_quantity) * trd_portfolio[item['instrument_token']]['stt_ctt']
                TNXChrgs = ((traded_price * traded_quantity) * 2) * trd_portfolio[item['instrument_token']]['buy_tran']
                GST = (Brokerage + TNXChrgs) * trd_portfolio[item['instrument_token']]['gst']
                SEBIChrgs = ((traded_price * 2) * traded_quantity) * 0.000001
                StampDuty = ((traded_price * 2) * traded_quantity) * trd_portfolio[item['instrument_token']]['stamp']
                order_charges = Brokerage + TNXChrgs + GST + SEBIChrgs + StampDuty + STT
                if carry_forward < 0:
                    target_amount = abs((order_charges * -2) + carry_forward) / traded_quantity
                    print(target_amount)
                else:
                    target_amount = abs(order_charges * 2) / traded_quantity
                    print(target_amount)
                if direction == "Up":
                    return ((traded_price + target_amount) - (
                            (traded_price + target_amount) % trd_portfolio[item['instrument_token']][
                        'tick_size'])) + trd_portfolio[item['instrument_token']]['tick_size']
                elif direction == "Down":
                    return (traded_price - target_amount) - (
                            (traded_price - target_amount) % trd_portfolio[item['instrument_token']]['tick_size'])
        for stock in trd_portfolio:
            profit[stock] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
        profit_Final = profit_Final[0:0]
    except Exception as e:
        traceback.print_exc(e)
        target(orderid, direction)


def positions(token):
    global trigger_thread_running
    try:
        pos = kite.positions()
        day_pos = pos['day']
        posdf = pd.DataFrame(day_pos)
        if posdf.empty:
            return 0
        else:
            total_pos = posdf.loc[posdf['instrument_token'] == token, ['quantity']]
            if total_pos.empty:
                return 0
            else:
                current_pos = total_pos.iloc[0, 0]
                return int(current_pos)
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
'''

# On_ticks data
'''                
                if trd_portfolio[company_data['instrument_token']]['start_time'] < (
                        company_data['last_trade_time'].time()) < trd_portfolio[company_data['instrument_token']]['end_time']:
                    if trd_portfolio[company_data['instrument_token']]['Trade'] == "YES":
                        if ((carry_forward/day_margin) * 100) < 2:
                            if trigger_thread_running != 'YES':
                                if len(HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']]) >= 1:
                                    if HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']]['Symbol']].iloc[-1, 8] != 0:
                                        if ((HA_Final.loc[
                                            HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                'Symbol']].iloc[-1, 2]) == (HA_Final.loc[HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                'Symbol']].iloc[-1, 3])) and (HA_Final.loc[HA_Final.Symbol ==
                                                                                           trd_portfolio[company_data[
                                                                                               'instrument_token']][
                                                                                               'Symbol']].iloc[
                                                                                  -1, 2] > (HA_Final.loc[
                                            HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                'Symbol']].iloc[-1, 5])) and (
                                                HA_Final.loc[
                                                    HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                        'Symbol']].iloc[-1, 8] > (HA_Final.loc[
                                            HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                'Symbol']].iloc[-1, 5])):
                                            order_trigger_loop_initiator = threading.Thread(target=trigger, args=[
                                                company_data['instrument_token']])
                                            order_trigger_loop_initiator.start()
                                        if (HA_Final.loc[
                                                HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                    'Symbol']].iloc[-1, 2] ==
                                            HA_Final.loc[
                                                HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                    'Symbol']].iloc[-1, 4]) and (
                                                HA_Final.loc[
                                                    HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                        'Symbol']].iloc[-1, 5] >
                                                HA_Final.loc[
                                                    HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                        'Symbol']].iloc[-1, 2]) and (
                                                HA_Final.loc[
                                                    HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                        'Symbol']].iloc[-1, 8] < (HA_Final.loc[
                                            HA_Final.Symbol == trd_portfolio[company_data['instrument_token']][
                                                'Symbol']].iloc[-1, 5])):
                                            order_trigger_loop_initiator = threading.Thread(target=trigger, args=[
                                                company_data['instrument_token']])
                                            order_trigger_loop_initiator.start()
'''