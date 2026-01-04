"""Orchestrator: coordinates fetcher, parser, interaction, normalizer, and writer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Set

from .fetcher import Fetcher
from .interaction import CommentInteraction
from .models import CommentEvent, Video
from .parser import parse_comments, parse_video_cards
from .writer import Writer


class Orchestrator:
    def __init__(self, fetcher: Fetcher, writer: Writer, interaction: CommentInteraction):
        self.fetcher = fetcher
        self.writer = writer
        self.interaction = interaction

    def run_for_user(self, user_id: str) -> None:
        fetched_at = datetime.now(timezone.utc)
        homepage_html = self.fetcher.fetch_homepage(user_id)
        videos = parse_video_cards(homepage_html, fetched_at)
        unique_videos, seen_ids = self._dedupe_videos(videos)
        self.writer.write_videos(unique_videos)

        for video in unique_videos:
            self._process_video(video)

    def _process_video(self, video: Video) -> None:
        page_html = self.fetcher.fetch_video_page(video.video_id)
        fetched_at = datetime.now(timezone.utc)
        seen_comments: Set[str] = set()
        while True:
            new_batch: List[CommentEvent] = []
            for comment in parse_comments(page_html, video.video_id, fetched_at):
                if comment.comment_id in seen_comments:
                    continue
                seen_comments.add(comment.comment_id)
                new_batch.append(comment)
            if new_batch:
                self.writer.write_comments(new_batch)
            if not self.interaction.has_more():
                break
            self.interaction.load_more()
            page_html = self.fetcher.fetch_video_page(video.video_id)

    def _dedupe_videos(self, videos: Iterable[Video]) -> tuple[list[Video], Set[str]]:
        seen: Set[str] = set()
        unique: List[Video] = []
        for video in videos:
            if video.video_id in seen:
                continue
            seen.add(video.video_id)
            unique.append(video)
        return unique, seen
