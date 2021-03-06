import pandas as pd
from kiteconnect import KiteTicker, KiteConnect
import datetime

api_k = "dysoztj41hntm1ma"  # api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94"  # api_secret
access_token = "7HxjGWRwvuAjVhe1PhBdy39plpnKvDH1"
kws = KiteTicker(api_k, access_token)
kite = KiteConnect(api_key=api_k, access_token=access_token)

headers = {  # header for API request to update circuit limits
    'Authorization': 'token dysoztj41hntm1ma:' + access_token
}

opening_margin = kite.margins(segment=None)
day_margin = opening_margin['equity']['net']

trd_portfolio = {
    4708097: {"Market": "NSE", "Segment": "Equity", "Symbol": "RBLBANK", "max_quantity": 100, 'Direction': "", 'Orderid': 0,
              'Target_order': '',
              'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050,
              'Quantity_multiplier': 1, 'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003, 'stt_ctt': 0.00025,
              'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003, 'margin_multiplier': 5,
              'exchange': kite.EXCHANGE_NSE, 'buffer_quantity': 5, 'round_value': 2, 'Trade': "YES", 'tick_size': .05,
              'start_time': datetime.time(9, 30, 00), 'end_time': datetime.time(15, 15, 00), "lower_circuit_limit": 0,
              "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0},
    1270529: {"Market": "NSE", "Segment": "Equity", "Symbol": "ICICIBANK", "max_quantity": 100, 'Direction': "", 'Orderid': 0,
              'Target_order': '',
              'Target_order_id': 0, 'Positions': 0, 'Tradable_quantity': 0, 'LTP': 0, 'Per_Unit_Cost': 1050,
              'Quantity_multiplier': 1, 'buy_brokerage': 0.0003, 'sell_brokerage': 0.0003, 'stt_ctt': 0.00025,
              'buy_tran': 0.0000325, 'sell_tran': 0.0000325, 'gst': 0.18, 'stamp': 0.00003, 'margin_multiplier': 5,
              'exchange': kite.EXCHANGE_NSE, 'buffer_quantity': 5, 'round_value': 2, 'Trade': "YES", 'tick_size': .05,
              'start_time': datetime.time(9, 30, 00), 'end_time': datetime.time(15, 15, 00), "lower_circuit_limit": 0,
              "upper_circuit_limit": 0, 'Target_amount': 0, 'Options_lot_size': 0}}

ohlc = {}  # python dictionary to store the ohlc data in it
ohlc_temp = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
ohlc_final_1min = pd.DataFrame(columns=["Symbol", "Time", "Open", "High", "Low", "Close", "TR", "ATR", "SMA", "TMA"])
RENKO = {}  # python dictionary to store the renko chart data in it
RENKO_temp = pd.DataFrame(columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA", "TMA"])
RENKO_Final = pd.DataFrame(columns=["Symbol", "Open", "Close", "Signal", "Position", "SMA", "TMA"])
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


def candle_thread_running():
    return None