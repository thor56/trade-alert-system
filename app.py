from re import match
from flask import Flask, json, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta

import os
from sqlalchemy.engine import create_engine

from sqlalchemy.sql.elements import Case

app = Flask(__name__)
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


engine = create_engine('postgresql://postgres:123@localhost/postgres')


@app.route("/")
def hello_world():

    return "Hello World!"


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
    result = []
    books = []
    with engine.connect() as con:
        books = con.execute("SELECT H.ticker, H.signal, H.timestamp FROM hour H, minutes M where H.ticker = M.ticker and " +
                            "CASE " +
                            "WHEN CAST(M.position AS DECIMAL(7,2)) > CAST(0 AS DECIMAL(7,2)) THEN H.signal = 'LONG' " +
                            "ELSE H.signal = 'SHORT' " +
                            "END and " +
                            "H.timestamp between M.timestamp - INTERVAL '1 hour' and M.timestamp ORDER BY H.timestamp desc ")


    return render_template('view.html', title='Trades', books=books)
