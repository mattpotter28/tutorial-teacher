"""Shared utilities for Tutorial Teacher."""

# Color palette - used across all UI components
ACCENT = "#6366f1"  # Indigo
DIM = "#6b7280"     # Gray
SUCCESS = "#10b981"  # Emerald


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    total = int(seconds)
    h, r = divmod(total, 3600)
    m, s = divmod(r, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_time_range(start: float, end: float) -> str:
    """Format a time range as 'MM:SS - MM:SS'."""
    return f"{format_timestamp(start)} - {format_timestamp(end)}"
