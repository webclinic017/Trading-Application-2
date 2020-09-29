from flask import Flask, request
import os
import datetime
import final
import json

app = Flask(__name__)


def log_name():
    # logs will be saved in files with current date
    return datetime.datetime.now().strftime("%Y-%m-%d") + '.txt'


@app.route('/post', methods=['POST'])
def post():
    # post back json data will be inside request.get_data()
    # as an example here it is being stored to a file
    f = open(log_name(), 'a+')
    order_response = request.get_data()
    f.write(str(order_response) + '\n')
    final.quantity()
    structured_response = json.loads(order_response)
    print(structured_response['average_price'], structured_response['tradingsymbol'], structured_response['transaction_type'], structured_response['quantity'], structured_response['status'], structured_response['instrument_token'])
    # circuit_limits()
    final.target(structured_response['average_price'], structured_response['tradingsymbol'], structured_response['transaction_type'], structured_response['quantity'], structured_response['status'], structured_response['instrument_token'])
    final.quantity()
    f.close()
    return 'done'


@app.route('/')
def index():
    # show the contents of todays log file
    if not os.path.exists(log_name()):
        open(log_name(), 'a+').close()
    return open(log_name()).read()


app.run(debug=True, host='0.0.0.0', port=80)
