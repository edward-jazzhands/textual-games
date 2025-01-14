"""Base class for all games. \n"""

# from abc import ABC, abstractmethod
from __future__ import annotations

from textual.message import Message
from textual.widget import Widget

# from textual_games.enums import PlayerState


class GameBase(Widget):

    def validate_interface(game: GameBase):
        """Validates if a game class implements the required contract."""

        required_members = {
            "calculate_winner": "method",
            "game_name": "attribute",
            "restart": "method",
            "get_possible_moves": "method",
            "update_UI_state": "method",
            "clear_focus": "method",
        }
            
        for member, kind in required_members.items():
            try:
                getattr(game, member)
            except AttributeError:
                raise NotImplementedError(f"{game.__name__} must implement {member} ({kind}).")

    class StartGame(Message):
        """Posted when a game is either mounted or restarted. \n
        Handled by start_game in TextualGames class."""

        def __init__(
                self,
                game: GameBase,
                rows: int,
                columns: int,
                max_depth: int,
            ):
            super().__init__()
            self.game = game
            self.rows = rows
            self.columns = columns
            self.max_depth = max_depth

