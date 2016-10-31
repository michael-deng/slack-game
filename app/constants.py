# Game configurations

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

# Errors

INVALID_COMMAND_ERROR = "We can't recognize your command! Type '/ttt help' for a list of possible commands."
CANNOT_CHALLENGE_ERROR = "Someone else is playing right now."
NO_CHALLENGE_ERROR = "No one challenged you."
NO_ACTIVE_GAME_ERROR = "No one is playing right now."
NOT_IN_A_GAME_ERROR = "You're not playing a game right now."
INCORRECT_TURN_ERROR = "It's not your turn right now."
SQUARE_TAKEN_ERROR = "That square is already taken."