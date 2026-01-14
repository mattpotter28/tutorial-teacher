"""Freeform Q&A mode for Tutorial Teacher."""

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from ..claude_client import ClaudeClient
from ..models import TutorialSession

# Color palette
ACCENT = "#6366f1"  # Indigo
DIM = "#6b7280"     # Gray


def show_help(console: Console) -> None:
    """Display compact help."""
    console.print()
    console.print(f"[{DIM}]commands[/{DIM}]   [bold]/s[/bold] segments  [bold]/s N[/bold] show segment  [bold]/clear[/bold] reset  [bold]/q[/bold] quit")
    console.print(f"[{DIM}]or just type a question about the tutorial[/{DIM}]")
    console.print()


def show_segments(session: TutorialSession, console: Console) -> None:
    """Display compact segment list."""
    console.print()
    for segment in session.segments:
        num = f"{segment.index + 1}".rjust(2)
        preview = segment.transcript[:60].replace('\n', ' ')
        if len(segment.transcript) > 60:
            preview += "..."
        console.print(f"  [{DIM}]{num}[/{DIM}]  {segment.format_time_range()}  [{DIM}]{preview}[/{DIM}]")
    console.print()


def show_segment_detail(session: TutorialSession, segment_num: int, console: Console) -> None:
    """Display a specific segment."""
    index = segment_num - 1

    if index < 0 or index >= len(session.segments):
        console.print(f"[{DIM}]1-{len(session.segments)}[/{DIM}]")
        return

    segment = session.segments[index]
    console.print()
    console.print(Panel(
        segment.transcript,
        title=f"[{DIM}]Section {segment_num} • {segment.format_time_range()}[/{DIM}]",
        border_style=DIM,
        padding=(1, 2),
    ))


def run_freeform_mode(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
) -> None:
    """Run freeform Q&A mode."""
    console.print(f"[{DIM}]ask anything about the tutorial • /h for help[/{DIM}]")
    console.print()

    while True:
        try:
            user_input = console.input(f"[bold]❯[/bold] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[{DIM}]bye[/{DIM}]\n")
            break

        if not user_input:
            continue

        # Commands
        if user_input.startswith("/"):
            parts = user_input.lower().split()
            cmd = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            if cmd in ("/q", "/quit"):
                console.print(f"\n[{DIM}]bye[/{DIM}]\n")
                break

            elif cmd in ("/h", "/help", "/?"):
                show_help(console)

            elif cmd in ("/s", "/segments"):
                if args:
                    try:
                        show_segment_detail(session, int(args[0]), console)
                    except ValueError:
                        console.print(f"[{DIM}]/s <number>[/{DIM}]")
                else:
                    show_segments(session, console)

            elif cmd == "/clear":
                claude_client.clear_history()
                console.print(f"[{DIM}]cleared[/{DIM}]")

            else:
                console.print(f"[{DIM}]/h for help[/{DIM}]")

            continue

        # Ask Claude
        console.print()
        try:
            full_response = ""
            with Live(Markdown(""), console=console, refresh_per_second=10) as live:
                for chunk in claude_client.ask(user_input, session):
                    full_response += chunk
                    live.update(Markdown(full_response))
            console.print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")
