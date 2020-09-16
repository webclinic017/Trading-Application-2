from requests.exceptions import ReadTimeout
from datasetup import *
from urllib.request import *
import requests
import json


def circuit_limits():
    with requests.session() as s:
        url = "https://api.kite.trade/quote?i="
        for entries in trd_portfolio:
            request_url = url + trd_portfolio[entries]["Market"] + ":" + trd_portfolio[entries]["Symbol"]
            r = s.get(request_url, headers=headers)
            result = json.loads(r.content)
            # print(result)
            trd_portfolio[entries]['lower_circuit_limit'] = result['data'][trd_portfolio[entries]["Market"] + ":" + trd_portfolio[entries]["Symbol"]][
                    'lower_circuit_limit']
            trd_portfolio[entries]['upper_circuit_limit'] = result['data'][trd_portfolio[entries]["Market"] + ":" + trd_portfolio[entries]["Symbol"]][
                    'upper_circuit_limit']
