from flask import Flask, jsonify
from datetime import date, timedelta
import datetime
import requests
import json
from flask_cors import CORS

# if saturday and sunday return fridays' prices, else return today's prices
weekno = datetime.datetime.today().weekday()

if weekno == 6:
    mostrecentday = str(date.today() - timedelta(days=2))
elif weekno == 0:
    mostrecentday = str(date.today()- timedelta(days=3))
else:
    mostrecentday = str(date.today() - timedelta(days=1))

app = Flask(__name__)
CORS(app)

@app.route("/stock_info/buy/<string:stockName>")
def buy(stockName):   
# get yesterday's/today's close prices for all stocks (USE YOUR OWN KEYS LOL[i only hv 5 req/min] -- polygon.io)
    r = requests.get('https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/'+mostrecentday+'?adjusted=true&apiKey=JVUOJpz7eTK1LXR6J0bZxnQVnyifIbvt')
    results = r.json()['results']

# find close price of stock chosen by user
    for result in results:
        if result['T'] == stockName:
            user_ticker_close_price = result['c']
            final_result = {"Ticker" : str(result['T']), "Close Price" : str(user_ticker_close_price)}
            final_result1 = json.dumps(final_result)
            return {
                "code":200,
                "data":final_result1
            }
    else:
        return {
            "code":404,
            "message": "Ticker not found"
        }



@app.route("/stock_info/get_all_stock_info")
def get_all_stock_info():
# get yesterday's/today's close prices for all stocks (USE YOUR OWN KEYS LOL[i only hv 5 req/min] -- polygon.io)
    # r = requests.get('https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/'+mostrecentday+'?adjusted=true&apiKey=svwrq5Gs8XJYQos1HqSs0T3ilmE1KAOx')
    r = requests.get('https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/'+'2022-03-28'+'?adjusted=true&apiKey=svwrq5Gs8XJYQos1HqSs0T3ilmE1KAOx')
    results = r.json()['results']
    return jsonify(results)

@app.route("/stock_info/get_indiv_info/<string:stockName>")
def get_indiv_info(stockName):
# get info for one stock
    r = requests.get('https://api.polygon.io/v2/aggs/ticker/'+stockName+'/range/1/day/2021-07-22/2021-07-22?adjusted=true&sort=asc&limit=120&apiKey=svwrq5Gs8XJYQos1HqSs0T3ilmE1KAOx')
    results = r.json()['results']
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5005, debug=True)

