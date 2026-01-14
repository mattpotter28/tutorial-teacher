"""Main CLI entry point for Tutorial Teacher."""

import os
import sys
from enum import Enum

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .claude_client import ClaudeClient
from .models import SessionMode
from .modes.freeform import run_freeform_mode
from .session import SessionManager
from .transcript import TranscriptError

# Load environment variables from .env file
load_dotenv()

app = typer.Typer(
    name="tt",
    help="Tutorial Teacher - Interactive AI assistant for YouTube coding tutorials",
    add_completion=False,
)
console = Console()


class ModeChoice(str, Enum):
    """CLI mode choices."""
    FREE = "free"
    STEP = "step"


@app.command()
def main(
    youtube_url: str = typer.Argument(
        ...,
        help="YouTube video URL or video ID",
    ),
    repo: str | None = typer.Option(
        None,
        "--repo",
        "-r",
        help="GitHub repository URL for code context (not yet implemented)",
    ),
    mode: ModeChoice = typer.Option(
        ModeChoice.FREE,
        "--mode",
        "-m",
        help="Tutorial mode: 'free' for freeform Q&A, 'step' for step-through",
    ),
) -> None:
    """
    Start an interactive tutorial session with a YouTube video.

    Examples:
        tt https://www.youtube.com/watch?v=VIDEO_ID
        tt VIDEO_ID --mode step
        tt https://youtu.be/VIDEO_ID --repo https://github.com/user/repo
    """
    # Check for API key early
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print(
            Panel(
                "[red]Error:[/red] ANTHROPIC_API_KEY environment variable not set.\n\n"
                "Please set your API key:\n"
                "  export ANTHROPIC_API_KEY=your-key-here\n\n"
                "Or create a .env file with:\n"
                "  ANTHROPIC_API_KEY=your-key-here",
                title="Missing API Key",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Warn about repo option
    if repo:
        console.print(
            "[yellow]Note:[/yellow] GitHub repo integration is not yet implemented. "
            "Continuing without repo context.\n"
        )

    # Create session
    console.print(f"\n[bold blue]Tutorial Teacher[/bold blue]\n")
    console.print(f"Loading tutorial from: [cyan]{youtube_url}[/cyan]\n")

    session_manager = SessionManager()
    session_mode = SessionMode.FREEFORM if mode == ModeChoice.FREE else SessionMode.STEP_THROUGH

    with console.status("[bold green]Fetching transcript..."):
        try:
            session = session_manager.create_session(
                video_url=youtube_url,
                mode=session_mode,
            )
        except TranscriptError as e:
            console.print(f"\n[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # Display session info
    display_session_info(session)

    # Initialize Claude client
    try:
        claude_client = ClaudeClient()
    except ValueError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)

    # Run the appropriate mode
    if session_mode == SessionMode.FREEFORM:
        run_freeform_mode(session, claude_client, console)
    else:
        console.print(
            "\n[yellow]Note:[/yellow] Step-through mode is not yet implemented. "
            "Starting freeform mode instead.\n"
        )
        run_freeform_mode(session, claude_client, console)


def display_session_info(session) -> None:
    """Display information about the loaded tutorial."""
    info_text = Text()
    info_text.append("Video ID: ", style="bold")
    info_text.append(f"{session.video_id}\n")
    info_text.append("Duration: ", style="bold")
    info_text.append(f"{session.format_duration()}\n")
    info_text.append("Segments: ", style="bold")
    info_text.append(f"{len(session.segments)}")

    console.print(
        Panel(
            info_text,
            title="[bold green]Tutorial Loaded[/bold green]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()
