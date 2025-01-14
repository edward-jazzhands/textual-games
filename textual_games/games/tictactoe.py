"""Tic-Tac-Toe game script for TextualGames"""

# Textual imports
# from textual.app import on
from textual.containers import Container
# from textual.widgets import Button

# TextualGames imports
from textual_games.game import GameBase
from textual_games.grid import Grid
from textual_games.enums import PlayerState

# NOTE: whitespace is important here:
x_token = r"""
 \_/ 
 / \ """
o_token = r"""  __ 
 /  \
 \__/"""

def loader():
    """Required function that returns the game's main widget"""
    return TicTacToe

        
class TicTacToe(GameBase):

    game_name = "Tic-Tac-Toe"

    def compose(self):

        self.rows = 3
        self.columns = 3
        
        self.grid = Grid(
            rows=self.rows,
            columns=self.columns,
            grid_width=34,          # NOTE: The sizes and formatting can be tricky to get perfect, so I've
            grid_height=18,         # decided its easiest to make each game enter the grid size and cell size manually.
            grid_gutter=0,              # If writing a game, you'll need to just play with these numbers until 
            player1_token=x_token,      # everything looks exactly the way you'd like.
            player2_token=o_token,      
            cell_size=5,            # <- nice big cells for Tic-Tac-Toe
            classes="grid onefr"
        )

        with Container(id="content", classes="onefr centered"):
            yield self.grid


    async def on_mount(self):
        self.post_message(self.StartGame(
            game = self,
            rows = self.rows,
            columns = self.columns,
            max_depth = 9
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

        possible_moves = []
        
        for row in range(self.rows):
            for col in range(self.columns):
                if board[row][col] == 0:
                    possible_moves.append((row, col))

        return possible_moves

    #* Called by: calculate_winner in TextualGames class.
    def calculate_winner(self, board: list[list[int]]) -> PlayerState | None:
        """Returns a PlayerState if game is over, else returns None."""

        rows      = board
        columns   = list(zip(*board))
        main_diag = [[board[i][i] for i in range(self.rows)]]
        anti_diag = [[board[i][self.columns - i - 1] for i in range(self.rows)]]

        # Combine all possible lines into a single list
        lines = (rows + columns + main_diag + anti_diag)

        def check_line(line, player):
            return all(cell == player for cell in line)
        
        for player in (1, 2):
            if any(check_line(line, player) for line in lines):     # Check for winner
                return PlayerState.PLAYER1 if player == 1 else PlayerState.PLAYER2

        if all(cell != 0 for row in board for cell in row):         # Check for draw
            return PlayerState.EMPTY
        
        return None        # game not over yet