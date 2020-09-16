import traceback
import datasetup as ds
import pandas as pd


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
