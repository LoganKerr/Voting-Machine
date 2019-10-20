from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SECRET_KEY'] = '91d0a0bd5a850edd9983720a5f90e9aa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

from voting_machine.models import Vote, Fingerprint
from voting_machine import routes