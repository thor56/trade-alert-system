from re import match
import re
from flask import Flask, json, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bootstrap import Bootstrap
from datetime import datetime, timedelta
from sqlalchemy.engine import create_engine
from sqlalchemy.sql.elements import Case
from coinapi_rest_v1.restapi import CoinAPIv1
from dateutil import parser
import os
import requests
import json
import pandas as pd
from customfunctions import get_pivots, getSwings, getSymbolIds, validateTrade


app = Flask(__name__)
Bootstrap(app)
app.config['DEBUG'] = True
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123@localhost/postgres"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL1")

db = SQLAlchemy(app)
CORS(app)


class M12(db.Model):
    __tablename__ = "minutes"
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(255))
    position = db.Column(db.String(255))
    timestamp = db.Column(db.Time())

    def __init__(self, ticker, position, timestamp):
        self.ticker = ticker
        self.position = position
        self.timestamp = timestamp

    def __repr__(self):
        return '%s/%s/%s' % (self.ticker, self.position,  self.timestamp)


class H3(db.Model):
    __tablename__ = "hour"
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(255))
    signal = db.Column(db.String(255))
    timestamp = db.Column(db.Time())

    def __init__(self, ticker, signal, timestamp):
        self.ticker = ticker
        self.signal = signal
        self.timestamp = timestamp

    def __repr__(self):
        return '%s/%s/%s' % (self.ticker, self.signal,  self.timestamp)


engine = create_engine(os.environ.get("DATABASE_URL1"))


@app.route("/")
def hello_world():

    return render_template('index.html')


@app.route("/webhook", methods=['POST'])
def test():
    data = json.loads(request.data)

    if 'position' in data:
        m12 = M12(data['ticker'], data['position'], data['time'])
        db.session.add(m12)
    elif 'signal' in data:
        h3 = H3(data['ticker'], data['signal'], data['time'])
        db.session.add(h3)

    db.session.commit()

    return data


@app.route("/view")
def view():

    H1Diff = []
    H1Result = []
    M30Diff = []
    M30Result = []
    H3Diff = []
    H3Result = []
    #  1H DIFF
    with engine.connect() as con:
        H1Result = con.execute("SELECT H.ticker, H.signal, H.timestamp FROM hour H, minutes M where H.ticker = M.ticker and " +
                               "CASE " +
                               "WHEN CAST(M.position AS DECIMAL(7,2)) > CAST(0 AS DECIMAL(7,2)) THEN H.signal = 'LONG' " +
                               "ELSE H.signal = 'SHORT' " +
                               "END and " +
                               "H.timestamp between M.timestamp - INTERVAL '1 hour' and M.timestamp ORDER BY H.timestamp desc ")

    for x in H1Result:
        if x not in H1Diff:
            H1Diff.append(x)

    C1H = len(H1Diff)
    #   30M DIFF
    with engine.connect() as con:
        M30Result = con.execute("SELECT H.ticker, H.signal, " +
                                "CASE WHEN H.timestamp > M.timestamp THEN H.timestamp else M.timestamp END" +
                                " FROM hour H, minutes M where H.ticker = M.ticker and " +
                                "CASE WHEN CAST(M.position AS DECIMAL(7,2)) > CAST(0 AS DECIMAL(7,2)) THEN H.signal = 'LONG' " +
                                "ELSE H.signal = 'SHORT' " +
                                "END and " +
                                "H.timestamp between M.timestamp - INTERVAL '30 minutes' and M.timestamp + INTERVAL '30 minutes' ORDER BY H.timestamp desc ")

    for x in M30Result:
        if x not in M30Diff:
            M30Diff.append(x)
    C30M = len(M30Diff)

    #   3H DIFF
    with engine.connect() as con:
        H3Result = con.execute("SELECT H.ticker, H.signal, " +
                               "CASE WHEN H.timestamp > M.timestamp THEN H.timestamp else M.timestamp END" +
                               " FROM hour H, minutes M where H.ticker = M.ticker and " +
                               "CASE WHEN CAST(M.position AS DECIMAL(7,2)) > CAST(0 AS DECIMAL(7,2)) THEN H.signal = 'LONG' " +
                               "ELSE H.signal = 'SHORT' " +
                               "END and " +
                               "H.timestamp between M.timestamp - INTERVAL '3 hours' and M.timestamp + INTERVAL '3 hours' ORDER BY H.timestamp desc ")

    for x in H3Result:
        if x not in H3Diff:
            H3Diff.append(x)

    C3H = len(H3Diff)
    df_swing = getSwings('BINANCE_SPOT_ALGO_USDT')
    df_trade_1H = pd.DataFrame(
        H1Diff, columns=['ticker', 'position', 'timestamp'])

    validateTrade(df_trade_1H)

    return render_template('view.html', title='Trades', H1Diff=H1Diff, M30Diff=M30Diff, H3Diff=H3Diff, C1H=C1H, C30M=C30M, C3H=C3H)


