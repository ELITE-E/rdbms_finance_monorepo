from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .ast import ColumnDef, TypeSpec
from .errors import ExecutionError


CATALOG_FILE = "catalog.json"

SUPPORTED_TYPES = {"INTEGER", "VARCHAR", "TEXT", "DATE", "BOOLEAN"}


@dataclass
class IndexMeta:
    name: str
    table_name: str
    column_name: str


@dataclass
class TableMeta:
    name: str
    columns: list[ColumnDef]
    indexes: dict[str, IndexMeta]  # index_name -> IndexMeta

    def column_names(self) -> set[str]:
        return {c.name for c in self.columns}

    def get_column(self, name: str) -> ColumnDef | None:
        for c in self.columns:
            if c.name == name:
                return c
        return None

    def primary_key_column(self) -> str | None:
        pk_cols = [c.name for c in self.columns if c.primary_key]
        if not pk_cols:
            return None
        # Step 3 rule: only one PK allowed
        return pk_cols[0]


@dataclass
class Catalog:
    version: int
    tables: dict[str, TableMeta]
    indexes: dict[str, IndexMeta]  # global index namespace

    @classmethod
    def empty(cls) -> "Catalog":
        return cls(version=1, tables={}, indexes={})

    @classmethod
    def load(cls, db_dir: Path) -> "Catalog":
        path = db_dir / CATALOG_FILE
        if not path.exists():
            return cls.empty()

        raw = json.loads(path.read_text(encoding="utf-8"))
        version = int(raw.get("version", 1))

        tables: dict[str, TableMeta] = {}
        indexes: dict[str, IndexMeta] = {}

        for tname, t in raw.get("tables", {}).items():
            cols = []
            for c in t.get("columns", []):
                typ = TypeSpec(name=c["typ"]["name"], params=list(c["typ"].get("params", [])))
                cols.append(
                    ColumnDef(
                        name=c["name"],
                        typ=typ,
                        not_null=bool(c.get("not_null", False)),
                        unique=bool(c.get("unique", False)),
                        primary_key=bool(c.get("primary_key", False)),
                    )
                )

            t_indexes: dict[str, IndexMeta] = {}
            for iname, im in t.get("indexes", {}).items():
                idx = IndexMeta(name=iname, table_name=im["table_name"], column_name=im["column_name"])
                t_indexes[iname] = idx
                indexes[iname] = idx

            tables[tname] = TableMeta(name=tname, columns=cols, indexes=t_indexes)

        # In case catalog.json also has global indexes (optional), merge
        for iname, im in raw.get("indexes", {}).items():
            if iname not in indexes:
                indexes[iname] = IndexMeta(name=iname, table_name=im["table_name"], column_name=im["column_name"])

        return cls(version=version, tables=tables, indexes=indexes)

    def save(self, db_dir: Path) -> None:
        path = db_dir / CATALOG_FILE

        def col_to_dict(c: ColumnDef) -> dict:
            return {
                "name": c.name,
                "typ": {"name": c.typ.name, "params": list(c.typ.params)},
                "not_null": c.not_null,
                "unique": c.unique,
                "primary_key": c.primary_key,
            }

        tables_dict: dict[str, dict] = {}
        for tname, t in self.tables.items():
            tables_dict[tname] = {
                "columns": [col_to_dict(c) for c in t.columns],
                "indexes": {
                    iname: {"table_name": idx.table_name, "column_name": idx.column_name}
                    for iname, idx in t.indexes.items()
                },
            }

        out = {
            "version": self.version,
            "tables": tables_dict,
            "indexes": {
                iname: {"table_name": idx.table_name, "column_name": idx.column_name}
                for iname, idx in self.indexes.items()
            },
        }
        path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")

    # ---------- validation helpers ----------

    def require_table(self, table_name: str) -> TableMeta:
        t = self.tables.get(table_name)
        if not t:
            raise ExecutionError(f"Table not found: {table_name}")
        return t

    def validate_type(self, typ: TypeSpec) -> None:
        tname = typ.name.upper()
        if tname not in SUPPORTED_TYPES:
            raise ExecutionError(f"Unsupported type: {typ.name}")

        if tname == "VARCHAR":
            if len(typ.params) != 1 or typ.params[0] <= 0:
                raise ExecutionError("VARCHAR requires exactly one positive length parameter, e.g. VARCHAR(255)")
        else:
            if typ.params:
                raise ExecutionError(f"Type {tname} does not accept parameters")

    def validate_create_table(self, table_name: str, columns: list[ColumnDef]) -> None:
        if table_name in self.tables:
            raise ExecutionError(f"Table already exists: {table_name}")

        col_names = [c.name for c in columns]
        if len(set(col_names)) != len(col_names):
            raise ExecutionError("Duplicate column name in CREATE TABLE")

        pk_cols = [c.name for c in columns if c.primary_key]
        if len(pk_cols) > 1:
            raise ExecutionError("Only one PRIMARY KEY column is supported in this phase")

        for c in columns:
            self.validate_type(c.typ)

    def validate_create_index(self, index_name: str, table_name: str, column_name: str) -> None:
        if index_name in self.indexes:
            raise ExecutionError(f"Index already exists: {index_name}")

        table = self.require_table(table_name)
        if column_name not in table.column_names():
            raise ExecutionError(f"Column not found: {table_name}.{column_name}")