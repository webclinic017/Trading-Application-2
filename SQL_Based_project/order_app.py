import datetime
from tkinter import *
from kiteconnect import KiteTicker, KiteConnect
import math
import pandas as pd

acc_token = open("access-token.txt", "r")

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret
access_token = acc_token.read()
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)
acc_token.close()

expiry_date = datetime.datetime.today() + datetime.timedelta(days=datetime.datetime.today().isoweekday() % 4)
print(type(expiry_date.date()))
print(str(expiry_date.date()))

opening_margin = kite.margins(segment=None)
print(opening_margin)
day_margin = opening_margin['equity']['available']['live_balance']
print(day_margin)

nifty_ltp = (kite.ltp('NSE:NIFTY 50')).get('NSE:NIFTY 50').get('last_price')
print(nifty_ltp)
closest_strike = round(nifty_ltp/100)*100
print("closest strike price is - {}".format(closest_strike))

instrument_list = kite.instruments()
df = pd.DataFrame(instrument_list)
valid_options = df.loc[(df['segment'] == 'NFO-OPT') & (df['name'] == 'NIFTY') & (df['expiry'].astype(str) == str(expiry_date.date())) & (df['strike'] == closest_strike) & (df['instrument_type'] == 'CE')].iloc[-1, 1]
print(type(valid_options['expiry']))
print(valid_options.to_string())
# for x in instrument_list:
#     print(x)
#
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