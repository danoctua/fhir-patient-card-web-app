from flask import Flask, render_template, url_for, request
from tools import *

app = Flask(__name__)

@app.route("/")
def main_page():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)