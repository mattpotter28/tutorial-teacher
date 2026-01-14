"""Session management for Tutorial Teacher."""

from .models import SessionMode, TutorialSession
from .repo_fetcher import RepoFetchError, fetch_repo_context
from .segmenter import segment_transcript
from .transcript import (
    TranscriptError,
    extract_video_id,
    fetch_transcript,
    get_full_transcript_text,
)


class SessionManager:
    """Manages tutorial sessions."""

    def __init__(self):
        self.current_session: TutorialSession | None = None

    def create_session(
        self,
        video_url: str,
        mode: SessionMode = SessionMode.FREEFORM,
        segment_duration: int = 300,
        repo_url: str | None = None,
    ) -> TutorialSession:
        """
        Create a new tutorial session from a YouTube URL.

        Args:
            video_url: YouTube video URL
            mode: Session mode (freeform or step-through)
            segment_duration: Duration of each segment in seconds
            repo_url: Optional GitHub repository URL for code context

        Returns:
            A new TutorialSession

        Raises:
            TranscriptError: If transcript cannot be fetched
            RepoFetchError: If repository cannot be fetched
        """
        # Extract video ID
        video_id = extract_video_id(video_url)

        # Fetch transcript
        entries = fetch_transcript(video_url)

        # Get full transcript text
        full_transcript = get_full_transcript_text(entries)

        # Create segments
        segments = segment_transcript(entries, segment_duration)

        # Fetch repo context if provided
        repo_context = ""
        if repo_url:
            repo_context = fetch_repo_context(repo_url)

        # Create session
        # For now, use a placeholder title (could fetch from YouTube API later)
        title = f"Tutorial ({video_id})"

        session = TutorialSession(
            video_url=video_url,
            video_id=video_id,
            title=title,
            segments=segments,
            current_segment_idx=0,
            mode=mode,
            full_transcript=full_transcript,
            repo_url=repo_url,
            repo_context=repo_context,
        )

        self.current_session = session
        return session

    def next_segment(self) -> bool:
        """
        Move to the next segment.

        Returns:
            True if moved to next segment, False if already at end
        """
        if not self.current_session:
            return False

        if self.current_session.current_segment_idx < len(self.current_session.segments) - 1:
            self.current_session.current_segment_idx += 1
            return True
        return False

    def previous_segment(self) -> bool:
        """
        Move to the previous segment.

        Returns:
            True if moved to previous segment, False if already at start
        """
        if not self.current_session:
            return False

        if self.current_session.current_segment_idx > 0:
            self.current_session.current_segment_idx -= 1
            return True
        return False

    def go_to_segment(self, index: int) -> bool:
        """
        Jump to a specific segment.

        Args:
            index: 0-based segment index

        Returns:
            True if jumped to segment, False if index out of range
        """
        if not self.current_session:
            return False

        if 0 <= index < len(self.current_session.segments):
            self.current_session.current_segment_idx = index
            return True
        return False
