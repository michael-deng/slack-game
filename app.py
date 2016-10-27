#!env/bin/python
from flask import Flask
from flask import jsonify
from flask import make_response

app = Flask(__name__)

@app.route('/', methods=['POST'])
def game_handler():
  return 'woah'

if __name__ == '__main__':
    app.run(debug=True)