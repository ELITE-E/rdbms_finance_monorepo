Step 5 — Constraints Enforcement on INSERT (PK / UNIQUE / NOT NULL) (IMPLEMENTED)
Step Goal
Enforce basic data integrity during INSERT:

NOT NULL
PRIMARY KEY (implies UNIQUE + NOT NULL)
UNIQUE (with SQL-like behavior: multiple NULL allowed)
What was implemented
Constraint checks added to INSERT execution:
NOT NULL check
PRIMARY KEY presence + uniqueness
UNIQUE uniqueness (skips NULL values)
Public API changed
None (still db.execute(sql)), but INSERT now raises ConstraintError for violations.
Files changed
simpledb/exec/executor.py
Tests added: tests/test_step5_constraints.py
Code Changes
simpledb/exec/executor.py (updated)
Only showing the relevant additions/changes (keep the rest from Step 4 as-is).