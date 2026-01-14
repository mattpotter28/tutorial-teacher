"""Step-through mode for Tutorial Teacher - guided segment-by-segment learning."""

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

from ..cache import get_cache
from ..claude_client import ClaudeClient
from ..models import TutorialSession
from ..utils import ACCENT, DIM


def show_help(console: Console) -> None:
    """Display compact help."""
    console.print()
    console.print(f"[{DIM}]navigation[/{DIM}]  [bold]/n[/bold] next  [bold]/b[/bold] back  [bold]/j N[/bold] jump  [bold]/o[/bold] overview")
    console.print(f"[{DIM}]other[/{DIM}]       [bold]/raw[/bold] transcript  [bold]/mode[/bold] switch  [bold]/q[/bold] quit")
    console.print(f"[{DIM}]or just type a question[/{DIM}]")
    console.print()


def show_overview(session: TutorialSession, console: Console) -> None:
    """Display compact section overview."""
    console.print()
    for segment in session.segments:
        is_current = segment.index == session.current_segment_idx
        marker = "▸" if is_current else " "
        style = f"bold {ACCENT}" if is_current else DIM
        num = f"{segment.index + 1}".rjust(2)
        console.print(f"  {marker} [{style}]{num}[/{style}]  {segment.format_time_range()}")
    console.print()


def show_welcome(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
) -> None:
    """Show brief AI-generated welcome."""
    welcome_prompt = f"""You're a coding teacher. Write a ONE sentence welcome (under 20 words) that mentions what this tutorial teaches. Be warm but brief.

Based on: {session.segments[0].transcript[:1000] if session.segments else "coding tutorial"}"""

    try:
        full_response = ""
        with Live("", console=console, refresh_per_second=10, transient=True) as live:
            for chunk in claude_client.ask(welcome_prompt, session):
                full_response += chunk
                live.update(f"[{DIM}]{full_response}[/{DIM}]")
        console.print(f"[{DIM}]{full_response.strip()}[/{DIM}]")
        console.print()
    except Exception:
        pass  # Skip welcome on error


def show_section_header(session: TutorialSession, console: Console) -> None:
    """Show minimal section header."""
    segment = session.current_segment
    if not segment:
        return

    total = len(session.segments)
    console.print()
    console.print(
        Rule(
            f"[bold]Section {segment.index + 1}[/bold] [dim]of {total}[/dim]  •  {segment.format_time_range()}",
            style=ACCENT,
            align="left",
        )
    )
    console.print()


def teach_segment(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
    use_cache: bool = True,
) -> None:
    """Have Claude teach the current segment."""
    segment = session.current_segment
    if not segment:
        return

    show_section_header(session, console)

    cache = get_cache()

    # Check disk cache first
    if use_cache:
        cached = cache.get_segment_breakdown(session.video_id, segment.index)
        if cached:
            console.print(Markdown(cached))
            return

    teach_prompt = f"""Break down this tutorial section into 3-5 clear steps. Be concise.

Guidelines:
- Numbered steps (1, 2, 3)
- Include code snippets in markdown
- Skip filler, focus on actions
- End with what they should have working

Transcript:
{segment.transcript}"""

    try:
        full_response = ""
        with Live(Markdown(""), console=console, refresh_per_second=10) as live:
            for chunk in claude_client.ask(teach_prompt, session):
                full_response += chunk
                live.update(Markdown(full_response))

        # Save to disk cache
        cache.save_segment_breakdown(session.video_id, segment.index, full_response)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def run_step_through_mode(
    session: TutorialSession,
    claude_client: ClaudeClient,
    console: Console,
) -> str:
    """Run step-through mode. Returns 'quit' or 'switch'."""
    claude_client.clear_history()

    # Brief welcome
    show_welcome(session, claude_client, console)

    # Teach first segment
    teach_segment(session, claude_client, console)

    while True:
        try:
            # Minimal prompt with position indicator
            seg = session.current_segment_idx + 1
            total = len(session.segments)
            prompt = f"\n[{ACCENT}]{seg}/{total}[/{ACCENT}] [bold]❯[/bold] "
            user_input = console.input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[{DIM}]bye[/{DIM}]\n")
            return "quit"

        if not user_input:
            continue

        # Commands
        if user_input.startswith("/"):
            cmd = user_input.lower().split()
            c = cmd[0]
            args = cmd[1:] if len(cmd) > 1 else []

            if c in ("/q", "/quit"):
                console.print(f"\n[{DIM}]bye[/{DIM}]\n")
                return "quit"

            elif c in ("/m", "/mode"):
                console.print(f"\n[{DIM}]switching to freeform mode...[/{DIM}]\n")
                return "switch"

            elif c in ("/h", "/help", "/?"):
                show_help(console)

            elif c in ("/n", "/next"):
                if session.current_segment_idx < len(session.segments) - 1:
                    session.current_segment_idx += 1
                    teach_segment(session, claude_client, console)
                else:
                    console.print(f"\n[{DIM}]end of tutorial — /b to go back[/{DIM}]\n")

            elif c in ("/b", "/back", "/p", "/prev"):
                if session.current_segment_idx > 0:
                    session.current_segment_idx -= 1
                    teach_segment(session, claude_client, console)
                else:
                    console.print(f"\n[{DIM}]already at start[/{DIM}]\n")

            elif c in ("/o", "/overview", "/s", "/sections"):
                show_overview(session, console)

            elif c in ("/j", "/jump"):
                if args:
                    try:
                        target = int(args[0])
                        if 1 <= target <= len(session.segments):
                            session.current_segment_idx = target - 1
                            teach_segment(session, claude_client, console)
                        else:
                            console.print(f"[{DIM}]1-{len(session.segments)}[/{DIM}]")
                    except ValueError:
                        console.print(f"[{DIM}]/j <number>[/{DIM}]")
                else:
                    console.print(f"[{DIM}]/j <number>[/{DIM}]")

            elif c == "/raw":
                segment = session.current_segment
                if segment:
                    console.print()
                    console.print(Panel(
                        segment.transcript,
                        border_style=DIM,
                        padding=(1, 2),
                    ))

            else:
                console.print(f"[{DIM}]/h for help[/{DIM}]")

            continue

        # Question about current segment
        segment = session.current_segment
        if not segment:
            continue

        question_prompt = f"""Answer this question about Section {segment.index + 1}. Be concise and helpful.

Question: {user_input}"""

        console.print()
        try:
            full_response = ""
            with Live(Markdown(""), console=console, refresh_per_second=10) as live:
                for chunk in claude_client.ask(question_prompt, session):
                    full_response += chunk
                    live.update(Markdown(full_response))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    return "quit"
