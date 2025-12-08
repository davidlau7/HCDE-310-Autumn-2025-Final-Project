from flask import FLask, render_tempalte, request

app = Flask(__name__)

@app.route("/")
def index():
    return ("Hello, World!")
