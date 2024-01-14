from time import monotonic

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Static


class TimeDisplay(Static):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = (
            self.set_interval(
                1 / 60,
                self.update_time,
                pause=True
                )
            )

    def update_time(self) -> None:
        """Method to update the time to the current time."""
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self):
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self):
        self.update_timer.pause()
        self.total += (monotonic() - self.start_time)
        self.time = self.total

    def reset(self):
        self.time = 0
        self.total = 0


class Stopwatch(Static):
    """A stopwatch widget."""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id
        time_display = self.query_one(TimeDisplay)

        if button_id == "start":
            self.add_class("started")
            time_display.start()
        elif button_id == "stop":
            self.remove_class("started")
            time_display.stop()
        elif button_id == "reset":
            time_display.reset()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay("00:00:00.00")


class StopwatchApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = 'textual_proto.tcss'
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add"),
        ("r", "remove_stopwatch", "Remove"),
        ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=False)
        yield Footer()
        yield ScrollableContainer(
                Stopwatch(), Stopwatch(), Stopwatch(),
                id='timers'
            )

    def action_add_stopwatch(self):
        new_stopwatch = Stopwatch()
        self.query_one('#timers').mount(new_stopwatch)
        new_stopwatch.scroll_visible()

    def action_remove_stopwatch(self):
        timers = self.query('Stopwatch')
        if timers:
            timers.last().remove()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()
