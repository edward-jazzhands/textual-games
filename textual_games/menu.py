# from __future__ import annotations
import importlib.util
import os
from typing import Dict, Any, Type, List

# 3rd party imports
from textual_pyfiglet import FigletWidget

# Textual imports
from textual import on, work
from textual.binding import Binding
from textual.app import App, SystemCommand
from textual.screen import Screen
from textual.message import Message
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Label, Static
from textual.dom import DOMNode
from textual.widget import Widget

# TextualGames imports
import textual_games.games as games
from textual_games.source_decorator import called_by
from textual_games.spinner import SpinnerWidget, ScrollingLine
from textual_games.simplebutton import SimpleButton
from textual_games.manager import GameManager
from textual_games.enums import PlayerState
from textual_games.grid import Grid
from textual_games.game import GameBase


class GameEntry(Widget):

    class GameSelected(Message):
        """Posted by: entry_pressed in GameEntry. \n
        Handled by: game_selected in TextualGames."""
        def __init__(self, game_class: Type[Any]):
            super().__init__()
            self.game_class = game_class

    def __init__(self, game_name: str, game_class: Type[Any], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_name = game_name
        self.game_class = game_class

    def compose(self):
        yield SimpleButton(self.game_name, classes="wide centered")

    @on(SimpleButton.Pressed)
    def entry_pressed(self, event: SimpleButton.Pressed):
        self.log.info(f"Pressed: {self.game_name}")
        self.post_message(self.GameSelected(self.game_class))

    def focus(self):
        self.query_one(SimpleButton).focus()


class TextualGames(App):

    CSS_PATH = ["css.tcss"]

    BINDINGS = [
        # Binding("escape", "foo", "Menu", show=True),
        Binding("up", "menu_previous", "Previous"),
        Binding("down", "menu_next", "Next"),
    ]

    # COMMAND_PALETTE_BINDING = "escape"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):

        self.game_manager = GameManager()
        yield self.game_manager

        with Horizontal(id="header", classes="wide header tall"):
            yield FigletWidget("Textual Games", font="small_slant")
        with Horizontal(id="animation_header", classes="h1 wide"):
            yield ScrollingLine(classes="wide")
        with Horizontal(id="turn_header", classes="wide header turnlabel"):
            yield Label(id="turn_label", classes="auto centered")
            yield SpinnerWidget("line", id="spinner", classes="auto centered")
        with Container(id="content", classes="onefr centered"):
            yield Static()
        yield Footer()

    def get_system_commands(self, screen: Screen):
        yield from super().get_system_commands(screen)  
        yield SystemCommand("Main Menu", "Exit game and go back to main menu", self.mount_games_menu)

    def on_mount(self):
        self.call_after_refresh(self.load_games)

    #* Called by: on_mount, directly above.
    async def load_games(self):

        self.content_window = self.query_one("#content")
        self.loader = GameLoader.with_default_games()            # Load only the package's built-in games
        # loader = GameLoader.with_default_games(["/path/to/user/games"])    # Load package and user games
        # loader = GameLoader("/path/to/games", "/path/to/more/games")       # specify directories manually

        games = self.loader.discover_games()
        self.log(games)

        self.all_games = [
            GameEntry(key, value, classes="wide centered") for key, value in games.items()
        ]
        await self.mount_games_menu()

    async def mount_games_menu(self):

        self.game_manager.game_running = False
        await self.content_window.remove_children()
        await self.content_window.mount_all(self.all_games)
        self.query_one("#turn_label").update("")

        self.query_one("#header").display = True
        self.query_one("#animation_header").display = True
        self.query_one("#spinner").visible = False
        self.query_one("#turn_header").display = False
        
        self.content_window.query_one(GameEntry).focus()

    def action_menu_next(self) -> None:
        self.refresh_bindings()
        self.screen.focus_next()

    def action_menu_previous(self) -> None:
        self.refresh_bindings()
        self.screen.focus_previous()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:  
        """Check if an action may run."""
        if action == "menu_next" or action == "menu_previous":
            if self.game_manager.game_running:
                return False
        return True
    
    ###~ Event Handlers ~###

    @called_by(GameEntry.entry_pressed)
    @on(GameEntry.GameSelected)
    def game_selected(self, event: GameEntry.GameSelected):

        self.log.info(f"game_selected in main app received: {event.game_class}")

        self.content_window.remove_children()
        self.current_game = event.game_class()
        self.content_window.mount(self.current_game)

    #* Called by on_mount or restart in a game widget.
    @on(GameBase.StartGame)
    def start_game(self, event: GameBase.StartGame):
        self.workers.cancel_all()
        self.query_one("#header").display = False
        self.query_one("#animation_header").display = False
        self.query_one("#turn_header").display = True
        self.game_manager.start_game(event)
        self.call_after_refresh(self.query_one(Footer).refresh, recompose=True)


    @called_by(
        GameManager.cell_pressed,
        GameManager.computer_turn_orch,
        GameManager.minimax
    )
    def calculate_winner(self, board: List[List[int]]) -> PlayerState | None:
        """Returns a PlayerState if game is over, else returns None. \n
        Playerstate can be PLAYER1, PLAYER2, or EMPTY. (Empty here means draw/tie game)"""
        # NOTE: This does not use an event because we need it to wait for the result,
        # and turning the whole thing async from top to bottom would be a pain in the ass.

        return self.current_game.calculate_winner(board)

    
    @called_by(
        GameManager.start_game,
        GameManager.cell_pressed, 
        GameManager.computer_turn_orch
    )
    @on(GameManager.ChangeTurn)         
    @work(exit_on_error=False)
    async def change_turn(self, event: GameManager.ChangeTurn):

        # NOTE: The cell_pressed method in GameManger updates the cell state.
        # That state is reactive, so the cell then updates itself with new rendering.
        # This method is only to update the UI before switching control from human <-> computer.
        # Partially out of necessity because it was more responsive / prevented freezing.

        self.log.debug(f"Turn label changing to {event.value.name}")
        if event.value == PlayerState.PLAYER1:
            self.query_one("#spinner").visible = False
            self.query_one("#turn_label").update("Your turn")
        else:
            self.query_one("#spinner").visible = True
            self.query_one("#turn_label").update("Computer is thinking... ")
            await self.game_manager.computer_turn_orch()

    @called_by(GameManager.end_game)
    @on(GameManager.GameOver)           
    def game_over(self, event: GameManager.GameOver):
        
        self.query_one("#spinner").visible = False
        self.notify("Game over", timeout=1.5)
        if event.result == PlayerState.EMPTY:
            self.query_one("#turn_label").update("It's a tie!")
        else:
            self.query_one("#turn_label").update(f"{event.result.name} wins!")

        self.current_game.grid.clear_focus()            #! This is presuming the game uses a grid.
        self.current_game.query_one("#restart").focus() #! This is presuming there's a button with id "restart"

    @called_by(GameManager.computer_turn_orch)
    @on(GameManager.ComputerMove)
    def play_computer_move(self, event: GameManager.ComputerMove):

        # The AI does not send a cell_pressed event because it doesn't click on the cell,
        # So we need to update the cell state manually.

        cell = self.current_game.grid.query_one(f"#cell_{event.row}_{event.col}")
        cell.state = PlayerState.PLAYER2

    @on(Grid.CellChosen)
    async def cell_chosen(self, event: Grid.CellChosen):
        await self.game_manager.cell_pressed(event.row, event.column)

class GameLoader(DOMNode):

    #* Called by: load_games in TextualGames class.
    def __init__(self, *directories: str):
        super().__init__()
        """ Initialize the game loader with one or more game directories. \n
        Args:
            *directories: Variable number of paths to directories containing games
        """
        self.game_directories = list(directories)
        self.loaded_games: Dict[str, Type[Any]] = {}

    @called_by(TextualGames.load_games)
    @classmethod
    def with_default_games(cls, extra_directories: List[str] = None):
        """ Create a GameLoader that includes both package games and optional extra directories. \n
        ### Args:
            extra_directories: Additional game directories to scan
        ### Returns:
            GameLoader: Configured to load both package and user games
        """
        default_path = games.__path__[0]
        
        directories = [default_path]
        if extra_directories:
            directories.extend(extra_directories)
            
        return cls(*directories)

    @called_by(TextualGames.load_games)
    def discover_games(self) -> Dict[str, Type[Any]]:
        """
        Scan all game directories for .py files and attempt to load them.
        Later directories can override games from earlier directories.
        
        Returns:
            Dict[str, Type[Any]]: Dictionary mapping game names to their game classes
        """
        self.loaded_games.clear()
        
        for directory in self.game_directories:
            if not os.path.exists(directory):
                self.log.error(f"ERROR: Games directory not found: {directory}")
                continue
                
            for filename in os.listdir(directory):
                if filename.endswith('.py') and not filename.startswith('__'):
                    scriptname = filename[:-3]
                    try:
                        module_path = os.path.join(directory, filename)
                        spec = importlib.util.spec_from_file_location(scriptname, module_path)
                        if spec is None or spec.loader is None:
                            self.log.error(f"Failed to load spec for game: {scriptname}")
                            continue
                            
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        try:
                            game_class = module.loader()
                        except AttributeError:
                            self.log.warning(f"Game {scriptname} does not have an loader function")
                            continue
                        try:
                            game_name = game_class.game_name
                            self.loaded_games[game_name] = game_class
                        except AttributeError:
                            self.log.warning(f"Game {scriptname} does not have a game_name attribute")
                            continue
                            
                    except Exception as e:
                        self.log.error(f"Error loading game {scriptname}: {str(e)}")
                    
        return self.loaded_games

