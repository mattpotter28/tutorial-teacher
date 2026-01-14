"""Caching functionality for Tutorial Teacher.

Caches data in a .tt/ directory to improve performance across sessions.
"""

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

from .models import TranscriptEntry, TutorialSegment


class TutorialCache:
    """Handles caching of tutorial data to disk."""

    def __init__(self, cache_dir: str = ".tt"):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory name for cache (relative to cwd)
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory structure if it doesn't exist."""
        (self.cache_dir / "transcripts").mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "segments").mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "repos").mkdir(parents=True, exist_ok=True)

    def _hash_key(self, key: str) -> str:
        """Create a safe filename from a key."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    # Transcript caching
    def get_transcript(self, video_id: str) -> list[TranscriptEntry] | None:
        """Get cached transcript entries for a video."""
        cache_file = self.cache_dir / "transcripts" / f"{video_id}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)
            return [
                TranscriptEntry(
                    start=entry["start"],
                    duration=entry["duration"],
                    text=entry["text"],
                )
                for entry in data
            ]
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def save_transcript(self, video_id: str, entries: list[TranscriptEntry]) -> None:
        """Save transcript entries to cache."""
        cache_file = self.cache_dir / "transcripts" / f"{video_id}.json"
        data = [
            {"start": e.start, "duration": e.duration, "text": e.text}
            for e in entries
        ]
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)
        except OSError:
            pass  # Silently fail on cache write errors

    # Segment breakdown caching (Claude's teaching responses)
    def get_segment_breakdown(self, video_id: str, segment_index: int) -> str | None:
        """Get cached Claude breakdown for a segment."""
        cache_file = self.cache_dir / "segments" / f"{video_id}_{segment_index}.txt"
        if not cache_file.exists():
            return None

        try:
            return cache_file.read_text()
        except OSError:
            return None

    def save_segment_breakdown(
        self, video_id: str, segment_index: int, breakdown: str
    ) -> None:
        """Save Claude's segment breakdown to cache."""
        cache_file = self.cache_dir / "segments" / f"{video_id}_{segment_index}.txt"
        try:
            cache_file.write_text(breakdown)
        except OSError:
            pass

    # Repo context caching
    def get_repo_context(self, repo_url: str) -> str | None:
        """Get cached repo context."""
        key = self._hash_key(repo_url)
        cache_file = self.cache_dir / "repos" / f"{key}.txt"
        if not cache_file.exists():
            return None

        try:
            return cache_file.read_text()
        except OSError:
            return None

    def save_repo_context(self, repo_url: str, context: str) -> None:
        """Save repo context to cache."""
        key = self._hash_key(repo_url)
        cache_file = self.cache_dir / "repos" / f"{key}.txt"
        try:
            cache_file.write_text(context)
        except OSError:
            pass

    def clear(self) -> None:
        """Clear all cached data."""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self._ensure_cache_dir()


# Global cache instance
_cache: TutorialCache | None = None


def get_cache() -> TutorialCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = TutorialCache()
    return _cache
