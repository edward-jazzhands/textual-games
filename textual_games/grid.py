from __future__ import annotations

# from rich.text import Text
from textual import on
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from textual.message import Message
from textual.binding import Binding

from textual_games.source_decorator import called_by
from textual_games.enums import PlayerState, GridFocusMode
from textual_games.manager import GameManager

class Cell(Static):

    state = reactive(PlayerState.EMPTY)
    """This is modified by `cell_pressed` method in the GameManager class
    whenever a move is chosen by either the player or the computer."""

    class Pressed(Message):
        """Posted by: `on_click` in Cell. \n
        Handled by: `cell_pressed` in TextualGames."""
        def __init__(self, cell: Cell):
            super().__init__()
            self.cell = cell

    class HoverEnter(Message):
        def __init__(self, cell: Cell) -> None:
            self.cell = cell
            """The cell that was entered (hovered over)."""
            super().__init__()

    def __init__(
            self,
            row: int,
            column: int,
            cell_size: int,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
        ):
        """ | Arg     | Description 
            |---------|-------------
            | row     | - The row of the cell
            | column  | - The column of the cell
            | name    | - The name of the widget
            | id      | - The ID of the widget in the DOM
            | classes | - The CSS classes for the widget """
            
        super().__init__(name=name, id=id, classes=classes)
        self.row = row
        self.column = column
        self.styles.width = (cell_size * 2)+1  # width of double the height makes a square (roughly) in monospace
        self.styles.height = cell_size

    def render(self):

        if self.state == PlayerState.PLAYER1:
            return self.parent.player1_token
        elif self.state == PlayerState.PLAYER2:
            return self.parent.player2_token
        else:
            return ""
        
    def watch_state(self, value):

        if self.parent.player1_color and self.parent.player2_color:
            if value == PlayerState.PLAYER1:
                self.set_class(True, 'red')
            elif value == PlayerState.PLAYER2:
                self.set_class(True, 'yellow')
            else:
                self.set_class(False, 'red', 'yellow')

    def watch_mouse_hover(self, value: bool) -> None:
        """OVERRIDE: Update from CSS if mouse over state changes.
        Textual addition: posts HoverEnter message."""

        if self._has_hover_style:
            self._update_styles()
        if value:
            self.post_message(self.HoverEnter(self))

    def on_click(self):
        self.post_message(self.Pressed(self))


