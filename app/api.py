"""This module receives, processes, and responds to Slack requests."""

from flask import request, jsonify
import random
import os

from app import app
from models import *
from constants import *

@app.route('/', methods=['GET'])
def certificate_verification():
    """Returns a HTTP 200 OK to a certificate verification check"""
    return ('', 200)

@app.route('/', methods=['POST'])
def request_handler():
    """Dispatches different commands to their respective handlers."""
    token = request.form['token']
    if token != os.environ['SLACK_TOKEN']:
        return UNAUTHORIZED_ERROR

    team_id = request.form['team_id']
    channel_id = request.form['channel_id']
    user_id = request.form['user_id']
    user_name = request.form['user_name']
    command = request.form['text']

    command_list = command.split(' ', 1)

    if command_list[0] == "challenge" and len(command_list) == 2:
        opponent = command_list[1]
        if opponent[0] == '@':
            opponent = opponent[1:]
        return handle_challenge(team_id, channel_id, user_id, user_name, opponent)
    elif command == "accept":
        return handle_accept(team_id, channel_id, user_id, user_name)
    elif command == "help":
        return handle_help()
    elif command == "moves":
        return handle_get_moves()
    elif command == "status":
        return handle_status(team_id, channel_id)
    elif command in MOVES:
        (x, y) = MOVES.get(command)
        return handle_move(team_id, channel_id, user_id, user_name, x, y)
    else:
        return INVALID_COMMAND_ERROR

def handle_challenge(team_id, channel_id, user_id, user_name, opponent_name):
    """Initializes a new challenge.

    Creates a new team and a new channel if they are not in the database yet.
    After that, the method generates a new challenge.

    Args:
        team_id: A string representing a Slack team's id
        channel_id: A string representing a Slack channel's id
        user_id: A string representing a Slack user's id
        user_name: A string representing the user's name
        opponent_name: A string representing the user being challenged

    Returns:
        A JSON response containing the details of a challenge. If the
        challenge fails because there is an ongoing game, the method returns
        an error as a string.
    """

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
    resp_text = ("{0} has challenged {1} to a game of tic-tac-toe!\n"
                 "Type `/ttt accept` to start the game."
                 .format(user_name, opponent_name))
    return jsonify({
        "response_type": "in_channel",
        "text": resp_text
    })

def handle_accept(team_id, channel_id, user_id, user_name):
    """Accepts a challenge.

    Creates a new game if the user accepting is the one specified by the 
    most recent challenge.

    Args:
        team_id: A string representing a Slack team's id
        channel_id: A string representing a Slack channel's id
        user_id: A string representing a Slack user's id
        user_name: A string representing the user's name

    Returns:
        A JSON response announcing the start of the game. If the accept fails
        because nobody challenged the player, the method returns an error as
        a string.
    """

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

    starter = random.choice([user_name, challenger.user_name])
    game = Game(BOARD_SIZE, starter, channel, challenger, curr_player)
    db.session.add(game)
    db.session.commit()
    curr_board = get_current_board(game)
    resp_text = ("{0} {1} has accepted the challenge!\n{2} has Xs and {1} has "
                 "Os, {3} has the first turn, good luck!\nHint: `/ttt moves` "
                 "shows you the commands for all possible moves."
                 .format(curr_board, user_name, challenger.user_name, starter))
    return jsonify({
        "response_type": "in_channel",
        "text": resp_text
    })

def handle_help():
    """Returns a list of basic commands."""
    resp_text = ("Play tic-tac-toe in Slack! Here are some basic commands:\n"
                 "`/ttt challenge [someone]` to challenge them to a game\n"
                 "`/ttt accept` to accept a challenge\n"
                 "`/ttt status` to see the condition of the current game\n"
                 "`/ttt moves` to see a list of available moves")
    return jsonify({
        "response_type": "ephemeral",
        "text": resp_text
    })

