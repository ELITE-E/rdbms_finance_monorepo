from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------- Core nodes ----------

class Statement:
    pass


@dataclass(frozen=True)
class TypeSpec:
    """
    Examples:
      INTEGER
      VARCHAR(255)
      DATE
      BOOLEAN
      TEXT
    """
    name: str
    params: list[int]


@dataclass(frozen=True)
class ColumnDef:
    name: str
    typ: TypeSpec
    not_null: bool = False
    unique: bool = False
    primary_key: bool = False


@dataclass(frozen=True)
class ColumnRef:
    """
    Examples:
      id
      users.email   -> table='users', column='email'
    """
    column: str
    table: str | None = None


@dataclass(frozen=True)
class Condition:
    left: ColumnRef
    op: str          # Phase 1: only "="
    right: Any       # int | str | bool


@dataclass(frozen=True)
class WhereClause:
    conditions: list[Condition]


# ---------- Statements ----------

@dataclass(frozen=True)
class CreateTable(Statement):
    table_name: str
    columns: list[ColumnDef]


@dataclass(frozen=True)
class CreateIndex(Statement):
    index_name: str
    table_name: str
    column_name: str


@dataclass(frozen=True)
class Insert(Statement):
    table_name: str
    columns: list[str]
    values: list[Any]  # must align with columns


@dataclass(frozen=True)
class JoinClause:
    table_name: str
    left: ColumnRef
    right: ColumnRef


@dataclass(frozen=True)
class Select(Statement):
    columns: list[ColumnRef] | None  # None means "*"
    from_table: str
    joins: list[JoinClause]
    where: WhereClause | None


@dataclass(frozen=True)
class Assignment:
    column: str
    value: Any


@dataclass(frozen=True)
class Update(Statement):
    table_name: str
    assignments: list[Assignment]
    where: WhereClause | None


@dataclass(frozen=True)
class Delete(Statement):
    table_name: str
    where: WhereClause | None