from __future__ import annotations

from dataclasses import dataclass


class SimpleDBError(Exception):
    """Base class for all SimpleDB errors."""


@dataclass
class Position:
    line: int
    col: int


class SqlSyntaxError(SimpleDBError):
    def __init__(self, message: str, position: Position | None = None):
        self.message = message
        self.position = position
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.position is None:
            return f"SqlSyntaxError: {self.message}"
        return f"SqlSyntaxError at line {self.position.line}, col {self.position.col}: {self.message}"


class ExecutionError(SimpleDBError):
    pass


class ConstraintError(SimpleDBError):
    pass