def handle_get_moves():
    """Returns a list of available moves."""
    resp_text = ("Available moves:\n"
                 "`/ttt topleft` to place a piece in the top left square\n"
                 "`/ttt top` to place a piece in the top square\n"
                 "`/ttt topright` to place a piece in the top right square\n"
                 "`/ttt left` to place a piece in the left square\n"
                 "`/ttt center` to place a piece in the center square\n"
                 "`/ttt right` to place a piece in the right square\n"
                 "`/ttt bottomleft` to place a piece in the bottom left square\n"
                 "`/ttt bottom` to place a piece in the bottom square\n"
                 "`/ttt bottomright` to place a piece in the bottom right square")
    return jsonify({
        "response_type": "ephemeral",
        "text": resp_text
    })

def handle_status(team_id, channel_id):
    """Returns the current game board and whose turn it is.

    Args:
        team_id: A string representing a Slack team's id
        channel_id: A string representing a Slack channel's id

    Returns:
        A JSON response containing the current game board and the player who
        holds the current turn. If there is no game happening, the method
        returns an error as a string.
    """

    team = Team.query.filter_by(team_id=team_id).first()
    if team == None:
        return NO_ACTIVE_GAME_ERROR

    channel = team.channels.filter_by(channel_id=channel_id).first()
    if channel == None:
        return NO_ACTIVE_GAME_ERROR

    most_recent_game = channel.games.order_by(Game.id.desc()).first()
    if most_recent_game == None or most_recent_game.finished:
        return NO_ACTIVE_GAME_ERROR

    curr_board = get_current_board(most_recent_game)
    resp_text = ("{0} It's {1}'s turn right now."
                .format(curr_board, most_recent_game.current_player_name))
    return jsonify({
        "response_type": "ephemeral",
        "text": resp_text
    })

def handle_move(team_id, channel_id, user_id, user_name, x, y):
    """Makes a move and returns the current state of the game.

    Adds a new piece to the board and analyzes if a player has won or if the 
    game ended in a draw.

    Args:
        team_id: A string representing a Slack team's id
        channel_id: A string representing a Slack channel's id
        user_id: A string representing a Slack user's id
        user_name: A string representing the user's name
        x: An integer representing the x coordinate of the new piece
        y: An integer representing the y coordinate of the new piece

    Returns:
        A JSON response containing the updated game board and the player with
        the next turn. If the game has ended, the method will instead announce
        the winning player or that the game ended in a draw. If the move is
        invalid, the method returns an error as a string.
    """

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
    curr_board = get_current_board(most_recent_game)
    if victory(curr_player_pieces):
        most_recent_game.finished = True
        resp_text = "{0} {1} has won the game! :fire:".format(curr_board, user_name)
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

def victory(pieces):
    """Returns whether or not a player has attained victory.

    Converts a list of pieces into a 2D array and analyzes that array to see
    if the pieces are in a winning pattern.

    Args:
        pieces: A list of Piece objects

    Returns:
        A boolean representing whether or not the pieces are in a winning
        configuration.
    """

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

def get_current_board(game):
    """Gets the current game board and returns its string representation.

    Converts the pieces of a game into a 2D array and converts that 2D array
    into a string.

    Args:
        game: A Game object

    Returns:
        A string representing the game board.
    """

    pieces = game.pieces
    board_matrix = [[' ' for i in range(BOARD_SIZE)] for j in range(BOARD_SIZE)]
    for piece in pieces:
        x = piece.x_coord
        y = piece.y_coord
        if piece.player == game.player1:
            board_matrix[x][y] = 'X'
        else:
            board_matrix[x][y] = 'O'

    board_string = "```"
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            board_string += ' '
            board_string += board_matrix[i][j]
            board_string += ' '
            if j != BOARD_SIZE - 1:
                board_string += '|'
        if i != BOARD_SIZE - 1:
            board_string += '\n'
            for k in range(BOARD_SIZE):
                board_string += '---'
                if k != BOARD_SIZE - 1:
                    board_string += '+'
            board_string += '\n'

    board_string += "```"
    return board_string
