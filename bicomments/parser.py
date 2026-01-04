"""Parser layer: stateless HTML parsing for videos and comments."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup

from .exceptions import ParseError
from .models import CommentEvent, Video
from .normalizer import normalize_comment_text, normalize_timestamp

VIDEO_CARD_CLASS = "bili-video-card__wrap"
VIDEO_ID_PATTERN = re.compile(r"/video/(BV[\w]+)")
AUTHOR_ID_PATTERN = re.compile(r"//space\.bilibili\.com/(\d+)")


def _extract_author(anchor) -> Tuple[str, str]:
    href = anchor.get("href") or ""
    author_match = AUTHOR_ID_PATTERN.search(href)
    if not author_match:
        raise ParseError("Author id not found on video card")
    return author_match.group(1), anchor.get_text(strip=True)


def parse_video_cards(html: str, fetched_at: datetime) -> List[Video]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_=VIDEO_CARD_CLASS)
    videos: List[Video] = []
    for card in cards:
        link = card.find("a", href=VIDEO_ID_PATTERN)
        if not link:
            continue
        video_url = link.get("href") or ""
        video_match = VIDEO_ID_PATTERN.search(video_url)
        if not video_match:
            continue
        video_id = video_match.group(1)

        title_tag = card.find("h3", class_="bili-video-card__info--tit")
        title = title_tag.get("title") if title_tag else link.get_text(strip=True)

        author_anchor = card.select_one(".bili-video-card__info--author a")
        if not author_anchor:
            raise ParseError(f"Author anchor missing for video {video_id}")
        author_id, author_name = _extract_author(author_anchor)

        publish_date_tag = card.select_one(".bili-video-card__info--date")
        publish_date_text = publish_date_tag.get_text(strip=True) if publish_date_tag else None
        publish_date = normalize_timestamp(publish_date_text, fetched_at) if publish_date_text else None

        stats_texts = [t.get_text(strip=True) for t in card.select(".bili-video-card__stats--text")]
        view_count = _parse_count(stats_texts[0]) if stats_texts else None
        comment_count = _parse_count(stats_texts[1]) if len(stats_texts) > 1 else None

        duration_tag = card.select_one(".bili-video-card__stats__duration")
        duration = duration_tag.get_text(strip=True) if duration_tag else None

        videos.append(
            Video(
                video_id=video_id,
                video_url=video_url,
                title=title or "",
                author_id=author_id,
                author_name=author_name,
                publish_date=publish_date,
                view_count=view_count,
                comment_count=comment_count,
                duration=duration,
                first_seen_at=fetched_at,
                last_seen_at=fetched_at,
            )
        )
    return videos


def _parse_count(text: str) -> Optional[int]:
    if not text:
        return None
    multipliers = {"万": 10_000, "亿": 100_000_000}
    for suffix, multiplier in multipliers.items():
        if text.endswith(suffix):
            try:
                return int(float(text.rstrip(suffix)) * multiplier)
            except ValueError:
                return None
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return None


def parse_comments(html: str, video_id: str, fetched_at: datetime) -> Iterable[CommentEvent]:
    soup = BeautifulSoup(html, "html.parser")
    for comment_node in soup.find_all("bili-comment-renderer"):
        main_comment = _parse_comment_node(comment_node, video_id, fetched_at, is_reply=False, parent_id=None)
        if main_comment:
            yield main_comment
        for reply_node in comment_node.find_all("bili-comment-reply-renderer"):
            reply_comment = _parse_comment_node(
                reply_node,
                video_id,
                fetched_at,
                is_reply=True,
                parent_id=main_comment.comment_id if main_comment else None,
            )
            if reply_comment:
                yield reply_comment


def _parse_comment_node(node, video_id: str, fetched_at: datetime, is_reply: bool, parent_id: Optional[str]) -> Optional[CommentEvent]:
    comment_id = node.get("data-id") or node.get("data-comment-id")
    if not comment_id:
        return None
    profile_id = node.get("data-user-profile-id")
    user_level = _parse_user_level(node)
    text_tag = node.find("p", id="contents")
    if not text_tag:
        return None
    publish_time_tag = node.find(id="pubdate")
    publish_text = publish_time_tag.get_text(strip=True) if publish_time_tag else None
    publish_time = normalize_timestamp(publish_text, fetched_at) if publish_text else fetched_at
    comment_text = normalize_comment_text(text_tag)
    return CommentEvent(
        comment_id=comment_id,
        video_id=video_id,
        user_id=profile_id or "",
        comment_text=comment_text,
        publish_time=publish_time,
        is_reply=is_reply,
        parent_comment_id=parent_id if is_reply else None,
        user_level=user_level,
    )


def _parse_user_level(node) -> Optional[int]:
    level_badge = node.find(attrs={"class": re.compile(r"level|user-level", re.I)})
    if not level_badge:
        return None
    text = level_badge.get_text(strip=True)
    digits = re.findall(r"\d+", text)
    if not digits:
        return None
    try:
        return int(digits[0])
    except ValueError:
        return None
