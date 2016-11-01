"""This module defines the constants used throughout the application."""

BOARD_SIZE = 3

MOVES = {
    "topleft": (0, 0),
    "top": (0, 1),
    "topright": (0, 2),
    "left": (1, 0),
    "center": (1, 1),
    "right": (1, 2),
    "bottomleft": (2, 0),
    "bottom": (2, 1),
    "bottomright": (2, 2)
}

UNAUTHORIZED_ERROR = "You are not authorized to use this application."
INVALID_COMMAND_ERROR = ("Oh no! We can't recognize your command! Try typing "
                         "`/ttt challenge [user]` to challenge someone to a "
                         "game. You can also type `/ttt help` for more help.")
CANNOT_CHALLENGE_ERROR = ("Someone else is playing right now. Wait a bit and "
                          "try again!")
NO_CHALLENGE_ERROR = ("No one challenged you. Don't be sad, challenge "
                      "someone else!")
NO_ACTIVE_GAME_ERROR = "No one is playing right now."
NOT_IN_A_GAME_ERROR = ("You're not playing a game right now. Challenge "
                       "someone to start a new game!")
INCORRECT_TURN_ERROR = "Wait for your turn!"
SQUARE_TAKEN_ERROR = "That square is already taken. Try an open one!"