#!env/bin/python
from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from flask import make_response

app = Flask(__name__)
# app.config.from_pyfile('config.py')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://michael:mypassword@localhost/game'

@app.route('/', methods=['POST'])
def game_handler():
	System.out.println(request.data)
  return 'woah'

if __name__ == '__main__':
  app.run(debug=True)