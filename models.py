from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

from app import app
db = SQLAlchemy(app)


class Game(db.Model):
  __tablename__ = "game"
  id = db.Column('id', db.Integer, primary_key=True)
  team_id = db.Column('team_id', db.Unicode)
  channel_id = db.Column('channel_id', db.Unicode)
  board_dimensions = db.Column('board_dimensions', db.Integer)
  player1_id = db.Column('player1_id', db.Integer, db.ForeignKey('player.id'))
  player2_id = db.Column('player2_id', db.Integer, db.ForeignKey('player.id'))

  player1 = db.relationship('Player', foreign_keys=player1_id)
  player2 = db.relationship('Player', foreign_keys=player2_id)

  def __init__(self, team_id, channel_id, board_dimensions, player1, player2):
    self.team_id = team_id
    self.channel_id = channel_id
    self.board_dimensions = board_dimensions
    self.player1 = player1
    self.player2 = player2


class Piece(db.Model):
  __tablename__ = "piece"
  id = db.Column('id', db.Integer, primary_key=True)
  x_coord = db.Column('x_coord', db.Integer)
  y_coord = db.Column('y_coord', db.Integer)
  player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
  game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

  player = db.relationship('Player', foreign_keys=player_id)
  game = db.relationship('Game', foreign_keys=game_id)

  def __init__(self, x_coord, y_coord, player, game):
    self.x_coord = x_coord
    self.y_coord = y_coord
    self.player = player
    self.game = game


class Player(db.Model):
  __tablename__ = "player"
  id = db.Column('id', db.Integer, primary_key=True)
  user_id = db.Column('user_id', db.Unicode)
  user_name = db.Column('user_name', db.Unicode)

  def __init__(self, user_id, user_name):
    self.user_id = user_id
    self.user_name = user_name

