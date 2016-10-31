from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app import db

class Game(db.Model):
    __tablename__ = "game"
    id = db.Column('id', db.Integer, primary_key=True)
    board_dimension = db.Column('board_dimension', db.Integer)
    current_player_name = db.Column('current_player', db.String(25))
    finished = db.Column('finished', db.Boolean, default=False)
    channel_id = db.Column('channel_id', db.Integer, db.ForeignKey('channel.id'))
    player1_id = db.Column('player1_id', db.Integer, db.ForeignKey('player.id'))
    player2_id = db.Column('player2_id', db.Integer, db.ForeignKey('player.id'))

    channel = db.relationship(
        'Channel', 
        foreign_keys=channel_id,
        backref=db.backref('games', lazy="dynamic")
    )
    player1 = db.relationship(
        'Player', 
        foreign_keys=player1_id,
        backref=db.backref('games_as_player1', lazy="dynamic")
    )
    player2 = db.relationship(
        'Player', 
        foreign_keys=player2_id,
        backref=db.backref('games_as_player2', lazy="dynamic")
    )

    def __init__(self, board_dimension, current_player_name, channel, player1, player2):
        self.board_dimension = board_dimension
        self.current_player_name = current_player_name
        self.channel = channel
        self.player1 = player1
        self.player2 = player2


class Piece(db.Model):
    __tablename__ = "piece"
    id = db.Column('id', db.Integer, primary_key=True)
    x_coord = db.Column('x_coord', db.Integer, index=True)
    y_coord = db.Column('y_coord', db.Integer, index=True)
    player_id = db.Column('player_id', db.Integer, db.ForeignKey('player.id'))
    game_id = db.Column('game_id', db.Integer, db.ForeignKey('game.id'))

    player = db.relationship(
        'Player',
        foreign_keys=player_id,
        backref=db.backref('pieces', lazy="dynamic")
    )
    game = db.relationship(
        'Game',
        foreign_keys=game_id,
        backref=db.backref('pieces', lazy="dynamic")
    )

    def __init__(self, x_coord, y_coord, player, game):
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.player = player
        self.game = game


class Player(db.Model):
    __tablename__ = "player"
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.String(20), index=True)
    user_name = db.Column('user_name', db.String(25), index=True)
    channel_id = db.Column('channel_id', db.Integer, db.ForeignKey('channel.id'))

    channel = db.relationship(
        'Channel', 
        foreign_keys=channel_id,
        backref=db.backref('players', lazy="dynamic")
    )

    def __init__(self, user_id, user_name, channel):
        self.user_id = user_id
        self.user_name = user_name
        self.channel = channel


class Challenge(db.Model):
    __tablename__ = "challenge"
    id = db.Column('id', db.Integer, primary_key=True)
    opponent_name = db.Column('opponent_name', db.String(25))
    expired = db.Column('expired', db.Boolean, default=False)
    channel_id = db.Column('channel_id', db.Integer, db.ForeignKey('channel.id'))
    challenger_id = db.Column('challenger_id', db.Integer, db.ForeignKey('player.id'))

    channel = db.relationship(
        'Channel',
        foreign_keys=channel_id,
        backref=db.backref('challenges', lazy="dynamic")
    )
    challenger = db.relationship(
        'Player',
        foreign_keys=challenger_id,
        backref=db.backref('challenges', lazy="dynamic")
    )

    def __init__(self, opponent_name, channel, challenger):
        self.opponent_name = opponent_name
        self.channel = channel
        self.challenger = challenger


class Team(db.Model):
    __tablename__ = "team"
    id = db.Column('id', db.Integer, primary_key=True)
    team_id = db.Column('team_id', db.String(20), index=True)

    def __init__(self, team_id):
        self.team_id = team_id


class Channel(db.Model):
    __tablename__ = "channel"
    id = db.Column('id', db.Integer, primary_key=True)
    channel_id = db.Column('channel_id', db.String(20), index=True)
    team_id = db.Column('team_id', db.Integer, db.ForeignKey('team.id'))

    team = db.relationship(
        'Team',
        foreign_keys=team_id,
        backref=db.backref('channels', lazy="dynamic")
    )

    def __init__(self, channel_id, team):
        self.channel_id = channel_id
        self.team = team

