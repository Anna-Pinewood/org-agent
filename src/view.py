import logging
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.theme import Theme
from rich.style import Style
from rich.text import Text
from rich import box

logger = logging.getLogger(__name__)

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "prompt": "bold blue",
    "highlight": "magenta",
})

class CLIView:
    def __init__(self):
        self.console = Console(theme=custom_theme)
        self.active_spinner: Optional[Progress] = None

    def display_message(self, message: str):
        logger.debug(f"Displaying message: {message}")
        panel = Panel(
            message,
            box=box.ROUNDED,
            style="info",
            border_style="bright_blue"
        )
        self.console.print(panel)

    def display_error(self, error: str):
        logger.error(f"Displaying error: {error}")
        panel = Panel(
            Text(f"🚨 {error}", style="error"),
            title="[red]ERROR[/red]",
            border_style="red",
            box=box.HEAVY
        )
        self.console.print(panel)

    def get_input(self, prompt: str = "Enter command") -> str:
        styled_prompt = f"[prompt]❯[/prompt] [highlight]{prompt}[/highlight]"
        user_input = Prompt.ask(styled_prompt)
        logger.debug(f"User input received: {user_input}")
        return user_input

    def start_progress(self, message: str = "Thinking"):
        progress = Progress(
            SpinnerColumn(style="bright_cyan"),
            TextColumn("[bright_cyan]{task.description}"),
            transient=True
        )
        progress.add_task(description=f"🤔 {message}...", total=None)
        progress.start()
        self.active_spinner = progress
        
    def stop_progress(self):
        if self.active_spinner:
            self.active_spinner.stop()
            self.active_spinner = None

    def display_result(self, result: str):
        logger.info(f"Displaying result: {result}")
        panel = Panel(
            Text(f"✨ {result}", style="success"),
            title="[bright_green]Result[/bright_green]",
            subtitle="[bright_green]✓ Complete[/bright_green]",
            border_style="green",
            box=box.DOUBLE
        )
        self.console.print("\n")  # Add some spacing
        self.console.print(panel)
        self.console.print("\n")  # Add some spacing
