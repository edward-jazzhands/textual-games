"""Battleship game script for TextualGames

UNFINISHED"""

from __future__ import annotations

# Textual imports
from textual.app import on
from textual.containers import Container, Horizontal
from textual.widgets import Button

from textual_games.game import GameBase
from textual_games.grid import Grid
from textual_games.enums import PlayerState


# def loader():
#     """Required function that returns the game's main widget"""
#     return Battleship
        

class Battleship(GameBase):

    game_name = "Battleship"

    def compose(self):

        self.grid = Grid(
            rows=6,
            columns=7,
            grid_width=50,
            grid_height=19,
            grid_gutter=0, 
            player1_color="red",
            player2_color="yellow",
            cell_size=3,
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
        ))

    #* Called by: calculate_winner in TextualGames class.
    def calculate_winner(self, board: list[list[int]]) -> PlayerState | None:
        """Returns a PlayerState if the game is over, else returns None."""

        pass

