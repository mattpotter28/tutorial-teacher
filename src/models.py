"""Data models for Tutorial Teacher."""

from dataclasses import dataclass, field
from enum import Enum

from .utils import format_timestamp, format_time_range


class SessionMode(Enum):
    """Tutorial session modes."""
    FREEFORM = "free"
    STEP_THROUGH = "step"


@dataclass
class TranscriptEntry:
    """A single entry from the YouTube transcript."""
    start: float  # Start time in seconds
    duration: float  # Duration in seconds
    text: str

    @property
    def end(self) -> float:
        """End time in seconds."""
        return self.start + self.duration

    def format_start_time(self) -> str:
        """Format start time as MM:SS or HH:MM:SS."""
        return format_timestamp(self.start)


@dataclass
class TutorialSegment:
    """A segment of the tutorial (e.g., 5-minute chunk)."""
    index: int  # 0-based segment index
    start_time: float  # Start time in seconds
    end_time: float  # End time in seconds
    title: str  # Generated or extracted title
    transcript: str  # Combined transcript text for this segment
    relevant_files: list[str] = field(default_factory=list)  # Optional GitHub files

    def format_time_range(self) -> str:
        """Format the time range as a string."""
        return format_time_range(self.start_time, self.end_time)

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self.end_time - self.start_time


@dataclass
class TutorialSession:
    """A tutorial session with all its state."""
    video_url: str
    video_id: str
    title: str
    segments: list[TutorialSegment]
    current_segment_idx: int = 0
    mode: SessionMode = SessionMode.FREEFORM
    full_transcript: str = ""  # Complete transcript for context
    repo_url: str | None = None  # GitHub repo URL if provided
    repo_context: str = ""  # Fetched repo content for Claude

    @property
    def current_segment(self) -> TutorialSegment | None:
        """Get the current segment."""
        if 0 <= self.current_segment_idx < len(self.segments):
            return self.segments[self.current_segment_idx]
        return None

    @property
    def total_duration(self) -> float:
        """Total duration of the tutorial in seconds."""
        if not self.segments:
            return 0.0
        return self.segments[-1].end_time

    def format_duration(self) -> str:
        """Format total duration as a string."""
        return format_timestamp(self.total_duration)
