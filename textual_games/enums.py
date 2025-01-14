from enum import Enum

class PlayerState(Enum):
    """The state of a cell in the game. \n
    Can be EMPTY, PLAYER1, or PLAYER2."""
    EMPTY = 0
    PLAYER1 = 1
    PLAYER2 = 2

class GridFocusMode(Enum):
    ALL = 0
    POSSIBLE_MOVES = 1