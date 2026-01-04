"""
BiComments layered crawler package.

This package follows the mandated architecture:
- Fetcher: HTTP requests and login state.
- Parser: HTML/JSON parsing (stateless, no side effects).
- Interaction: UI/scroll/load triggers for comments.
- Normalizer: Data cleaning and normalization.
- Writer: Database or sink adapters.
- Orchestrator: Coordinates the flow.

Concrete implementations live in sibling modules; defaults are lightweight
and intended as starting points for production-ready implementations.
"""

__all__ = [
    "models",
    "exceptions",
    "fetcher",
    "parser",
    "interaction",
    "normalizer",
    "writer",
    "orchestrator",
]
