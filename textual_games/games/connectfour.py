"""Connect Four game script for TextualGames"""

from __future__ import annotations

# Textual imports
from textual.app import on
from textual.containers import Container, Horizontal
from textual.widgets import Button

from textual_games.game import GameBase
from textual_games.grid import Grid, GridFocusType, GridGravity
from textual_games.enums import PlayerState


def loader():
    """Required function that returns the game's main widget"""
    return ConnectFour
        

class ConnectFour(GameBase):

    game_name = "Connect Four"

    def compose(self):

        focus_mode = GridFocusType.COLUMNS      # This BS is necessary because intellisense wouldn't work
        gravity = GridGravity.DOWN              # properly if I tried inserting it down there directly.

        self.grid = Grid(
            rows=6,
            columns=7,
            grid_width=50,
            grid_height=19,
            grid_gutter=0, 
            player1_color="red",
            player2_color="yellow",
            cell_size=3,
            focus_mode=focus_mode,
            gravity=gravity,
            classes="grid onefr"
        )        

        with Container(id="content", classes="onefr centered"):
            yield self.grid
        with Horizontal(classes="centered wide footer"):
            yield Button("Restart", id="restart", classes="centered")

    async def on_mount(self):
        self.restart()

    @on(Button.Pressed, "#restart")
    def restart(self):
        self.grid.restart_grid()
        self.post_message(self.StartGame(
            game = self,
            rows = 6,
            columns = 7,
            max_depth = 7,
            gravity=GridGravity.DOWN
        ))

    #* Called by: calculate_winner in TextualGames class.
    def calculate_winner(self, board: list[list[int]]) -> PlayerState | None:
        """Returns a PlayerState if the game is over, else returns None."""

        rows = len(board)
        cols = len(board[0])
        streak_to_win = 4

        lines = []                           # Pre-calculate all possible lines
        lines.extend(board)                                                                 # Add all rows
        lines.extend([[board[row][col] for row in range(rows)] for col in range(cols)])     # Add all columns

        for row in range(rows):              # Add all diagonals (main and anti)
            for col in range(cols):

                # Main diagonal (top-left to bottom-right)
                if row <= rows - streak_to_win and col <= cols - streak_to_win:
                    lines.append([board[row + i][col + i] for i in range(streak_to_win)])
                
                # Anti-diagonal (top-right to bottom-left)
                if row <= rows - streak_to_win and col >= streak_to_win - 1:
                    lines.append([board[row + i][col - i] for i in range(streak_to_win)])

        def check_line(line: list[int], player: int) -> bool:
            """Checks if a line contains 4 consecutive pieces of the same player."""
            count = 0
            for cell in line:
                count = count + 1 if cell == player else 0
                if count == streak_to_win:
                    return True
            return False
    
        for player in (1, 2):
            if any(check_line(line, player) for line in lines):     # Check for winner
                return PlayerState.PLAYER1 if player == 1 else PlayerState.PLAYER2

        if all(cell != 0 for row in board for cell in row):         # Check for draw
            return PlayerState.EMPTY

        return None         # game not over yet

