Step 6 — UPDATE + DELETE using append-only tombstones (IMPLEMENTED)
Step Goal
Add working:

UPDATE table SET ... [WHERE ...]
DELETE FROM table [WHERE ...]
…while keeping storage append-only (no file rewriting), by appending tombstone records.

What was implemented
Storage now supports tombstones:
Appended record: {"_op":"DELETE","_rid": <rid>}
Table scans now return only active rows (rows not tombstoned).
Executor now supports:
UPDATE (batch-validated, then append new row versions + tombstones for old rows)
DELETE (append tombstones)
Constraints are enforced on UPDATE too:
NOT NULL
PRIMARY KEY (unique + not null)
UNIQUE (NULLs ignored, SQL-like)
Key design note (important)
UPDATE creates a new physical row (new _rid) and tombstones the old _rid. Logical identity should be your PRIMARY KEY value, not _rid.