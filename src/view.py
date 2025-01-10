import logging
from datetime import datetime
from typing import Optional, Dict
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.theme import Theme
from rich.style import Style
from rich.text import Text
from rich.logging import RichHandler
from rich import box
import sys

logger = logging.getLogger(__name__)

# Enhanced theme with logging colors
custom_theme = Theme({
    "info": "bright_cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "prompt": "bold blue",
    "highlight": "magenta",
    "timestamp": "dim cyan",
    "logger_name": "bright_blue",
    "message": "bright_white",
    "level.debug": "dim cyan",
    "level.info": "bright_green",
    "level.warning": "bright_yellow",
    "level.error": "bold red",
    "level.critical": "bold red reverse",
})


class RichLogHandler(RichHandler):
    """Custom Rich log handler with enhanced formatting and colors."""

    def __init__(self, console: Optional[Console] = None, **kwargs):
        """
        Initialize the Rich log handler with custom formatting.

        Args:
            console: Optional Rich console instance. If not provided, creates new one.
            **kwargs: Additional arguments passed to RichHandler.
        """
        self.log_colors: Dict[str, str] = {
            "DEBUG": "[level.debug]",
            "INFO": "[level.info]",
            "WARNING": "[level.warning]",
            "ERROR": "[level.error]",
            "CRITICAL": "[level.critical]"
        }

        super().__init__(
            console=console or Console(theme=custom_theme),
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=False,  # We'll handle time formatting ourselves
            show_level=False,  # We'll handle level formatting ourselves
            show_path=False,  # We'll handle this in our format
            **kwargs
        )

    def render(
        self,
        record: logging.LogRecord,
        traceback: Optional[Text] = None,
        message_renderable: Optional[Text] = None
    ) -> Text:
        """
        Render a log record with custom formatting and colors.

        Args:
            record: The LogRecord instance
            message: The formatted log message

        Returns:
            Text: Rich Text object with formatted log message
        """
        time_format = datetime.fromtimestamp(
            record.created).strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

        # Build the log message with custom formatting
        log_text = Text()

        # Add timestamp
        log_text.append(f"{time_format}", style="timestamp")
        log_text.append(" - ")

        # Add logger name
        log_text.append(f"{record.name}", style="logger_name")
        log_text.append(" - ")

        # Add log level with appropriate color
        level_color = self.log_colors.get(record.levelname, "[white]")
        log_text.append(f"{record.levelname}", style=level_color)
        log_text.append(" - ")

        # Add the actual message
        # Add the message - either as a renderable or from the record
        if message_renderable:
            log_text.append(message_renderable)
        else:
            log_text.append(str(record.getMessage()), style="message")

        # Add traceback if present
        if traceback:
            log_text.append("\n")
            log_text.append(traceback)

        return log_text


class CLIView:
    """Enhanced CLI view with Rich formatting and logging capabilities."""

    def __init__(self):
        """Initialize the CLI view with custom console and logging setup."""
        self.console = Console(theme=custom_theme)
        self.active_spinner: Optional[Progress] = None

        # Configure logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging with Rich handler and custom formatting."""
        # Create our custom Rich handler
        rich_handler = RichLogHandler(console=self.console)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicate logs
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Add our custom handler
        root_logger.addHandler(rich_handler)

    # Rest of your existing CLIView methods remain the same
    def display_message(self, message: str):
        logger.debug("Displaying message: %s", message)
        panel = Panel(
            Text(message),
            box=box.ROUNDED,
            style="bright_cyan",
            border_style="bright_blue"
        )
        self.console.print(panel)

    def display_error(self, error: str):
        logger.error("Displaying error: %s", error)
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
        logger.debug("User input received: %s", user_input)
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
        logger.info("Displaying result: %s", result)
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
