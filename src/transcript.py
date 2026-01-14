"""YouTube transcript fetching functionality."""

import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from .models import TranscriptEntry


class TranscriptError(Exception):
    """Error fetching transcript."""
    pass


def extract_video_id(url: str) -> str:
    """
    Extract YouTube video ID from various URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - Just the video ID itself
    """
    # Already a video ID (11 characters, alphanumeric with - and _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    parsed = urlparse(url)

    # youtu.be/VIDEO_ID
    if parsed.netloc in ('youtu.be', 'www.youtu.be'):
        return parsed.path.lstrip('/')

    # youtube.com/watch?v=VIDEO_ID
    if parsed.netloc in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            query = parse_qs(parsed.query)
            if 'v' in query:
                return query['v'][0]

        # /embed/VIDEO_ID or /v/VIDEO_ID
        match = re.match(r'^/(embed|v)/([a-zA-Z0-9_-]{11})', parsed.path)
        if match:
            return match.group(2)

    raise TranscriptError(f"Could not extract video ID from URL: {url}")


def fetch_transcript(video_url: str) -> list[TranscriptEntry]:
    """
    Fetch the transcript for a YouTube video.

    Args:
        video_url: YouTube video URL or video ID

    Returns:
        List of TranscriptEntry objects

    Raises:
        TranscriptError: If transcript cannot be fetched
    """
    try:
        video_id = extract_video_id(video_url)
    except TranscriptError:
        raise

    try:
        # Create API instance (new API in v1.0.0+)
        ytt_api = YouTubeTranscriptApi()

        # Fetch transcript - defaults to English, falls back to auto-generated
        transcript = ytt_api.fetch(video_id)

        # Convert to our TranscriptEntry format
        return [
            TranscriptEntry(
                start=snippet.start,
                duration=snippet.duration,
                text=snippet.text,
            )
            for snippet in transcript
        ]

    except NoTranscriptFound:
        raise TranscriptError(
            f"No transcript available for video: {video_id}"
        )
    except TranscriptsDisabled:
        raise TranscriptError(
            f"Transcripts are disabled for video: {video_id}"
        )
    except VideoUnavailable:
        raise TranscriptError(
            f"Video is unavailable: {video_id}"
        )
    except Exception as e:
        raise TranscriptError(f"Failed to fetch transcript: {e}")


def get_full_transcript_text(entries: list[TranscriptEntry]) -> str:
    """Combine all transcript entries into a single text."""
    return " ".join(entry.text for entry in entries)