@app.route("/getChart")
def getChart():
    # url = 'https://rest.coinapi.io/v1/ohlcv/POLONIEX_SPOT_LTC_USDC/history?period_id=1MIN&time_start=2020-01-01T00:00:00'
    # url = 'https://rest.coinapi.io/v1/symbols'

    # headers = {'X-CoinAPI-Key': '08F2D382-58E3-49B0-8B6F-CB20DD06DE17'}
    # response = requests.get(url, headers=headers)
    # data = response.content
    lis = []
    f = open('data1.json')

    # returns JSON object as
    # a dictionary
    data = json.load(f)

    # Iterating through the json
    # list
    for i in data:
        lis.append(i['symbol_id'])

    # Closing file
    f.close()

    # df1 = pd.DataFrame([x] for x in lis)
    # df1.to_excel('symbolid.xlsx')
    df2 = pd.read_excel('watchlist.xlsx', engine='openpyxl')
    lis2 = list(df2[0])
    lis3 = []
    for x in lis2:
        if "BINANCE_SPOT_" + x + "_USDT" in lis:
            lis3.append("BINANCE_SPOT_" + x + "_USDT")
        elif "KUCOIN_SPOT_" + x + "_USDT" in lis:
            lis3.append("KUCOIN_SPOT_" + x + "_USDT")
        elif "FTX_SPOT_" + x + "_USDT" in lis:
            lis3.append("FTX_SPOT_" + x + "_USDT")
        elif "COINBASE_SPOT_" + x + "_USDT" in lis:
            lis3.append("COINBASE_SPOT_" + x + "_USDT")
        elif "GATEIO_SPOT_" + x + "_USDT" in lis:
            lis3.append("GATEIO_SPOT_" + x + "_USDT")
        else:
            lis3.append("")
    df1 = pd.DataFrame({'Coin': lis2, 'symbol_id': lis3})
    df1.to_excel('FinalList.xlsx')
    return ''


def ConvertWatchList():
    df = pd.read_csv('Watchlist.csv')
    lis = []
    for col in df:

        if 'USDT' not in col and 'BUSD' not in col:
            # print(re.sub(r'^.*?:', '', col[:-3]))
            lis.append(re.sub(r'^.*?:', '', col[:-3]))
        else:
            # print(re.sub(r'^.*?:', '', col[:-4]))
            lis.append(re.sub(r'^.*?:', '', col[:-4]))

    df1 = pd.DataFrame([x] for x in lis)
    df1.to_excel('watchlist.xlsx')
    return 'Success!'


@app.route("/getPriceData")
def getPriceData():
    # BITSTAMP_SPOT_BTC_USD
    # region inputs
    symbol_id = request.args['symbol_id']
    _date = request.args['date']
    # endregion
    symbol_list = getSymbolIds()
    for symbol in symbol_list:
        symbol_id = symbol
        # region time converions
        to_date = parser.parse(_date)
        to_date_str = str(
            (to_date+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%f%z'))
        # endregion

        # region API req and OHLC Data save
        url = 'https://rest.coinapi.io/v1/ohlcv/' + symbol_id + \
            '/history?period_id=10MIN&time_start='+_date + \
            '&time_end' + to_date_str + '&limit=144'

        #   anima@
        headers = {'X-CoinAPI-Key': '08F2D382-58E3-49B0-8B6F-CB20DD06DE17'}
        #   ran598
        # headers = {'X-CoinAPI-Key': 'E635958C-2CCA-43EE-B3E1-EB22AF831D0F'}
        # headers = {'X-CoinAPI-Key': '8C05335A-ED7E-47F1-A949-C3856592155A'}
        #   # tcfu
        # headers = {'X-CoinAPI-Key': 'DB2795F5-14D0-46BC-9AE7-41E1A5F16A64'}
        #   # tech2
        # headers = {'X-CoinAPI-Key': '9B6D3727-F3E4-4319-B4D3-A1FA93D09C14'}
        #   # sujan

        response = requests.get(url, headers=headers)
        df = pd.read_json(response.content)
        if not os.path.exists('OHLC/' + str(_date)):
            os.makedirs('OHLC/' + str(_date))

        df.to_excel('OHLC/' + str(_date) + '/' + symbol_id + '.xlsx')
    # endregion
    # url = 'https://rest.coinapi.io/v1/assets'
    # headers = {'X-CoinAPI-Key': '08F2D382-58E3-49B0-8B6F-CB20DD06DE17'}  # anima@
    # headers = {'X-CoinAPI-Key': 'E635958C-2CCA-43EE-B3E1-EB22AF831D0F'}  # ran598
    # headers = {'X-CoinAPI-Key': '8C05335A-ED7E-47F1-A949-C3856592155A'}  # tcfu
    # headers = {'X-CoinAPI-Key': 'DB2795F5-14D0-46BC-9AE7-41E1A5F16A64'}  # tech2
    # headers = {'X-CoinAPI-Key': '9B6D3727-F3E4-4319-B4D3-A1FA93D09C14'}  # sujan

    response = requests.get(url, headers=headers)
    return str(response.headers)


@ app.route("/calculateSwings")
def calculateSwings():
    symbol_list = getSymbolIds()
    for symbol in list(symbol_list):
        for root, subdirectories, files in os.walk('OHLC/'):
            for subdirectory in subdirectories:
                folderName = os.path.join(root, subdirectory)
                df = pd.read_excel(folderName + '/' +
                                   symbol + '.xlsx', engine='openpyxl')
                df = get_pivots(df, symbol)
                if not os.path.exists('swings/' + subdirectory):
                    os.makedirs('swings/' + subdirectory)
                df.to_excel('swings/' + subdirectory + '/' + symbol + '.xlsx')
    return ''
