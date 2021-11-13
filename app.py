from flask import Flask, json, request

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/test", methods=['POST'])
def test():
    return json.loads(request.data)
