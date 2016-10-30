from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://michael:mypassword@localhost/game'
db = SQLAlchemy(app)

from app import api, models, constants