Step 3 — Catalog (schema) + JSON persistence (IMPLEMENTED)
Step Goal
Make CREATE TABLE and CREATE INDEX actually change database state by storing schema metadata in a persistent catalog (JSON under the DB directory).

What was implemented
A Catalog that stores:
tables
columns (+ types + PK/UNIQUE/NOT NULL flags)
indexes (name → table + column)
JSON persistence:
auto-load on Database.open()
auto-save after DDL changes
Basic DDL execution:
CREATE TABLE ...
CREATE INDEX ... ON table(col)
Validation:
table name uniqueness
exactly 0 or 1 primary key column per table (Phase 1 simplification)
supported types validation (INTEGER, VARCHAR(n), TEXT, DATE, BOOLEAN)
index requires existing table + column
index names must be globally unique (simplifies lookups)
Public API added/changed
Database.open() now loads catalog
Database.execute() now executes DDL; non-DDL still raises “not implemented” (until Step 4+)
Files/modules added
simpledb/catalog.py
simpledb/exec/executor.py
tests + (optional) docs stub