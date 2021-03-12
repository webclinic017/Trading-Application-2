from requests.exceptions import ReadTimeout
from urllib.request import *
import requests
import json
import usdinr as ds

headers = {  # header for API request to update circuit limits
    'Authorization': 'token dysoztj41hntm1ma:' + ds.access_token
}


def circuit_limits():
    with requests.session() as s:
        url = "https://api.kite.trade/quote?i="
        for entries in ds.trd_portfolio:
            request_url = url + ds.trd_portfolio[entries]["Market"] + ":" + ds.trd_portfolio[entries]["Symbol"]
            r = s.get(request_url, headers=headers)
            result = json.loads(r.content)
            # print(result)
            ds.trd_portfolio[entries]['lower_circuit_limit'] = result['data'][ds.trd_portfolio[entries]["Market"] + ":" + ds.trd_portfolio[entries]["Symbol"]][
                    'lower_circuit_limit']
            print(ds.trd_portfolio[entries]['lower_circuit_limit'])
            ds.trd_portfolio[entries]['upper_circuit_limit'] = result['data'][ds.trd_portfolio[entries]["Market"] + ":" + ds.trd_portfolio[entries]["Symbol"]][
                    'upper_circuit_limit']
            print(ds.trd_portfolio[entries]['upper_circuit_limit'])


circuit_limits()
