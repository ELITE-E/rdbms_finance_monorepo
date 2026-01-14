from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..ast import (
    ColumnRef,
    CreateIndex,
    CreateTable,
    Delete,
    Insert,
    Select,
    Statement,
    Update,
)
from ..catalog import Catalog, IndexMeta, TableMeta
from ..errors import ConstraintError, ExecutionError
from ..result import CommandOk, QueryResult
from ..storage.heap import HeapTable


@dataclass
class Executor:
    db_dir: Path
    catalog: Catalog

    def execute(self, stmt: Statement):
        if isinstance(stmt, CreateTable):
            return self._create_table(stmt)
        if isinstance(stmt, CreateIndex):
            return self._create_index(stmt)
        if isinstance(stmt, Insert):
            return self._insert(stmt)
        if isinstance(stmt, Select):
            return self._select(stmt)
        if isinstance(stmt, Update):
            return self._update(stmt)
        if isinstance(stmt, Delete):
            return self._delete(stmt)

        raise ExecutionError(f"Unsupported statement: {type(stmt).__name__}")

    # ---------- DDL ----------

    def _create_table(self, stmt: CreateTable) -> CommandOk:
        self.catalog.validate_create_table(stmt.table_name, stmt.columns)

        table = TableMeta(name=stmt.table_name, columns=stmt.columns, indexes={})
        self.catalog.tables[stmt.table_name] = table
        self.catalog.save(self.db_dir)

        HeapTable.open(self.db_dir, stmt.table_name)
        return CommandOk(rows_affected=0, message=f"Table created: {stmt.table_name}")

    def _create_index(self, stmt: CreateIndex) -> CommandOk:
        self.catalog.validate_create_index(stmt.index_name, stmt.table_name, stmt.column_name)

        idx = IndexMeta(name=stmt.index_name, table_name=stmt.table_name, column_name=stmt.column_name)
        self.catalog.indexes[stmt.index_name] = idx

        table = self.catalog.require_table(stmt.table_name)
        table.indexes[stmt.index_name] = idx

        self.catalog.save(self.db_dir)
        return CommandOk(
            rows_affected=0,
            message=f"Index created: {stmt.index_name} ON {stmt.table_name}({stmt.column_name})",
        )

    # ---------- common helpers ----------

    def _resolve_col(self, table_name: str, colref: ColumnRef, ctx: str) -> str:
        if colref.table is not None and colref.table != table_name:
            raise ExecutionError(f"{ctx}: column qualifier {colref.table}.{colref.column} does not match {table_name}")
        return colref.column

    def _validate_insert_types(self, table: TableMeta, row: dict[str, Any]) -> None:
        for col_def in table.columns:
            if col_def.name not in row:
                continue
            val = row[col_def.name]
            if val is None:
                continue

            t = col_def.typ.name.upper()
            if t == "INTEGER":
                if not isinstance(val, int) or isinstance(val, bool):
                    raise ExecutionError(f"Type error: {table.name}.{col_def.name} expects INTEGER")
            elif t in ("VARCHAR", "TEXT", "DATE"):
                if not isinstance(val, str):
                    raise ExecutionError(f"Type error: {table.name}.{col_def.name} expects TEXT/DATE")
                if t == "VARCHAR":
                    max_len = col_def.typ.params[0]
                    if len(val) > max_len:
                        raise ExecutionError(f"Type error: {table.name}.{col_def.name} exceeds VARCHAR({max_len})")
            elif t == "BOOLEAN":
                if not isinstance(val, bool):
                    raise ExecutionError(f"Type error: {table.name}.{col_def.name} expects BOOLEAN")
            else:
                raise ExecutionError(f"Unsupported type: {t}")

    def _row_matches_where(self, table_name: str, row: dict[str, Any], where) -> bool:
        if where is None:
            return True
        for cond in where.conditions:
            if cond.op != "=":
                raise ExecutionError("Only '=' is supported in WHERE in this phase")
            col = self._resolve_col(table_name, cond.left, "WHERE")
            if row.get(col) != cond.right:
                return False
        return True

    # ---------- constraint helpers (INSERT + UPDATE) ----------

    def _enforce_constraints_batch(
        self,
        table: TableMeta,
        existing_rows: list[dict[str, Any]],
        new_rows: list[dict[str, Any]],
        exclude_rids: set[int],
    ) -> None:
        """
        Checks NOT NULL / PK / UNIQUE for a batch of new candidate rows,
        against existing active rows excluding exclude_rids.
        """

        # filter existing rows (excluding those being updated/deleted)
        existing_kept = [r for r in existing_rows if int(r.get("_rid")) not in exclude_rids]

        # NOT NULL + PK implies NOT NULL
        for nr in new_rows:
            for c in table.columns:
                if c.not_null or c.primary_key:
                    if nr.get(c.name) is None:
                        if c.primary_key:
                            raise ConstraintError(f"PRIMARY KEY column cannot be NULL: {table.name}.{c.name}")
                        raise ConstraintError(f"NOT NULL constraint failed: {table.name}.{c.name}")

        pk_col = table.primary_key_column()
        if pk_col is not None:
            existing_pks = set(r.get(pk_col) for r in existing_kept)
            seen_new_pks: set[Any] = set()
            for nr in new_rows:
                pk_val = nr.get(pk_col)
                # pk_val cannot be None due to NOT NULL check above
                if pk_val in existing_pks:
                    raise ConstraintError(
                        f"PRIMARY KEY constraint failed: duplicate value {pk_val!r} for {table.name}.{pk_col}"
                    )
                if pk_val in seen_new_pks:
                    raise ConstraintError(
                        f"PRIMARY KEY constraint failed: duplicate value {pk_val!r} within UPDATE/INSERT batch"
                    )
                seen_new_pks.add(pk_val)

        # UNIQUE columns (NULL ignored)
        unique_cols = [c.name for c in table.columns if c.unique]
        for ucol in unique_cols:
            existing_vals = set(r.get(ucol) for r in existing_kept if r.get(ucol) is not None)
            seen_new: set[Any] = set()
            for nr in new_rows:
                v = nr.get(ucol)
                if v is None:
                    continue
                if v in existing_vals:
                    raise ConstraintError(
                        f"UNIQUE constraint failed: duplicate value {v!r} for {table.name}.{ucol}"
                    )
                if v in seen_new:
                    raise ConstraintError(
                        f"UNIQUE constraint failed: duplicate value {v!r} within UPDATE/INSERT batch for {table.name}.{ucol}"
                    )
                seen_new.add(v)

    # ---------- INSERT ----------

    def _insert(self, stmt: Insert) -> CommandOk:
        table = self.catalog.require_table(stmt.table_name)

        table_cols = table.column_names()
        for c in stmt.columns:
            if c not in table_cols:
                raise ExecutionError(f"Unknown column in INSERT: {stmt.table_name}.{c}")

        row: dict[str, Any] = {c.name: None for c in table.columns}
        for c, v in zip(stmt.columns, stmt.values):
            row[c] = v

        self._validate_insert_types(table, row)

        heap = HeapTable.open(self.db_dir, stmt.table_name)
        existing = list(heap.scan_active())

        # INSERT is a batch of 1 row; no exclusions
        self._enforce_constraints_batch(table, existing_rows=existing, new_rows=[row], exclude_rids=set())

        heap.insert(row)
        return CommandOk(rows_affected=1, message="1 row inserted")

    # ---------- SELECT (single table) ----------

    def _select(self, stmt: Select) -> QueryResult:
        if stmt.joins:
            raise ExecutionError("JOIN not implemented yet (later step)")

        table = self.catalog.require_table(stmt.from_table)
        heap = HeapTable.open(self.db_dir, stmt.from_table)

        if stmt.columns is None:  # "*"
            out_cols = [c.name for c in table.columns]
        else:
            out_cols = [self._resolve_col(stmt.from_table, c, "SELECT") for c in stmt.columns]
            table_cols = table.column_names()
            for c in out_cols:
                if c not in table_cols:
                    raise ExecutionError(f"Unknown column in SELECT: {stmt.from_table}.{c}")

        rows_out: list[list[Any]] = []
        for row in heap.scan_active():
            if not self._row_matches_where(stmt.from_table, row, stmt.where):
                continue
            rows_out.append([row.get(c) for c in out_cols])

        return QueryResult(columns=out_cols, rows=rows_out)

    # ---------- UPDATE ----------

    def _update(self, stmt: Update) -> CommandOk:
        table = self.catalog.require_table(stmt.table_name)
        heap = HeapTable.open(self.db_dir, stmt.table_name)

        table_cols = table.column_names()
        for a in stmt.assignments:
            if a.column not in table_cols:
                raise ExecutionError(f"Unknown column in UPDATE: {stmt.table_name}.{a.column}")

        existing = list(heap.scan_active())
        matches = [r for r in existing if self._row_matches_where(stmt.table_name, r, stmt.where)]
        if not matches:
            return CommandOk(rows_affected=0, message="0 rows updated")

        # Build new candidate rows (don’t write anything yet)
        new_rows: list[dict[str, Any]] = []
        exclude_rids: set[int] = set()

        for old in matches:
            old_rid = int(old["_rid"])
            exclude_rids.add(old_rid)

            candidate = {c.name: old.get(c.name) for c in table.columns}  # logical columns only
            for a in stmt.assignments:
                candidate[a.column] = a.value

            self._validate_insert_types(table, candidate)
            new_rows.append(candidate)

        # Enforce constraints as a batch (prevents partial updates)
        self._enforce_constraints_batch(table, existing_rows=existing, new_rows=new_rows, exclude_rids=exclude_rids)

        # Apply: append new rows + tombstone old rids
        for old, candidate in zip(matches, new_rows):
            heap.insert(candidate)
            heap.tombstone(int(old["_rid"]))

        return CommandOk(rows_affected=len(matches), message=f"{len(matches)} rows updated")

    # ---------- DELETE ----------

    def _delete(self, stmt: Delete) -> CommandOk:
        self.catalog.require_table(stmt.table_name)
        heap = HeapTable.open(self.db_dir, stmt.table_name)

        existing = list(heap.scan_active())
        matches = [r for r in existing if self._row_matches_where(stmt.table_name, r, stmt.where)]
        for r in matches:
            heap.tombstone(int(r["_rid"]))

        return CommandOk(rows_affected=len(matches), message=f"{len(matches)} rows deleted")

# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path
# from typing import Any

# from ..ast import ColumnRef, CreateIndex, CreateTable, Insert, Select, Statement
# from ..catalog import Catalog, IndexMeta, TableMeta
# from ..errors import ConstraintError, ExecutionError
# from ..result import CommandOk, QueryResult
# from ..storage.heap import HeapTable


# @dataclass
# class Executor:
#     db_dir: Path
#     catalog: Catalog

#     # ... (DDL + other helpers unchanged)

#     # ---------- constraints (Step 5) ----------

#     def _enforce_insert_constraints(self, table: TableMeta, heap: HeapTable, row: dict[str, Any]) -> None:
#         # NOT NULL + PK implies NOT NULL
#         for c in table.columns:
#             if c.not_null or c.primary_key:
#                 if row.get(c.name) is None:
#                     if c.primary_key:
#                         raise ConstraintError(f"PRIMARY KEY column cannot be NULL: {table.name}.{c.name}")
#                     raise ConstraintError(f"NOT NULL constraint failed: {table.name}.{c.name}")

#         pk_col = table.primary_key_column()
#         pk_val = row.get(pk_col) if pk_col else None

#         # Build list of UNIQUE columns + their incoming values (skip NULL like SQL UNIQUE)
#         unique_checks: list[tuple[str, Any]] = []
#         for c in table.columns:
#             if c.unique and row.get(c.name) is not None:
#                 unique_checks.append((c.name, row.get(c.name)))

