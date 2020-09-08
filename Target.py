import traceback
from datasetup import *


def target(price, symbol, transacion_type, volume, status, instrument_token):
    global profit_Final, profit_temp, carry_forward, profit
    try:
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
                                           columns=["Symbol", "BUY Price", "SELL Price", "Profit", "Volume", "Charges",
                                                    "final_profit"])
                profit_Final = profit_Final.append(profit_temp)
                profit_Final.drop_duplicates(keep='first', inplace=True)
                carry_forward = carry_forward + profit[instrument_token][6]
                print(profit_Final.to_string())
                print("Amount made till now: " + str(carry_forward))
                profit[instrument_token] = ["Symbol", 0, 0, "Profit", 0, 0, 0]
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
    except Exception as e:
        traceback.print_exc(e)
