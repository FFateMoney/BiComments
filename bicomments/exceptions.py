"""Shared exceptions for the BiComments crawler."""


class FetchError(Exception):
    """Raised when fetching a page fails or returns an unexpected response."""


class ParseError(Exception):
    """Raised when parsing HTML/JSON fails or expected nodes are missing."""


class InteractionError(Exception):
    """Raised when an interaction step (e.g., load-more) fails."""


class WriteError(Exception):
    """Raised when writing to the data sink fails."""
