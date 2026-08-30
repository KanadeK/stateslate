"""Public error contract for invalid input and unsafe operations."""

from __future__ import annotations


class StateSlateError(Exception):
    """A user-correctable boundary or project-contract error."""

    def __init__(self, code: str, message: str, repair: str) -> None:
        self.code = code
        self.message = message
        self.repair = repair
        super().__init__(f"[{code}] {message}\nRepair: {repair}")
