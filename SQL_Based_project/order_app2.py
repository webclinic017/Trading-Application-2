import datetime
from tkinter import *
from kiteconnect import KiteTicker, KiteConnect
import cryptography
import math
import pandas as pd

acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()
CE_ins_tkn = 0
PE_ins_tkn = 0
CE_symbol = ''
PE_symbol = ''
instrument_list = kite.instruments()
df = pd.DataFrame(instrument_list)

# below steps help us find the next expiry date
def expiry_date():
    d = datetime.date.today()
    while d.weekday() != 3:
        d += datetime.timedelta(1)

    if d == datetime.date.today():
        d += datetime.timedelta(7)
    return d


option_expiry_date = expiry_date()

def treadable_amount():
    opening_margin = kite.margins(segment=None)
    day_margin = opening_margin['equity']['available']['live_balance']
    return day_margin/3


single_order_amount = treadable_amount()

def nifty_spot():
    nifty_ltp = (kite.ltp('NSE:NIFTY 50')).get('NSE:NIFTY 50').get('last_price')
    return round(nifty_ltp / 100) * 100

def options_list():
    global CE_symbol,CE_ins_tkn, PE_ins_tkn, PE_symbol
    closest_strike = nifty_spot()
    valid_options = df.loc[(df['segment'] == 'NFO-OPT') & (df['name'] == 'NIFTY') & (
                df['expiry'].astype(str) == str(option_expiry_date)) & (df['strike'] == closest_strike)]
    print(valid_options.to_string())
    CE_ins_tkn = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 0]
    PE_ins_tkn = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 0]
    CE_symbol = valid_options[valid_options['instrument_type'] == 'CE'].iloc[0, 2]
    PE_symbol = valid_options[valid_options['instrument_type'] == 'PE'].iloc[0, 2]
    print(CE_ins_tkn, PE_ins_tkn, CE_symbol, PE_symbol)


options_list()



'''
# root = Tk()
#
#
# def buy():
#     bought_confirmation = Label(root, text="positions bought").grid(row=10, column=0, columnspan=2)
#     pass
#
#
# def exit_positions():
#     exit_confirmation = Label(root, text="positions exited").grid(row=10, column=3, columnspan=2)
#     pass
#
#
# root.title('Positions')
# root.geometry("600x400")
#
# # labels in the UI
# Margin = Label(root, text=day_margin, pady=10, padx=10).grid(row=0, column=0)
# Tradeable_options = Label(root, text="Tradeable Options", pady=10, padx=10).grid(row=1, column=0, columnspan=2)
# Buy_Button = Button(root, text="BUY", command=buy, borderwidth=5, pady=5, padx=5).grid(row=2, column=1)
# positions = Label(root, text="exisitng positions", pady=5, padx=5).grid(row=1, column=2, columnspan=2)
# Exit_Position_Button = Button(root, text="EXIT", command=exit_positions, borderwidth=5, pady=5, padx=5).grid(row=2, column=3)
#
# root.mainloop()

'''