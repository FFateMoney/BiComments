"""Fetcher layer: HTTP requests and session management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from .exceptions import FetchError


@dataclass
class FetcherConfig:
    base_url: str = "https://www.bilibili.com"
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    timeout: int = 15


class Fetcher:
    """Handles authenticated requests without parsing or interaction."""

    def __init__(self, config: Optional[FetcherConfig] = None):
        self.config = config or FetcherConfig()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.config.user_agent})

    def fetch(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=self.config.timeout)
        except requests.RequestException as exc:
            raise FetchError(f"Request failed: {url}") from exc
        if not response.ok:
            raise FetchError(f"Unexpected status {response.status_code} for {url}")
        return response.text

    def fetch_homepage(self, user_id: str) -> str:
        url = f"{self.config.base_url}/space.bilibili.com/{user_id}/video"
        return self.fetch(url)

    def fetch_video_page(self, video_id: str) -> str:
        url = f"{self.config.base_url}/video/{video_id}"
        return self.fetch(url)
