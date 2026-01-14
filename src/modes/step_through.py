"""Step-through mode for Tutorial Teacher - guided segment-by-segment learning."""

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from ..claude_client import ClaudeClient
from ..models import TutorialSession


# Cache for processed segment instructions
_segment_cache: dict[int, str] = {}


def display_step_help(console: Console) -> None:
    """Display available commands."""
    console.print("\n[bold]Commands:[/bold]")
    console.print("  [green]/next[/green], [green]/n[/green]      - Continue to next section")
    console.print("  [green]/back[/green], [green]/b[/green]      - Go back to previous section")
    console.print("  [green]/overview[/green], [green]/o[/green]  - Show tutorial overview")
    console.print("  [green]/jump <n>[/green]      - Jump to section n")
    console.print("  [green]/raw[/green]           - Show raw transcript for current section")
    console.print("  [green]/quit[/green], [green]/q[/green]      - Exit")
    console.print("\n  [dim]Or just type a question to ask about this section[/dim]\n")


def display_overview(session: TutorialSession, console: Console) -> None:
    """Display tutorial overview with sections."""
    console.print(f"\n[bold]Tutorial Overview[/bold] ({session.format_duration()} total)\n")

    for segment in session.segments:
        is_current = segment.index == session.current_segment_idx
        marker = "[cyan]>[/cyan]" if is_current else " "
        style = "cyan" if is_current else "dim"
        console.print(f"  {marker} [{style}]Section {segment.index + 1}[/{style}] {segment.format_time_range()}")

    console.print()


def show_welcome(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
) -> None:
    """Show a warm welcome and tutorial introduction."""
    console.print()

    welcome_prompt = f"""You are a friendly coding teacher welcoming a student to a tutorial.

Based on this tutorial transcript, write a brief welcome (3-4 sentences max):
1. Greet them warmly
2. Tell them what they'll learn in this tutorial
3. Mention roughly how long it is ({session.format_duration()}) and that it's broken into {len(session.segments)} sections
4. End with an encouraging "Let's get started!" or similar

Keep it concise and friendly. Don't use headers or bullet points - just natural sentences.

Transcript preview (first section):
{session.segments[0].transcript[:1500] if session.segments else "No transcript available"}"""

    try:
        full_response = ""
        with Live(Markdown(""), console=console, refresh_per_second=10) as live:
            for chunk in claude_client.ask(welcome_prompt, session):
                full_response += chunk
                live.update(Markdown(full_response))
        console.print()
    except Exception as e:
        # Fallback welcome if Claude fails
        console.print(f"Welcome! This tutorial is {session.format_duration()} long, broken into {len(session.segments)} sections.")
        console.print("Type [green]/help[/green] for commands, or just ask questions as you go.\n")


def teach_segment(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
    use_cache: bool = True,
) -> None:
    """Have Claude teach the current segment as step-by-step instructions."""
    segment = session.current_segment
    if not segment:
        console.print("[red]No section available[/red]\n")
        return

    total = len(session.segments)

    # Header
    console.print(f"\n[bold cyan]Section {segment.index + 1} of {total}[/bold cyan] [dim]({segment.format_time_range()})[/dim]\n")

    # Check cache
    if use_cache and segment.index in _segment_cache:
        console.print(Markdown(_segment_cache[segment.index]))
        _show_nav_hint(session, console)
        return

    teach_prompt = f"""You are a patient coding teacher guiding a student through a tutorial step by step.

For this section of the tutorial ({segment.format_time_range()}), break down what the instructor is teaching into clear, actionable steps.

Guidelines:
- Use numbered steps (1, 2, 3...)
- Each step should be something concrete the student can DO
- Include any code snippets the instructor mentions (use markdown code blocks)
- Keep explanations brief but clear
- If there are gotchas or tips mentioned, include them
- End with what they should have accomplished by the end of this section

Section transcript:
{segment.transcript}

Write the step-by-step breakdown now:"""

    try:
        full_response = ""
        with Live(Markdown(""), console=console, refresh_per_second=10) as live:
            for chunk in claude_client.ask(teach_prompt, session):
                full_response += chunk
                live.update(Markdown(full_response))

        # Cache the response
        _segment_cache[segment.index] = full_response
        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]\n")
        return

    _show_nav_hint(session, console)


def _show_nav_hint(session: TutorialSession, console: Console) -> None:
    """Show navigation hint."""
    hints = []
    if session.current_segment_idx > 0:
        hints.append("[dim]/back[/dim]")
    if session.current_segment_idx < len(session.segments) - 1:
        hints.append("[dim]/next[/dim]")

    if hints:
        console.print(f"\n{' | '.join(hints)}\n")


def run_step_through_mode(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
) -> None:
    """
    Run step-through mode - guided segment-by-segment learning.
    """
    global _segment_cache
    _segment_cache = {}  # Clear cache for new session

    # Clear Claude's conversation history for fresh context
    claude_client.clear_history()

    # Welcome the user
    show_welcome(session, claude_client, console)

    # Teach the first segment
    teach_segment(session, claude_client, console)

    while True:
        try:
            segment_num = session.current_segment_idx + 1
            total = len(session.segments)
            user_input = console.input(f"[bold cyan][{segment_num}/{total}][/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[dim]Happy coding![/dim]\n")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            parts = user_input.lower().split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            if command in ("/quit", "/q"):
                console.print("\n[dim]Happy coding![/dim]\n")
                break

            elif command in ("/help", "/h"):
                display_step_help(console)

            elif command in ("/next", "/n"):
                if session.current_segment_idx < len(session.segments) - 1:
                    session.current_segment_idx += 1
                    teach_segment(session, claude_client, console)
                else:
                    console.print("\n[green]You've reached the end of the tutorial![/green]")
                    console.print("[dim]Use /back to review, or /quit to exit.[/dim]\n")

            elif command in ("/back", "/b", "/prev"):
                if session.current_segment_idx > 0:
                    session.current_segment_idx -= 1
                    teach_segment(session, claude_client, console)
                else:
                    console.print("\n[dim]You're at the beginning.[/dim]\n")

            elif command in ("/overview", "/o", "/segments", "/s"):
                display_overview(session, console)

            elif command == "/jump":
                if args:
                    try:
                        target = int(args[0])
                        if 1 <= target <= len(session.segments):
                            session.current_segment_idx = target - 1
                            teach_segment(session, claude_client, console)
                        else:
                            console.print(f"[red]Section must be between 1 and {len(session.segments)}[/red]\n")
                    except ValueError:
                        console.print("[red]Usage: /jump <section_number>[/red]\n")
                else:
                    console.print("[red]Usage: /jump <section_number>[/red]\n")

            elif command == "/raw":
                segment = session.current_segment
                if segment:
                    console.print(Panel(
                        segment.transcript,
                        title=f"[dim]Raw transcript - Section {segment.index + 1}[/dim]",
                        border_style="dim",
                    ))
                    console.print()

            else:
                console.print(f"[dim]Unknown command. Type /help for options.[/dim]\n")

            continue

        # Non-command: ask a question about current segment
        segment = session.current_segment
        if not segment:
            continue

        question_prompt = f"""The student is on Section {segment.index + 1} ({segment.format_time_range()}) and has a question.

Answer helpfully and concisely, like a patient teacher. If they're asking about code, include examples.

Their question: {user_input}"""

        console.print()
        try:
            full_response = ""
            with Live(Markdown(""), console=console, refresh_per_second=10) as live:
                for chunk in claude_client.ask(question_prompt, session):
                    full_response += chunk
                    live.update(Markdown(full_response))
            console.print()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")
