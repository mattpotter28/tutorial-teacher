"""Data models for Tutorial Teacher."""

from dataclasses import dataclass, field
from enum import Enum


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

    def format_timestamp(self) -> str:
        """Format start time as MM:SS or HH:MM:SS."""
        total_seconds = int(self.start)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


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
        def fmt(seconds: float) -> str:
            total = int(seconds)
            h, r = divmod(total, 3600)
            m, s = divmod(r, 60)
            if h > 0:
                return f"{h}:{m:02d}:{s:02d}"
            return f"{m}:{s:02d}"
        return f"{fmt(self.start_time)} - {fmt(self.end_time)}"

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
        total = int(self.total_duration)
        h, r = divmod(total, 3600)
        m, s = divmod(r, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
