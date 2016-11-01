"""This module contains all the tests for this application."""

from flask_testing import TestCase
import unittest
import json

from app import app, db, api
from app.models import *
from app.api import get_current_board
from app.constants import *


class BaseTestCase(TestCase):
    """A base test case for this application."""

    def create_app(self):
        app.config.from_object('config.TestConfiguration')
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class ApiTests(BaseTestCase):
    """Test cases for the tic-tac-toe API"""

    base_data = dict(
        team_id='T2W2QQW5A',
        channel_id='C2W35PTRV'
    )

    invalid = dict(
        base_data,
        user_id='U2W2V2KL6',
        user_name='michael',
        text='gibberish'
    )

    michael_challenge = dict(
        base_data,
        user_id='U2W2V2KL6',
        user_name='michael',
        text='challenge victoria',
    )

    victoria_accept = dict(
        base_data,
        user_id='U2W2USDLG',
        user_name='victoria',
        text='accept',
    )

    status = dict(
        base_data,
        user_id='U2W2USDLG',
        user_name='victoria',
        text='status',
    )

    michael_move = dict(
        base_data,
        user_id='U2W2V2KL6',
        user_name='michael',
        text='left',
    )

    victoria_move = dict(
        base_data,
        user_id='U2W2USDLG',
        user_name='victoria',
        text='left',
    )

    def test_certificate_verification(self):
        response = self.client.get('/')
        assert response.status_code == 200

    def test_invalid_command(self):
        response = self.client.post('/', data=self.invalid)
        assert response.status_code == 200
        assert response.data == INVALID_COMMAND_ERROR

    def test_challenge_success(self):
        response = self.client.post('/', data=self.michael_challenge)
        assert Team.query.count() == 1
        assert Team.query.first().team_id == 'T2W2QQW5A'
        assert Channel.query.count() == 1
        assert Channel.query.first().channel_id == 'C2W35PTRV'
        assert Challenge.query.count() == 1
        assert Challenge.query.first().opponent_name == 'victoria'

        resp_text = json.loads(response.data)['text']
        assert resp_text == ("michael has challenged victoria to "
                             "a game of tic-tac-toe! Type '/ttt accept' "
                             "to start the game.")

    def test_accept_success(self):
        self.client.post('/', data=self.michael_challenge)
        response = self.client.post('/', data=self.victoria_accept)
        assert Challenge.query.first().expired == True
        assert Game.query.count() == 1
        assert Game.query.first().player1.user_name == 'michael'
        assert Game.query.first().player2.user_name == 'victoria'

        starting_player = Game.query.first().current_player_name
        resp_text = json.loads(response.data)['text']
        assert resp_text == ("victoria has accepted the challenge! "
                             "michael has Xs and victoria has Os. "
                             "{0} has the first turn, good luck!"
                             .format(starting_player))

    def test_challenge_failure(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        response = self.client.post('/', data=self.michael_challenge)
        assert Challenge.query.count() != 2
        assert response.data == CANNOT_CHALLENGE_ERROR

    def test_accept_failure(self):
        response = self.client.post('/', data=self.victoria_accept)
        assert Game.query.count() != 1
        assert response.data == NO_CHALLENGE_ERROR

    def test_get_current_board(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        game = Game.query.first()
        michael = Player.query.filter_by(user_name='michael').first()
        victoria = Player.query.filter_by(user_name='victoria').first()

        db.session.add(Piece(0, 0, michael, game))
        db.session.add(Piece(2, 0, michael, game))
        db.session.add(Piece(1, 1, victoria, game))
        db.session.add(Piece(1, 2, victoria, game))
        db.session.commit()

        board_string = get_current_board(game, game.pieces)
        assert board_string == ("``` X |   |   \n"
                                   "---+---+---\n"
                                   "   | O | O \n"
                                   "---+---+---\n"
                                   " X |   |   ```")

    def test_status_success(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        game = Game.query.first()
        michael = Player.query.filter_by(user_name='michael').first()
        victoria = Player.query.filter_by(user_name='victoria').first()

        db.session.add(Piece(0, 0, michael, game))
        db.session.add(Piece(2, 0, michael, game))
        db.session.add(Piece(1, 1, victoria, game))
        db.session.add(Piece(1, 2, victoria, game))
        db.session.commit()

        board = get_current_board(game, game.pieces)
        response = self.client.post('/', data=self.status)
        resp_text = json.loads(response.data)['text']
        assert resp_text == ("{0} It's {1}'s turn right now."
                             .format(board, game.current_player_name))
        
    def test_status_failure(self):
        response = self.client.post('/', data=self.status)
        assert response.data == NO_ACTIVE_GAME_ERROR

    def test_move_success(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        game = Game.query.first()

        if game.current_player_name == 'michael':
            response = self.client.post('/', data=self.michael_move)
        else:
            response = self.client.post('/', data=self.victoria_move)

        assert game.pieces.count() == 1
        assert game.pieces.first().x_coord == 1
        assert game.pieces.first().y_coord == 0

    def test_move_failure(self):
        response = self.client.post('/', data=self.michael_move)
        assert response.data == NOT_IN_A_GAME_ERROR

    def test_square_already_taken_failure(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        game = Game.query.first()

        if game.current_player_name == 'michael':
            self.client.post('/', data=self.michael_move)
            response = self.client.post('/', data=self.victoria_move)
        else:
            self.client.post('/', data=self.victoria_move)
            response = self.client.post('/', data=self.michael_move)

        assert game.pieces.count() == 1
        assert response.data == SQUARE_TAKEN_ERROR

    def test_not_your_turn_failure(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        game = Game.query.first()

        if game.current_player_name == 'michael':
            response = self.client.post('/', data=self.victoria_move)
        else:
            response = self.client.post('/', data=self.michael_move)

        assert game.pieces.count() == 0
        assert response.data == INCORRECT_TURN_ERROR

    def test_victory(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        game = Game.query.first()
        michael = Player.query.filter_by(user_name='michael').first()
        victoria = Player.query.filter_by(user_name='victoria').first()

        db.session.add(Piece(0, 0, michael, game))
        db.session.add(Piece(2, 0, michael, game))
        db.session.add(Piece(1, 1, victoria, game))
        db.session.add(Piece(1, 2, victoria, game))
        db.session.commit()

        if game.current_player_name == 'michael':
            response = self.client.post('/', data=self.michael_move)
        else:
            response = self.client.post('/', data=self.victoria_move)

        assert game.finished == True

        board = get_current_board(game, game.pieces)
        resp_text = json.loads(response.data)['text']
        assert resp_text == ("{0} {1} has won the game!"
                             .format(board, game.current_player_name))

    def test_draw(self):
        self.client.post('/', data=self.michael_challenge)
        self.client.post('/', data=self.victoria_accept)
        game = Game.query.first()
        michael = Player.query.filter_by(user_name='michael').first()
        victoria = Player.query.filter_by(user_name='victoria').first()

        db.session.add(Piece(0, 0, michael, game))
        db.session.add(Piece(0, 2, michael, game))
        db.session.add(Piece(1, 1, michael, game))
        db.session.add(Piece(2, 1, michael, game))
        db.session.add(Piece(0, 1, victoria, game))
        db.session.add(Piece(1, 2, victoria, game))
        db.session.add(Piece(2, 0, victoria, game))
        db.session.add(Piece(2, 2, victoria, game))

        if game.current_player_name == 'michael':
            response = self.client.post('/', data=self.michael_move)
        else:
            response = self.client.post('/', data=self.victoria_move)

        assert game.finished == True

        board = get_current_board(game, game.pieces)
        resp_text = json.loads(response.data)['text']
        assert resp_text == ("{0} The game ended in a draw!"
                             .format(board))


if __name__ == '__main__':
    unittest.main()
