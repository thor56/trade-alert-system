from flask import Flask, json, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

import os

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123@localhost/users"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL1")

db = SQLAlchemy(app)
CORS(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return '%s/%s' % (self.name, self.email)


@app.route("/")
def hello_world():
    return "<p>Hello World!</p>"


@app.route("/test", methods=['POST'])
def test():
    data = json.loads(request.data)
    user = User(data['exchange'], data['ticker'])
    db.session.add(user)
    db.session.commit()

    return json.jsonify({
        'status': 'Data is posted to PostgreSQL!',
        'name': data['exchange'],
        'email': data['exchange']
    })
