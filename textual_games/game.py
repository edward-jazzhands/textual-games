"""Base class for all games. \n"""

# from abc import ABC, abstractmethod
from __future__ import annotations

from textual.message import Message
from textual.widget import Widget

from textual_games.enums import GridGravity

# from textual_games.enums import PlayerState


class GameBase(Widget):

    class StartGame(Message):
        """Posted when a game is either mounted or restarted. \n
        Handled by start_game in TextualGames class."""

        def __init__(
                self,
                game: GameBase,
                rows: int,
                columns: int,
                max_depth: int,
                gravity: GridGravity = GridGravity.NONE
            ):
            super().__init__()
            self.game = game
            self.rows = rows
            self.columns = columns
            self.max_depth = max_depth
            self.gravity = gravity

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.calculate_winner
        except AttributeError:
            raise NotImplementedError("Game must implement calculate_winner method.")
        
        try:
            self.game_name
        except AttributeError:
            raise NotImplementedError("Game must implement game_name attribute.")
        
        try:
            self.restart
        except AttributeError:
            raise NotImplementedError("Game must implement restart method.")

    # #* Called by: calculate_winner in Main App.
    # def calculate_winner(self, board: list[list[int]]) -> PlayerState | None:
    #     """Returns a PlayerState if game is over, else returns None."""
    #     pass