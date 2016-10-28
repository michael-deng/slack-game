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
def request_handler():
  team_id = request.form['team_id']
  channel_id = request.form['channel_id']
  user_id = request.form['user_id']
  user_name = request.form['user_name']
  text = request.form['text']
  
  text_list = text.split(' ', 1)
  
  return 'woah'

if __name__ == '__main__':
  app.run(debug=True)