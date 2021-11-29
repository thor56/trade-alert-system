from re import match
from flask import Flask, json, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from flask_bootstrap import Bootstrap


import os
from sqlalchemy.engine import create_engine

from sqlalchemy.sql.elements import Case

app = Flask(__name__)
Bootstrap(app)
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

    return render_template('view.html', title='Trades', H1Diff=H1Diff, M30Diff=M30Diff, H3Diff=H3Diff, C1H=C1H, C30M=C30M, C3H=C3H)
