"""Writer layer: sink abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from .exceptions import WriteError
from .models import CommentEvent, Video


class Writer:
    """Abstract writer interface."""

    def write_videos(self, videos: Iterable[Video]) -> None:
        raise NotImplementedError

    def write_comments(self, comments: Iterable[CommentEvent]) -> None:
        raise NotImplementedError


@dataclass
class InMemoryWriter(Writer):
    """In-memory writer useful for testing and dry-runs."""

    videos: List[Video] = field(default_factory=list)
    comments: List[CommentEvent] = field(default_factory=list)

    def write_videos(self, videos: Iterable[Video]) -> None:
        try:
            self.videos.extend(videos)
        except Exception as exc:  # pragma: no cover - minimal defensive guard
            raise WriteError("Failed to write videos") from exc

    def write_comments(self, comments: Iterable[CommentEvent]) -> None:
        try:
            self.comments.extend(comments)
        except Exception as exc:  # pragma: no cover - minimal defensive guard
            raise WriteError("Failed to write comments") from exc
