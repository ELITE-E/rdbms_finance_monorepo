Step 4 — Data Storage (JSONL “heap files”) + INSERT + basic SELECT scans (IMPLEMENTED)
Step Goal
Persist table rows on disk (JSONL) and support first real DML:

INSERT INTO ...
SELECT ... FROM ... [WHERE ...] (single-table only, no JOIN yet)
What was implemented
Row storage per table: db_dir/data/<table>.jsonl
Per-table meta: db_dir/data/<table>.meta.json to track next_rid
A simple heap-table interface:
append-only inserts
full-table scan for SELECT
rows include internal fields: _rid, _deleted
DML execution:
INSERT validates table/columns + basic type checks
SELECT supports:
* or explicit column list
WHERE col = literal [AND ...]
qualified column refs like users.email (must match FROM table)
Explicit limitations (still not done)
UPDATE, DELETE execution (next steps)
JOIN execution (later step)
PK/UNIQUE/NOT NULL enforcement (Step 5)
Using indexes to speed up SELECT (later step)
