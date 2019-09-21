from flask import render_template, request
from voting_machine import app, db
from voting_machine.models import Vote

@app.route("/")
def home():
    return render_template('home.html')