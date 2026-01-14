"""Transcript segmentation functionality."""

from .models import TranscriptEntry, TutorialSegment
from .utils import format_timestamp


def segment_transcript(
    entries: list[TranscriptEntry],
    segment_duration: int = 300  # 5 minutes in seconds
) -> list[TutorialSegment]:
    """
    Break transcript entries into fixed-duration segments.

    Args:
        entries: List of transcript entries
        segment_duration: Duration of each segment in seconds (default 5 minutes)

    Returns:
        List of TutorialSegment objects
    """
    if not entries:
        return []

    segments: list[TutorialSegment] = []
    current_segment_entries: list[TranscriptEntry] = []
    segment_start_time = 0.0
    segment_index = 0

    for entry in entries:
        # Check if this entry would push us past the segment boundary
        segment_end_time = segment_start_time + segment_duration

        if entry.start >= segment_end_time and current_segment_entries:
            # Finalize current segment
            segment = _create_segment(
                index=segment_index,
                entries=current_segment_entries,
                start_time=segment_start_time,
                end_time=segment_end_time,
            )
            segments.append(segment)

            # Start new segment
            segment_index += 1
            segment_start_time = segment_end_time
            current_segment_entries = []

        current_segment_entries.append(entry)

    # Don't forget the last segment
    if current_segment_entries:
        # Calculate actual end time from last entry
        last_entry = current_segment_entries[-1]
        actual_end = last_entry.start + last_entry.duration

        segment = _create_segment(
            index=segment_index,
            entries=current_segment_entries,
            start_time=segment_start_time,
            end_time=actual_end,
        )
        segments.append(segment)

    return segments


def _create_segment(
    index: int,
    entries: list[TranscriptEntry],
    start_time: float,
    end_time: float,
) -> TutorialSegment:
    """Create a TutorialSegment from a list of entries."""
    # Combine all entry texts
    transcript_text = " ".join(entry.text for entry in entries)

    # Generate a simple title
    title = f"Part {index + 1}: {format_timestamp(start_time)} - {format_timestamp(end_time)}"

    return TutorialSegment(
        index=index,
        start_time=start_time,
        end_time=end_time,
        title=title,
        transcript=transcript_text,
    )


def get_segment_for_time(segments: list[TutorialSegment], time_seconds: float) -> TutorialSegment | None:
    """Find the segment that contains a given timestamp."""
    for segment in segments:
        if segment.start_time <= time_seconds < segment.end_time:
            return segment
    return None
