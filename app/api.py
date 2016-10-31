#!env/bin/python

from flask import request, jsonify
import random
# from flask import make_response

from app import app
from models import *
from constants import *

@app.route('/', methods=['POST'])
def request_handler():
    team_id = request.form['team_id']
    channel_id = request.form['channel_id']
    user_id = request.form['user_id']
    user_name = request.form['user_name']
    command = request.form['text']

    command_list = command.split(' ', 1)

    if command_list[0] == "challenge" and len(command_list) == 2:
        opponent_name = command_list[1]
        return handle_challenge(team_id, channel_id, user_id, user_name, opponent_name)
    elif command == "accept":
        return handle_accept(team_id, channel_id, user_id, user_name)
    elif command == "status":
        return handle_status(team_id, channel_id)
    elif command in MOVES:
        (x, y) = MOVES.get(command)
        return handle_move(team_id, channel_id, user_id, user_name, x, y)
    else:
        return INVALID_COMMAND_ERROR

def handle_challenge(team_id, channel_id, user_id, user_name, opponent_name):
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
        return CANNOT_CHALLENGE_ERROR

    curr_player = channel.players.filter_by(user_id=user_id).first()
    if curr_player == None:
        curr_player = Player(user_id, user_name, channel)
        db.session.add(curr_player)
    
    challenge = Challenge(opponent_name, channel, curr_player)
    db.session.add(challenge)
    db.session.commit()
    resp_text = ("{0} has challenged {1} to a game of tic-tac-toe! "
                 "Type '/ttt accept' to start the game."
                 .format(user_name, opponent_name))
    return jsonify({
        "response_type": "in_channel",
        "text": resp_text
    })

def handle_accept(team_id, channel_id, user_id, user_name):
    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        return NO_CHALLENGE_ERROR

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        return NO_CHALLENGE_ERROR

    challenges = channel.challenges
    most_recent_challenge = challenges.order_by(Challenge.id.desc()).first()
    if (most_recent_challenge == None or 
            most_recent_challenge.expired or 
            most_recent_challenge.opponent_name != user_name):
        return NO_CHALLENGE_ERROR

    most_recent_challenge.expired = True
    challenger = most_recent_challenge.challenger
    curr_player = channel.players.filter_by(user_id=user_id).first()
    if curr_player == None:
        curr_player = Player(user_id, user_name, channel)
        db.session.add(curr_player)

    starting_player = random.choice([user_name, challenger.user_name])
    game = Game(BOARD_SIZE, starting_player, channel, challenger, curr_player)
    db.session.add(game)
    db.session.commit()
    resp_text = ("{0} has accepted the challenge! {1} has Xs and {0} has Os. "
                 "{3} has the first turn, good luck!"
                 .format(user_name, challenger.user_name, starting_player))
    return jsonify({
        "response_type": "in_channel",
        "text": resp_text
    })

def handle_status(team_id, channel_id):
    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        return NO_ACTIVE_GAME_ERROR

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        return NO_ACTIVE_GAME_ERROR

    most_recent_game = channel.games.order_by(Game.id.desc()).first()
    if most_recent_game == None or most_recent_game.finished:
        return NO_ACTIVE_GAME_ERROR

    curr_board = get_current_board(most_recent_game, most_recent_game.pieces)
    resp_text = ("{0} It's {1}'s turn right now."
                .format(curr_board, most_recent_game.current_player_name))
    return jsonify({
        "response_type": "in_channel",
        "text": resp_text
    })

def handle_move(team_id, channel_id, user_id, user_name, x, y):
    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        return NOT_IN_A_GAME_ERROR

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        return NOT_IN_A_GAME_ERROR

    curr_player = channel.players.filter_by(user_id=user_id).first()
    most_recent_game = channel.games.order_by(Game.id.desc()).first()
    if (most_recent_game == None or 
            most_recent_game.finished or 
            (most_recent_game.player1 != curr_player and 
                most_recent_game.player2 != curr_player)):
        return NOT_IN_A_GAME_ERROR
    if most_recent_game.current_player_name != user_name:
        return INCORRECT_TURN_ERROR

    pieces = most_recent_game.pieces
    if pieces.filter_by(x_coord=x, y_coord=y).count() > 0:
        return SQUARE_TAKEN_ERROR

    new_piece = Piece(x, y, curr_player, most_recent_game)
    db.session.add(new_piece)
    
    curr_player_pieces = pieces.filter_by(player=curr_player)
    curr_board = get_current_board(most_recent_game, pieces)
    if current_player_won(curr_player_pieces):
        most_recent_game.finished = True
        resp_text = "{0} {1} has won the game!".format(curr_board, user_name)
    elif pieces.count() == BOARD_SIZE * BOARD_SIZE:
        most_recent_game.finished = True
        resp_text = "{0} The game ended in a draw!".format(curr_board)
    else:
        player1 = most_recent_game.player1
        player2 = most_recent_game.player2
        opponent = player1 if curr_player == player2 else player2
        most_recent_game.current_player_name = opponent.user_name
        resp_text = ("{0} {1} has made a move, now it's {2}'s turn."
                    .format(curr_board, user_name, opponent.user_name))

    db.session.commit()
    return jsonify({
        "response_type": "in_channel",
        "text": resp_text
    })

def current_player_won(pieces):
    board = [[0 for i in range(BOARD_SIZE)] for j in range(BOARD_SIZE)]
    for piece in pieces:
        x = piece.x_coord
        y = piece.y_coord
        board[x][y] = 1

    diagonal1 = 0
    diagonal2 = 0
    for i in range(BOARD_SIZE):
        horizontal = 0
        vertical = 0
        for j in range(BOARD_SIZE):
            if board[i][j] == 1:
                horizontal += 1
            if board[j][i] == 1:
                vertical += 1
        if horizontal == BOARD_SIZE or vertical == BOARD_SIZE:
            return True
        if board[i][i] == 1:
            diagonal1 += 1
        if board[i][BOARD_SIZE - i - 1] == 1:
            diagonal2 += 1
    if diagonal1 == BOARD_SIZE or diagonal2 == BOARD_SIZE:
        return True
    return False

def get_current_board(game, pieces):
    board = [[' ' for i in range(BOARD_SIZE)] for j in range(BOARD_SIZE)]
    for piece in pieces:
        x = piece.x_coord
        y = piece.y_coord
        if piece.player == game.player1:
            board[x][y] = 'X'
        else:
            board[x][y] = 'O'

    board_string = "```"
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            board_string += ' '
            board_string += board[i][j]
            if j != BOARD_SIZE - 1:
                board_string += ' |'
        if i != BOARD_SIZE - 1:
            board_string += '\n'
            for k in range(BOARD_SIZE):
                board_string += '---'
                if k != BOARD_SIZE - 1:
                    board_string += '+'
            board_string += '\n'

    board_string += "```"
    return board_string

