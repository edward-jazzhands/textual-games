"""Connect Four game script for TextualGames"""

from __future__ import annotations

# Textual imports
from textual.app import on
from textual.containers import Container, Horizontal
from textual.widgets import Button

from textual_games.game import GameBase
from textual_games.grid import Grid, GridFocusMode
from textual_games.enums import PlayerState


def loader():
    """Required function that returns the game's main widget"""
    return ConnectFour
        

class ConnectFour(GameBase):

    game_name = "Connect Four"

    def compose(self):

        self.rows = 6
        self.columns = 7
        focus_mode = GridFocusMode.POSSIBLE_MOVES   # intellisense wont work if inserting it down there directly.

        self.grid = Grid(
            rows=self.rows,
            columns=self.columns,
            grid_width=50,
            grid_height=19,
            grid_gutter=0, 
            player1_color="red",
            player2_color="yellow",
            cell_size=3,
            focus_mode=focus_mode,
            classes="grid onefr"
        )        

        with Container(id="content", classes="onefr centered"):
            yield self.grid

    def on_mount(self):
        self.post_message(self.StartGame(
            game = self,
            rows = self.rows,
            columns = self.columns,
            max_depth = 7,
        ))

    #* Called by TextualGames.start_game, TextualGames.restart
    def restart(self):
        self.grid.restart_grid()

    #* Called by: TextualGames.update_board
    def update_UI_state(self, event):
        self.grid.update_grid(event)

    #* Called by: game_over in TextualGames class.
    def clear_focus(self):
        self.grid.clear_focus()


    # NOTE: This will run in a thread when called by minimax
    #* Called by GameManager.minimax, Grid.focus_cell
    def get_possible_moves(self, board) -> list[tuple[int, int]]:
        """Returns a list of tuples representing coordinates of empty cells."""

        possible_moves = []

        # This system here basically represents gravity.
        for col in range(self.columns):
            for row in range(self.rows):
                if row != self.rows-1:                      # if not last row:
                    if board[row+1][col] == 0:         # is row below empty?
                        continue
                    else:
                        if board[row][col] == 0:
                            possible_moves.append((row, col))
                        break
                else:                                    
                    possible_moves.append((row, col))       # it should only get here if column is empty

        return possible_moves

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

