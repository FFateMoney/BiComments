"""Interaction layer abstractions for comment loading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .exceptions import InteractionError


class CommentInteraction(Protocol):
    """Interface for comment loading actions (click, scroll, API trigger)."""

    def has_more(self) -> bool:
        ...

    def load_more(self) -> None:
        ...


@dataclass
class PagedInteraction:
    """Simple interaction that iterates through a finite number of pages."""

    max_pages: int
    current_page: int = 0

    def has_more(self) -> bool:
        return self.current_page < self.max_pages

    def load_more(self) -> None:
        if not self.has_more():
            raise InteractionError("No more pages to load")
        self.current_page += 1
