"""Data models for BiComments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Video:
    video_id: str
    video_url: str
    title: str
    author_id: str
    author_name: str
    publish_date: Optional[datetime]
    view_count: Optional[int]
    comment_count: Optional[int]
    duration: Optional[str]
    first_seen_at: datetime
    last_seen_at: datetime


@dataclass(slots=True)
class CommentEvent:
    comment_id: str
    video_id: str
    user_id: str
    comment_text: str
    publish_time: datetime
    is_reply: bool
    parent_comment_id: Optional[str]
    user_level: Optional[int]
