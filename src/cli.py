"""Main CLI entry point for Tutorial Teacher."""

import os
from enum import Enum

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.style import Style
from rich.text import Text
from rich.rule import Rule

from .claude_client import ClaudeClient
from .models import SessionMode
from .modes.freeform import run_freeform_mode
from .repo_fetcher import RepoFetchError
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

# Color palette - muted, professional
ACCENT = "#6366f1"  # Indigo
DIM = "#6b7280"     # Gray
SUCCESS = "#10b981" # Emerald


class ModeChoice(str, Enum):
    """CLI mode choices."""
    FREE = "free"
    STEP = "step"


def print_header() -> None:
    """Print minimal header."""
    console.print()
    console.print("[bold]tutorial-teacher[/bold]", style=f"bold {ACCENT}")
    console.print()


def print_context(session, mode: str) -> None:
    """Print compact context line."""
    parts = []
    parts.append(f"[bold]{session.format_duration()}[/bold]")
    parts.append(f"[dim]•[/dim] {len(session.segments)} sections")
    parts.append(f"[dim]•[/dim] {mode} mode")
    if session.repo_url:
        # Extract just repo name from URL
        repo_name = session.repo_url.rstrip('/').split('/')[-1]
        parts.append(f"[dim]•[/dim] [dim]repo:[/dim] {repo_name}")

    console.print("  ".join(parts))
    console.print()


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
        help="GitHub repository URL for code context",
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
        console.print()
        console.print("[red]✗[/red] ANTHROPIC_API_KEY not set")
        console.print()
        console.print("[dim]Set your API key:[/dim]")
        console.print("  export ANTHROPIC_API_KEY=sk-ant-...")
        console.print()
        raise typer.Exit(1)

    print_header()

    session_manager = SessionManager()
    session_mode = SessionMode.FREEFORM if mode == ModeChoice.FREE else SessionMode.STEP_THROUGH

    # Fetch transcript with spinner
    with console.status(f"[{DIM}]Loading...[/{DIM}]", spinner="dots"):
        try:
            session = session_manager.create_session(
                video_url=youtube_url,
                mode=session_mode,
                repo_url=repo,
            )
        except TranscriptError as e:
            console.print(f"[red]✗[/red] {e}")
            raise typer.Exit(1)
        except RepoFetchError as e:
            console.print(f"[red]✗[/red] {e}")
            raise typer.Exit(1)

    # Display compact context
    mode_name = "step-through" if mode == ModeChoice.STEP else "freeform"
    print_context(session, mode_name)

    # Initialize Claude client
    try:
        claude_client = ClaudeClient()
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1)

    # Run the appropriate mode
    if session_mode == SessionMode.FREEFORM:
        run_freeform_mode(session, claude_client, console)
    else:
        from .modes.step_through import run_step_through_mode
        run_step_through_mode(session, claude_client, console)


if __name__ == "__main__":
    app()
