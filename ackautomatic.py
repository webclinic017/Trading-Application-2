import requests
import json
import kiteconnect
from kiteconnect import KiteTicker, KiteConnect
import datetime
from datasetup import *

headers = {
    'Authorization': 'token dysoztj41hntm1ma:'+access_token
}

with requests.session() as s:
    url = "https://api.kite.trade/quote?i="
    for x in trd_portfolio:
        request_url = url+trd_portfolio[x]["Market"]+":"+trd_portfolio[x]["Symbol"]
        r = s.get(request_url, headers=headers)
        result = json.loads(r.content)
        print("Lower Circuit Limit ",
              result['data'][trd_portfolio[x]["Market"] + ":" + trd_portfolio[x]["Symbol"]]['lower_circuit_limit'])
        trd_portfolio[x]['lower_circuit_limit'] = result['data'][trd_portfolio[x]["Market"] + ":" + trd_portfolio[x]["Symbol"]]['lower_circuit_limit']
        print("Upper Circuit Limit ",
              result['data'][trd_portfolio[x]["Market"] + ":" + trd_portfolio[x]["Symbol"]]['upper_circuit_limit'])
        trd_portfolio[x]['upper_circuit_limit'] = result['data'][trd_portfolio[x]["Market"] + ":" + trd_portfolio[x]["Symbol"]]['upper_circuit_limit']

print(trd_portfolio.values())
