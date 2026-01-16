Step 2 — Parser → AST (IMPLEMENTED)
Step Goal
Parse the token stream from Step 1 into an AST (Abstract Syntax Tree) for the confirmed Phase 1 SQL subset.

What we implemented (deliverables)
AST node definitions (simpledb/ast.py)
Recursive-descent parser (simpledb/parser.py)
Parser integrated into Database.execute() (it now tokenizes + parses)
Parser test suite (tests/test_parser.py)
Public API added/changed
New: simpledb.parser.parse_sql(sql: str) -> Statement
New: simpledb.parser.parse_script(sql: str) -> list[Statement] (handles ; separated input)
Changed: Database.execute() now parses (still does not execute yet)
What is supported in Step 2 (syntax)
DDL

CREATE TABLE t ( col TYPE [NOT NULL] [UNIQUE] [PRIMARY KEY], ... );
CREATE INDEX idx_name ON table_name(col_name);
DML

INSERT INTO t (c1, c2) VALUES (v1, v2);
SELECT * | col_list FROM t [JOIN t2 ON a=b]* [WHERE c=v [AND ...]];
UPDATE t SET c=v [, ...] [WHERE c=v [AND ...]];
DELETE FROM t [WHERE c=v [AND ...]];
WHERE conditions

only = and AND
literals: INT, 'STRING', true/false
Explicit limitations (by design, for now)
No FOREIGN KEY, no table-level constraints like UNIQUE (a,b)
No ORDER BY, GROUP BY, SUM, COUNT
No < > <= >=
No aliases (FROM transactions t) yet — use full table names in qualified columns (transactions.user_id)