#         # Scan existing rows once and check for duplicates
#         for existing in heap.scan():
#             if pk_col is not None:
#                 if existing.get(pk_col) == pk_val:
#                     raise ConstraintError(
#                         f"PRIMARY KEY constraint failed: duplicate value {pk_val!r} for {table.name}.{pk_col}"
#                     )

#             for col_name, val in unique_checks:
#                 if existing.get(col_name) == val:
#                     raise ConstraintError(
#                         f"UNIQUE constraint failed: duplicate value {val!r} for {table.name}.{col_name}"
#                     )

#     # ---------- INSERT (updated) ----------

#     def _insert(self, stmt: Insert) -> CommandOk:
#         table = self.catalog.require_table(stmt.table_name)

#         # validate columns exist
#         table_cols = table.column_names()
#         for c in stmt.columns:
#             if c not in table_cols:
#                 raise ExecutionError(f"Unknown column in INSERT: {stmt.table_name}.{c}")

#         # build full row with missing columns as None
#         row: dict[str, Any] = {c.name: None for c in table.columns}
#         for c, v in zip(stmt.columns, stmt.values):
#             row[c] = v

#         self._validate_insert_types(table, row)

#         heap = HeapTable.open(self.db_dir, stmt.table_name)

#         # Step 5: enforce PK/UNIQUE/NOT NULL
#         self._enforce_insert_constraints(table, heap, row)

