from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import traceback

trd_portfolio = {779521:{"Symbol":"SBIN","max_quantity":10000},
                 779522:{"Symbol":"ABC","max_quantity":100}
                 }

print(trd_portfolio[779521]['Symbol'])