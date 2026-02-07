from __future__ import annotations


class ResolverError(Exception):
    """Exception raised when a resolver cannot normalize or resolve an identifier.

    Raise this with a user-friendly message that can be surfaced to the UI.
    """

    def __init__(self, message: str) -> None:  # noqa: D107
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:  # pragma: no cover - trivial  # noqa: D105
        return self.message
