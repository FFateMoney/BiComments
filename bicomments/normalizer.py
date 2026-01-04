"""Normalization utilities for BiComments."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

RELATIVE_PATTERN = re.compile(r"(\d+)\s*(秒|分钟|小时|天|周|月|年)前")


def normalize_comment_text(node) -> str:
    """Extract pure text from a comment node, ignoring images and decorations."""
    for tag in node.find_all(["img", "svg"]):
        tag.extract()
    text = node.get_text(separator="", strip=True)
    return text


def normalize_timestamp(raw: str, ref: datetime) -> Optional[datetime]:
    """Normalize absolute or relative timestamps to UTC-aware datetime."""
    if not raw:
        return None
    raw = raw.strip()
    relative = _parse_relative(raw, ref)
    if relative:
        return relative

    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_relative(raw: str, ref: datetime) -> Optional[datetime]:
    match = RELATIVE_PATTERN.search(raw)
    if not match:
        return None
    value, unit = match.groups()
    try:
        count = int(value)
    except ValueError:
        return None
    delta = {
        "秒": timedelta(seconds=count),
        "分钟": timedelta(minutes=count),
        "小时": timedelta(hours=count),
        "天": timedelta(days=count),
        "周": timedelta(weeks=count),
        "月": timedelta(days=30 * count),
        "年": timedelta(days=365 * count),
    }.get(unit)
    if not delta:
        return None
    ref_utc = ref if ref.tzinfo else ref.replace(tzinfo=timezone.utc)
    return (ref_utc - delta).astimezone(timezone.utc)
