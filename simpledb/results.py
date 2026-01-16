from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CommandOk:
    rows_affected: int = 0
    message: str = "OK"


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]