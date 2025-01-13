# Textual imports
from rich.spinner import Spinner
from textual.widgets import Static


class SpinnerWidget(Static):
    def __init__(
            self, 
            spinner: str, 
            text: str | None = None, 
            *args, 
            **kwargs
        ):
        super().__init__(*args, **kwargs)
        self._spinner = Spinner(spinner, text)  

    def on_mount(self) -> None:
        self.set_interval(1 / 60, self.update_spinner)

    def update_spinner(self) -> None:
        self.update(self._spinner)


class ScrollingLine(Static):

    def on_mount(self):
        self.counter = 0
        self.max = 3
        self.set_interval(1 / 15, self.asciiscroll)

    def asciiscroll(self):
        asciifoo = (" " * self.counter) + "+" + (" " * ((self.counter - self.max)*-1))
        self.update(asciifoo * (self.screen.size.width//4))
        self.counter += 1
        if self.counter > self.max:
            self.counter = 0
