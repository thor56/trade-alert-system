from flask import Flask, json, request, url_for
from flask_sqlalchemy import SQLAlchemy

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE'] = os.environ.get("DATABASE_URL")

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)


db.init_app()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/test", methods=['POST'])
def test():
    data = json.loads(request.data)
    user = User(name=data["exchange"], email=data["ticker"])
    db.session.add(user)
    db.session.commit()
    return data
