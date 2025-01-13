from __future__ import annotations
from copy import deepcopy
from asyncio import sleep

# Textual imports
from rich.text import Text
from textual import work, on
from textual.worker import Worker, WorkerState
from textual.message import Message
from textual.widget import Widget

# TextualGames imports
from textual_games.enums import PlayerState, GridGravity
from textual_games.game import GameBase

class GameManager(Widget):

    class ChangeTurn(Message):
        """Posted by `start_game`, `cell_pressed`, and `computer_turn_orch` in GameManager. \n
        Handled by `change_turn` in TextualGames."""
        def __init__(self, value: PlayerState):
            super().__init__()
            self.value = value

    class ComputerMove(Message):
        """Posted by `computer_turn_orch` when the AI has chosen a move. \n
        Handled by: `play_computer_move` in TextualGames class."""
        def __init__(self, row: int, col: int):
            super().__init__()
            self.row = row
            self.col = col

    class GameOver(Message):
        """Posted by: `cell_pressed` and `computer_turn_orch` in GameManager. \n
        Handled by `game_over` in TextualGames."""
        def __init__(self, result: PlayerState):
            super().__init__()
            self.result = result


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display = False
        self.game_running = False
    
    #* Called by: `mount_grid` and `restart` in TicTacToe.
    def start_game(self, event: GameBase.StartGame):

        self.game_running = True
        self.game = event.game       #! This is not currently used, but could be useful for future features.
        self.rows = event.rows          # right now things are mostly decoupled.
        self.columns = event.columns
        self.max_depth = event.max_depth
        self.gravity = event.gravity
        self.empty_cells = self.rows*self.columns
        self.int_board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]
        self.move_counter = 0

        self.log(
            "Starting game with settings:\n"
            f"Rows: {self.rows}\n"
            f"Columns: {self.columns}\n"
            f"Max depth: {self.max_depth}\n"
            f"Gravity: {self.gravity}\n"
        )

        self.post_message(self.ChangeTurn(PlayerState.PLAYER1))
        self.notify("Game started", timeout=1.5)

    def end_game(self, game_result: PlayerState):
        self.game_running = False
        self.post_message(self.GameOver(game_result))

    #* Called by: cell_pressed in Grid class
    async def cell_pressed(self, row: int, column: int):
        self.log.info(f"manager Cell pressed: {row}, {column}")

        self.log.info(f"self.game_running: {self.game_running}")

        if self.int_board[row][column] != 0:
            self.notify("Cell already taken", timeout=1)
            return
        if not self.game_running:
            return

        self.int_board[row][column] = 1
        self.move_counter += 1
        self.empty_cells -= 1
        game_result = self.app.calculate_winner(self.int_board)
        if game_result is not None:
            self.end_game(game_result)
            return
    
        self.post_message(self.ChangeTurn(PlayerState.PLAYER2))     # Change turn to AI
        # NOTE: I let the main app call the computer_turn_orch method to ensure the
        # UI is updated before it starts thinking.

    #* Called by: change_turn in main App.
    async def computer_turn_orch(self):

        self.minimax_counter = 0
        self.pruning_counter = 0
        self.depth_limit_counter = 0

        board_copy = deepcopy(self.int_board)
        worker = self.computer_turn_worker(board_copy)
        ai_row, ai_col = await worker.wait()
        if ai_row is None:
            raise ValueError("AI made an invalid move.")

        self.log(
            f"Minimax counter: {self.minimax_counter}\n"
            f"Branches pruned: {self.pruning_counter}\n"
            f"Times depth limit reached: {self.depth_limit_counter}\n"
        )        

        self.int_board[ai_row][ai_col] = 2              # Apply AI move to integer board
        self.move_counter += 1
        self.empty_cells -= 1
        self.post_message(self.ComputerMove(ai_row, ai_col))  # Updates the cell state in the Grid

        game_result = self.app.calculate_winner(self.int_board)
        if game_result is not None:
            self.end_game(game_result)
            return
        
        self.post_message(self.ChangeTurn(PlayerState.PLAYER1))     # Change turn back to human


    def get_possible_moves(self, board: list[list[int]]) -> list[tuple[int, int]]:

        possible_moves = []
        
        if self.gravity == GridGravity.DOWN:
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
        else:
            for row in range(self.rows):
                for col in range(self.columns):
                    if board[row][col] == 0:
                        possible_moves.append((row, col))


        return possible_moves


    @work(thread=True, exit_on_error=False)
    async def computer_turn_worker(self, board: list[list[int]]) -> tuple[int, int]:

        await sleep(0.5)            # Artificial delay to simulate thinking time
        _, best_move = self.minimax(
            board,
            depth=0,                 # always start at depth 0
            is_maximizing=True,      # AI is maximizer
            alpha=float('-inf'),
            beta=float('inf'),
        )   
        return best_move

    def minimax(
        self,
        board: list[list[int]],
        depth: int,
        is_maximizing: bool,
        alpha: float,
        beta: float,
    ) -> tuple[int, tuple[int, int]]:
        """ | Arg           | Description 
            |---------------|---------------------
            | board         | - The current game board state
            | depth         | - Current depth in the game tree
            | is_maximizing | - True if AI's turn (maximizing), False if human's turn (minimizing)

            Returns:
                tuple[int, tuple[int, int]]: best_score, best_move (as tuple of coordinates)"""

        self.minimax_counter += 1

        result = self.app.calculate_winner(board)

        # Base cases: game over scenarios
        if result == PlayerState.PLAYER1:     # Human is minimizer
            return -10 + depth, None
        elif result == PlayerState.PLAYER2:   # AI is maximizer
            return 10 - depth, None
        elif result == PlayerState.EMPTY:     # Draw
            return 0, None

        if depth >= self.max_depth:
            self.depth_limit_counter += 1
            return 0, None
    
        best_move  = (None, None)
        best_score = float('-inf') if is_maximizing else float('inf')
        player     =             2 if is_maximizing else 1

        possible_moves = self.get_possible_moves(board)

        for move in possible_moves:
            row, col = move

            board[row][col] = player
            score, _, = self.minimax(board, depth + 1, not is_maximizing, alpha, beta)
            board[row][col] = 0         # Undo move

            if is_maximizing and score > best_score:
                    best_score = score
                    alpha = max(score, alpha)
                    best_move = (row, col)
            elif not is_maximizing and score < best_score:
                    best_score = score
                    beta = min(score, beta)
                    best_move = (row, col)

            if beta <= alpha:
                self.pruning_counter += 1
                break

        return best_score, best_move

    @on(Worker.StateChanged)
    def worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            self.log(Text(f"Worker {event.worker.name} completed successfully", style="green"))

