from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello people of AWS Women! v1.0.0"