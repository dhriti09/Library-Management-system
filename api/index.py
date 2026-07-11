
from flask import Flask,render_template
app=Flask(__name__,template_folder="../templates",static_folder="../static")
books=["vistas","invention","rich&poor","indian","macroeconomics","microeconomics"]
@app.route("/")
def home():
    return render_template("index.html",books=books)
app=app
