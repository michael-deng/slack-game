#!env/bin/python

from flask import request
# from flask_sqlalchemy import SQLAlchemy
# from flask import jsonify
# from flask import make_response

from app import app

from models import *
from constants import *

import random

@app.route('/', methods=['POST'])
def request_handler():
    team_id = request.form['team_id']
    channel_id = request.form['channel_id']
    user_id = request.form['user_id']
    user_name = request.form['user_name']
    command = request.form['text']
  
    command_list = command.split(' ', 1)

    if command_list[0] == "challenge" and len(command_list) == 2:
        opponent = command_list[1]
        res = handle_challenge(team_id, channel_id, user_id, user_name, opponent)
    elif command == "accept":
        res = handle_accept(team_id, channel_id, user_id, user_name)
    elif command == "status":
        res = handle_status(team_id, channel_id)
    elif command in MOVES:
        res = handle_move(team_id, channel_id, user_id, user_name, command)
    else:
        res = "We can't recognize your command! Type '/ttt help' for a list of possible commands."
    return res

def handle_challenge(team_id, channel_id, user_id, user_name, opponent):
    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        team = Team(team_id)
        db.session.add(team)

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        channel = Channel(channel_id, team)
        db.session.add(channel)
    
    most_recent_game = channel.games.order_by(Game.id.desc()).first()
    if most_recent_game != None and not most_recent_game.finished:
        return "Someone else is playing right now."

    player = channel.players.filter_by(user_id=user_id).first()
    if player == None:
        player = Player(user_id, user_name, channel)
        db.session.add(player)
    
    challenge = Challenge(opponent, channel, player)
    db.session.add(challenge)
    db.session.commit()
    return ("{0} has challenged {1} to a game of tic-tac-toe! If you're {3}, type '/ttt accept' to start the game."
            .format(user_name, opponent, opponent))

def handle_accept(team_id, channel_id, user_id, user_name):
    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        return "You haven't been challenged by anyone."

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        return "You haven't been challenged by anyone."

    most_recent_challenge = channel.challenges.order_by(Challenge.id.desc()).first()
    if most_recent_challenge == None or most_recent_challenge.expired or most_recent_challenge.opponent != user_name:
        return "You haven't been challenged by anyone."

    most_recent_challenge.expired = True
    challenger = most_recent_challenge.challenger
    player = channel.players.filter_by(user_id=user_id).first()
    if player == None:
        player = Player(user_id, user_name, channel)
        db.session.add(player)

    starting_player = random.choice([user_name, challenger.user_name])
    game = Game(BOARD_DIMENSION, starting_player, channel, challenger, player)
    db.session.add(game)
    db.session.commit()
    return "{0} has accepted the challenge!".format(starting_player)

def handle_status(team_id, channel_id):
    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        return "No one is playing right now."

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        return "No one is playing right now."

    most_recent_game = channel.games.order_by(Game.id.desc()).first()
    if most_recent_game == None or most_recent_game.finished:
        return "No one is playing right now."

    response = get_current_board(most_recent_game.pieces)
    response += "It's {0}'s turn right now.".format(most_recent_game.current_player)
    return response


def handle_move(team_id, channel_id, user_id, user_name, command):
    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        return "You're not playing a game right now."

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        return "You're not playing a game right now."

    current_player = channel.players.filter_by(user_id=user_id).first()
    most_recent_game = channel.games.order_by(Game.id.desc()).first()
    if most_recent_game.finished or most_recent_game.player1 != current_player or most_recent_game.player2 != current_player:
        return "You're not playing a game right now."

    if most_recent_game.current_player != user_name:
        return "It's not your turn right now."

    pieces = most_recent_game.pieces

    (x_coord, y_coord) = MOVES.get(command)
    if pieces.query.filter_by(x_coord=x_coord, y_coord=y_coord).count() > 0:
        return "This square is already taken."

    new_piece = Piece(x_coord, y_coord, current_player, most_recent_game)
    db.session.add(new_piece)
    pieces.append(new_piece)
    current_player_pieces = pieces.filter_by(player=current_player)

    opponent = most_recent_game.player1 if current_player == most_recent_game.player1 else most_recent_game.player2
    most_recent_game.current_player = opponent.user_name

    current_player_won = check_player_won(current_player_pieces, current_player)
    response = get_current_board(pieces)
    if current_player_won:
        most_recent_game.finished = True
        response += "{0} has won the game!".format(user_name)
    else:
        response += "{0} has made a move, now it's {1}'s turn.".format(user_name, opponent.name)

    db.session.commit()
    return response
        


def check_player_won(pieces, player):
    board = [[0 for i in range(BOARD_DIMENSION)] for j in range(BOARD_DIMENSION)]
    for piece in pieces:
        x = piece.x_coord
        y = piece.y_coord
        board[x][y] = 1

    for i in range(BOARD_DIMENSION):
        horizontal = 0
        vertical = 0
        for j in range(BOARD_DIMENSION):
            if board[i][j] == 1:
                horizontal += 1
            if board[j][i] == 1:
                vertical += 1
        if horizontal == 3 or vertical == 3:
            return True

    diagonal1 = 0
    diagonal2 = 0
    for k in range(BOARD_DIMENSION):
        if board[k][k] == 1:
            diagonal1_X += 1
        if board[k][BOARD_DIMENSION - k - 1] == 1:
            diagonal2_X += 1
    if diagonal1 == 3 or diagonal2 == 3:
        return True
    return False


def get_current_board(pieces):
    board = [[' ' for i in range(BOARD_DIMENSION)] for j in range(BOARD_DIMENSION)]
    for piece in pieces:
        x = piece.x_coord
        y = piece.y_coord
        if piece.player == most_recent_game.player1:
            board[x][y] = 'X'
        else:
            board[x][y] = 'O'
    # return board

    board_string = "```"

    for i in range(BOARD_DIMENSION):
        for j in range(BOARD_DIMENSION):
            board_string += ' '
            board_string += board[i][j]
            if j != BOARD_DIMENSION - 1:
                board_string += ' |'
        if i != BOARD_DIMENSION - 1:
            board_string += '\n'
            for k in range(BOARD_DIMENSION):
                board_string += '---'
                if k != BOARD_DIMENSION - 1:
                    board_string += '+'
            board_string += '\n'

    board_string += "```"
    return board_string

