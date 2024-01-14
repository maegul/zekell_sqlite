import sys
import string
import random

import flask
from flask import Flask

def lp(msg):
    print(msg, file=sys.stdout)

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/jsontest")
def jsontest():
    resp_content = {'content': ''.join(random.choices(string.ascii_letters, k=10))}
    resp = flask.make_response(
            resp_content
            # {'a': 1, 'b': 2},  # response
        )
    # unsafe!!??
    resp.headers['Access-Control-Allow-Origin'] = '*'

    # resp.headers['crossorigin'] = 'anonymous'
    # lp(resp.headers)

    return resp


