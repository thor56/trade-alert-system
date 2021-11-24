from flask import Flask, json, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import create_engine

import os

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
    minutes_data = M12.query.all()
    data = []
    result =[]
    for x in minutes_data:
        signal = "LONG"
        if float(x.position) < 0:
            signal = "SHORT"

        query = db.session.query(H3).filter(
            H3.ticker.like(x.ticker),
            H3.signal.like(signal),
            H3.timestamp.between(x.timestamp + timedelta(minutes=-30), x.timestamp + timedelta(minutes=30)))
        for row in db.session.execute(query).fetchall():
            data.append(list(row))
            print(row.__dict__)
        
    for i in data:
        if i not in result:
            result.append(i)
    # print(result)
    return render_template('view.html', title='Trades', result = result)

    
