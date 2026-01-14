"""Freeform Q&A mode for Tutorial Teacher."""

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from ..claude_client import ClaudeClient
from ..models import TutorialSession


def display_help(console: Console) -> None:
    """Display available commands."""
    table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="green")
    table.add_column("Description")

    table.add_row("/help, /h", "Show this help message")
    table.add_row("/segments, /s", "List all tutorial segments")
    table.add_row("/segment <n>", "Show details for segment n (1-based)")
    table.add_row("/clear", "Clear conversation history")
    table.add_row("/quit, /q", "Exit the session")
    table.add_row("", "")
    table.add_row("[dim]any text[/dim]", "[dim]Ask a question about the tutorial[/dim]")

    console.print(table)
    console.print()


def display_segments(session: TutorialSession, console: Console) -> None:
    """Display all tutorial segments."""
    table = Table(title="Tutorial Segments", show_header=True, header_style="bold cyan")
    table.add_column("#", style="bold", width=4)
    table.add_column("Time Range", width=20)
    table.add_column("Preview", overflow="ellipsis")

    for segment in session.segments:
        preview = segment.transcript[:80] + "..." if len(segment.transcript) > 80 else segment.transcript
        table.add_row(
            str(segment.index + 1),
            segment.format_time_range(),
            preview,
        )

    console.print(table)
    console.print()


def display_segment_detail(session: TutorialSession, segment_num: int, console: Console) -> None:
    """Display details for a specific segment."""
    # Convert to 0-based index
    index = segment_num - 1

    if index < 0 or index >= len(session.segments):
        console.print(f"[red]Invalid segment number. Please use 1-{len(session.segments)}[/red]\n")
        return

    segment = session.segments[index]
    console.print(
        Panel(
            segment.transcript,
            title=f"[bold]Segment {segment_num}: {segment.format_time_range()}[/bold]",
            border_style="blue",
        )
    )
    console.print()


def run_freeform_mode(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
) -> None:
    """
    Run the freeform Q&A mode.

    Args:
        session: The current tutorial session
        claude_client: The Claude API client
        console: Rich console for output
    """
    console.print("\n[bold]Freeform Q&A Mode[/bold]")
    console.print("Ask any question about the tutorial. Type [green]/help[/green] for commands.\n")

    while True:
        try:
            # Get user input
            user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[yellow]Goodbye![/yellow]\n")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            command = user_input.lower().split()[0]
            args = user_input.split()[1:] if len(user_input.split()) > 1 else []

            if command in ("/quit", "/q"):
                console.print("\n[yellow]Goodbye![/yellow]\n")
                break

            elif command in ("/help", "/h"):
                display_help(console)

            elif command in ("/segments", "/s"):
                display_segments(session, console)

            elif command == "/segment":
                if args:
                    try:
                        segment_num = int(args[0])
                        display_segment_detail(session, segment_num, console)
                    except ValueError:
                        console.print("[red]Please provide a valid segment number[/red]\n")
                else:
                    console.print("[red]Usage: /segment <number>[/red]\n")

            elif command == "/clear":
                claude_client.clear_history()
                console.print("[green]Conversation history cleared.[/green]\n")

            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Type [green]/help[/green] for available commands.\n")

            continue

        # Send question to Claude
        console.print()
        console.print("[bold magenta]Assistant:[/bold magenta]")

        try:
            # Stream the response with live update
            full_response = ""
            with Live(Markdown(""), console=console, refresh_per_second=10) as live:
                for chunk in claude_client.ask(user_input, session):
                    full_response += chunk
                    live.update(Markdown(full_response))

            console.print()  # Add spacing after response

        except Exception as e:
            console.print(f"[red]Error communicating with Claude: {e}[/red]\n")