#         heap.insert(row)
#         return CommandOk(rows_affected=1, message="1 row inserted")

#step5changesabove(read md5)

# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path
# from typing import Any

# from ..ast import ColumnRef, CreateIndex, CreateTable, Insert, Select, Statement
# from ..catalog import Catalog, IndexMeta, TableMeta
# from ..errors import ExecutionError
# from ..result import CommandOk, QueryResult
# from ..storage.heap import HeapTable


# @dataclass
# class Executor:
#     db_dir: Path
#     catalog: Catalog

#     def execute(self, stmt: Statement):
#         if isinstance(stmt, CreateTable):
#             return self._create_table(stmt)
#         if isinstance(stmt, CreateIndex):
#             return self._create_index(stmt)
#         if isinstance(stmt, Insert):
#             return self._insert(stmt)
#         if isinstance(stmt, Select):
#             return self._select(stmt)

#         # Step 4: UPDATE/DELETE/JOIN not implemented yet
#         raise ExecutionError(f"Not implemented yet (Step 4): {type(stmt).__name__}")

#     # ---------- DDL ----------

#     def _create_table(self, stmt: CreateTable) -> CommandOk:
#         self.catalog.validate_create_table(stmt.table_name, stmt.columns)

#         table = TableMeta(name=stmt.table_name, columns=stmt.columns, indexes={})
#         self.catalog.tables[stmt.table_name] = table
#         self.catalog.save(self.db_dir)

#         # Ensure storage files exist right away
#         HeapTable.open(self.db_dir, stmt.table_name)

#         return CommandOk(rows_affected=0, message=f"Table created: {stmt.table_name}")

#     def _create_index(self, stmt: CreateIndex) -> CommandOk:
#         self.catalog.validate_create_index(stmt.index_name, stmt.table_name, stmt.column_name)

#         idx = IndexMeta(name=stmt.index_name, table_name=stmt.table_name, column_name=stmt.column_name)
#         self.catalog.indexes[stmt.index_name] = idx

#         table = self.catalog.require_table(stmt.table_name)
#         table.indexes[stmt.index_name] = idx

#         self.catalog.save(self.db_dir)
#         return CommandOk(
#             rows_affected=0,
#             message=f"Index created: {stmt.index_name} ON {stmt.table_name}({stmt.column_name})",
#         )

#     # ---------- helpers ----------

#     def _validate_insert_types(self, table: TableMeta, row: dict[str, Any]) -> None:
#         """
#         Basic type validation only (constraints like NOT NULL/UNIQUE/PK come in Step 5).
#         """
#         for col_def in table.columns:
#             if col_def.name not in row:
#                 continue
#             val = row[col_def.name]
#             if val is None:
#                 continue

#             t = col_def.typ.name.upper()
#             if t == "INTEGER":
#                 if not isinstance(val, int) or isinstance(val, bool):
#                     raise ExecutionError(f"Type error: {table.name}.{col_def.name} expects INTEGER")
#             elif t in ("VARCHAR", "TEXT", "DATE"):
#                 if not isinstance(val, str):
#                     raise ExecutionError(f"Type error: {table.name}.{col_def.name} expects TEXT")
#                 if t == "VARCHAR":
#                     max_len = col_def.typ.params[0]
#                     if len(val) > max_len:
#                         raise ExecutionError(
#                             f"Type error: {table.name}.{col_def.name} exceeds VARCHAR({max_len})"
#                         )
#             elif t == "BOOLEAN":
#                 if not isinstance(val, bool):
#                     raise ExecutionError(f"Type error: {table.name}.{col_def.name} expects BOOLEAN")
#             else:
#                 raise ExecutionError(f"Unsupported type: {t}")

