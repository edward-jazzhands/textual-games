from enum import Enum

class PlayerState(Enum):
    """The state of a cell in the game. \n
    Can be EMPTY, PLAYER1, or PLAYER2."""
    EMPTY = 0
    PLAYER1 = 1
    PLAYER2 = 2

class GridFocusType(Enum):
    ALL = "all"
    ROWS = "rows"
    COLUMNS = "columns"

class GridGravity(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    NONE = "none"