class Grid(Widget):

    #* Handled by: cell_chosen in TextualGames class.
    class CellChosen(Message):
        def __init__(self, row: int, column: int):
            super().__init__()
            self.row = row
            self.column = column

    #* Sent by: action_restart in Grid class.
    #* Handled by: restart in the Game class that uses the grid.
    class RestartGame(Message):
        pass

    BINDINGS = [
        Binding("left", "left", "Move left"),
        Binding("right", "right", "Move right"),
        Binding("up", "up", "Move up"),
        Binding("down", "down", "Move down"),
        Binding("enter", "select", "Select"),
        Binding("r", "restart", "Restart"),
    ]

    # focus_grid: reactive[list[list[int]]] = reactive([])        # 2d list
    focus_string: str = reactive("")

    def __init__(
            self,
            rows: int,
            columns: int,
            grid_width: int,
            grid_height: int,
            cell_size: int,
            grid_gutter: int = 1,
            player1_token: str = '',
            player2_token: str = '',
            player1_color: str | None = None,
            player2_color: str | None = None,
            focus_mode: GridFocusMode = GridFocusMode.ALL,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
        ):  #! TODO update docstring VVV
        """ | Arg             | Description 
            |-----------------|-------------
            | rows            | - The number of rows in the grid
            | columns         | - The number of columns in the grid
            | grid_width      | - The width of the grid
            | grid_height     | - The height of the grid
            | cell_size       | - The size of each cell
            | grid_gutter     | - The space between cells
            | player1_token   | - The token for player 1
            | player2_token   | - The token for player 2
            | player1_color   | - The color of player 1's token
            | player2_color   | - The color of player 2's token
            | focus_mode      | - The direction of focus
            | name            | - The name of the widget
            | id              | - The ID of the widget in the DOM
            | classes         | - The CSS classes for the widget """
        
        super().__init__(name=name, id=id, classes=classes)
        self.rows:      int = rows
        self.columns:   int = columns
        self.cell_size: int = cell_size
        self.player1_token: str = player1_token
        self.player2_token: str = player2_token
        self.player1_color: str = player1_color
        self.player2_color: str = player2_color
        self.focus_mode: GridFocusMode = focus_mode

        self.styles.grid_size_rows = self.rows
        self.styles.grid_size_columns = self.columns
        self.styles.grid_gutter_vertical = grid_gutter
        self.styles.grid_gutter_horizontal = grid_gutter
        self.styles.width = grid_width
        self.styles.height = grid_height

        #! CHANGE FOCUS GRID TO REACTIVE. MODEL/VIEW PATTERN.

    def compose(self):

        for row in range(self.rows):
            for col in range(self.columns):
                yield Cell(
                    row = row,
                    column = col,
                    cell_size = self.cell_size,
                    id = f"cell_{row}_{col}",
                    classes = "gridcell bordered centered"
                )

    #* Called by: game_over in TextualGames class.
    def clear_focus(self):
        "Disables focus on the grid and removes the focusing class from all cells."

        self.can_focus = False
        for cell in self.query_children(Cell):
            cell.remove_class("focusing")
        self.focus_string = "0" * (self.rows * self.columns)

    #* Called by: restart in TextualGames class. Used by games to both start and restart.
    def restart_grid(self):
        "Clears the grid, re-enables focus, and focuses cell (0,0)"
        self.log.debug("Restarting grid...")

        for cell in self.query_children(Cell):
            cell.state = PlayerState.EMPTY
        self.focus_string = "0" * (self.rows * self.columns)
        self.can_focus = True
        self.focus()
        self.focus_cell(0, 0) 

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:  
        """Check if an action may run."""
        if action == "up" or action == "down":
            if self.focus_mode == GridFocusMode.POSSIBLE_MOVES:
                return False
        return True

    @on(Cell.Pressed)
    def action_select(self):
        self.log.debug("Action: Select")
        row_index, col_index = self.string_to_coordinates(self.focus_string)
        self.post_message(self.CellChosen(row_index, col_index))

    #* Called by: update_UI_state in the current_game
    def update_grid(self, event: GameManager.UpdateGameState):
        self.query_one(f"#cell_{event.row}_{event.column}").state = PlayerState.PLAYER1


    def action_app_focus(self):
        self.app.action_focus_next()

    def action_restart(self):
        self.log.debug("Action: Restart")
        self.post_message(self.RestartGame())


    ###~ Grid Focusing System ~###

    #* Movement:
    # --------------

    @on(Cell.HoverEnter)
    def cell_hovered(self, event: Cell.HoverEnter):
        self.log.debug(f"cell_hovered in Grid: {event.cell.row}, {event.cell.column}")
        if not self.can_focus:
            self.log.debug("Cell hovered cannot focus")
            return
        self.focus_cell(event.cell.row, event.cell.column)   

    def action_left(self):
        self.log.debug("Action: Left")
        self.refresh_bindings()
        row_index, col_index = self.string_to_coordinates(self.focus_string)
        self.focus_cell(
            row_index, (col_index-1 if col_index != 0 else self.columns-1)
        ) # subtract 1 if not first column, else go to last column

    def action_right(self):
        self.log.debug("Action: Right")
        self.refresh_bindings()
        row_index, col_index = self.string_to_coordinates(self.focus_string)
        self.focus_cell(
            row_index, (col_index+1 if col_index != self.columns-1 else 0)
        ) # add 1 if not last column, else go to first column

    def action_up(self):
        self.log.debug("Action: Up")
        self.refresh_bindings()
        row_index, col_index = self.string_to_coordinates(self.focus_string)
        self.focus_cell(
            (row_index-1 if row_index != 0 else self.rows-1), col_index
        ) # subtract 1 if not first row, else go to last row

    def action_down(self):
        self.log.debug("Action: Down")
        self.refresh_bindings()
        row_index, col_index = self.string_to_coordinates(self.focus_string)
        self.focus_cell(
            (row_index+1 if row_index != self.rows-1 else 0), col_index
        ) # add 1 if not last row, else go to first row

    #* Logic:
    # --------------

    def watch_focus_string(self, old: str, new: str):
        """Using the model/view pattern, this method watches the focus_grid and updates the UI accordingly."""

        old_row, old_col = self.string_to_coordinates(old)
        new_row, new_col = self.string_to_coordinates(new)

        self.log.debug(
            f"Old string: {old} \n"
            f"old_row: {old_row}, old_col: {old_col} \n"
            f"New string: {new} \n"
            f"new_row: {new_row}, new_col: {new_col}"
        )

        if old_row is not None and old_col is not None:
            self.query_one(f"#cell_{old_row}_{old_col}").remove_class("focusing")
        if new_row is not None and new_col is not None:
            self.query_one(f"#cell_{new_row}_{new_col}").add_class("focusing")


    @called_by(restart_grid, cell_hovered,
        action_left, action_right, action_up, action_down)
    def focus_cell(self, row: int, col: int):
        self.log.debug(f"Focus cell in grid: {row}, {col}")

        if self.focus_mode == GridFocusMode.ALL:
            pass    # Default. Do nothing
        
        elif self.focus_mode == GridFocusMode.POSSIBLE_MOVES:

            #! Big change needed: Grid shouldn't let you focus on cells that are taken

            board = self.app.game_manager.get_current_board()
            possible_moves = self.app.current_game.get_possible_moves(board)
            for move in possible_moves:     # each move is tuple of coordinates (0, 0), (2, 3), etc
                if move[1] == col:          # find move that matches current column
                    row = move[0]           # set row to that move

        self.focus_string = self.coordinates_to_string(row, col)

    @called_by(action_select, watch_focus_string,
        action_left, action_right, action_up, action_down)
    def string_to_coordinates(self, string: str) -> tuple[int, int] | tuple[None, None]:

        if '1' in string:
            index = string.index('1')  # Find the index of the '1' in the string
            row = index // self.columns    # Convert index to row
            col = index % self.columns     # Convert index to column
            return row, col
        else:
            return None, None
        
    @called_by(focus_cell)
    def coordinates_to_string(self, row: int, col: int) -> str:

        new_focus = [0] * (self.rows * self.columns)
        new_focus[(row * self.columns) + col] = 1
        return "".join(map(str, new_focus)) 