#     def _resolve_select_column(self, from_table: str, colref: ColumnRef) -> str:
#         """
#         Returns the real column name to read from a row dict.
#         Enforces that qualifiers match FROM table in Step 4.
#         """
#         if colref.table is not None and colref.table != from_table:
#             raise ExecutionError(
#                 f"Only single-table SELECT supported in Step 4; got qualified column {colref.table}.{colref.column}"
#             )
#         return colref.column

#     # ---------- INSERT ----------

#     def _insert(self, stmt: Insert) -> CommandOk:
#         table = self.catalog.require_table(stmt.table_name)

#         # validate columns exist
#         table_cols = table.column_names()
#         for c in stmt.columns:
#             if c not in table_cols:
#                 raise ExecutionError(f"Unknown column in INSERT: {stmt.table_name}.{c}")

#         # build full row with missing columns as None
#         row: dict[str, Any] = {c.name: None for c in table.columns}
#         for c, v in zip(stmt.columns, stmt.values):
#             row[c] = v

#         self._validate_insert_types(table, row)

#         heap = HeapTable.open(self.db_dir, stmt.table_name)
#         heap.insert(row)

#         return CommandOk(rows_affected=1, message="1 row inserted")

#     # ---------- SELECT (single table scan) ----------

#     def _row_matches_where(self, from_table: str, row: dict[str, Any], stmt: Select) -> bool:
#         if stmt.where is None:
#             return True
#         for cond in stmt.where.conditions:
#             if cond.op != "=":
#                 raise ExecutionError("Only '=' is supported in WHERE in Step 4")
#             col_name = self._resolve_select_column(from_table, cond.left)
#             if row.get(col_name) != cond.right:
#                 return False
#         return True

#     def _select(self, stmt: Select) -> QueryResult:
#         if stmt.joins:
#             raise ExecutionError("JOIN not implemented yet (comes later)")

#         table = self.catalog.require_table(stmt.from_table)
#         heap = HeapTable.open(self.db_dir, stmt.from_table)

#         # Determine output columns
#         if stmt.columns is None:  # "*"
#             out_cols = [c.name for c in table.columns]
#         else:
#             out_cols = [self._resolve_select_column(stmt.from_table, c) for c in stmt.columns]

#             # validate selected columns exist
#             table_cols = table.column_names()
#             for c in out_cols:
#                 if c not in table_cols:
#                     raise ExecutionError(f"Unknown column in SELECT: {stmt.from_table}.{c}")

#         rows_out: list[list[Any]] = []
#         for row in heap.scan():
#             if not self._row_matches_where(stmt.from_table, row, stmt):
#                 continue
#             rows_out.append([row.get(c) for c in out_cols])

#         return QueryResult(columns=out_cols, rows=rows_out)
    
#step4changesabove

# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path

# from ..ast import CreateIndex, CreateTable, Statement
# from ..catalog import Catalog, IndexMeta, TableMeta
# from ..errors import ExecutionError
# from ..result import CommandOk


# @dataclass
# class Executor:
#     db_dir: Path
#     catalog: Catalog

#     def execute(self, stmt: Statement):
#         if isinstance(stmt, CreateTable):
#             return self._create_table(stmt)
#         if isinstance(stmt, CreateIndex):
#             return self._create_index(stmt)

#         # Step 3: DML not implemented yet
#         raise ExecutionError(f"Not implemented yet (Step 3): {type(stmt).__name__}")

#     def _create_table(self, stmt: CreateTable) -> CommandOk:
#         self.catalog.validate_create_table(stmt.table_name, stmt.columns)

#         table = TableMeta(name=stmt.table_name, columns=stmt.columns, indexes={})
#         self.catalog.tables[stmt.table_name] = table
#         self.catalog.save(self.db_dir)

#         return CommandOk(rows_affected=0, message=f"Table created: {stmt.table_name}")

#     def _create_index(self, stmt: CreateIndex) -> CommandOk:
#         self.catalog.validate_create_index(stmt.index_name, stmt.table_name, stmt.column_name)

#         idx = IndexMeta(name=stmt.index_name, table_name=stmt.table_name, column_name=stmt.column_name)
#         self.catalog.indexes[stmt.index_name] = idx

#         table = self.catalog.require_table(stmt.table_name)
#         table.indexes[stmt.index_name] = idx

#         self.catalog.save(self.db_dir)
#         return CommandOk(rows_affected=0, message=f"Index created: {stmt.index_name} ON {stmt.table_name}({stmt.column_name})")