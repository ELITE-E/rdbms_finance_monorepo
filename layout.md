simple_rdbms/
  README.md
  docs/
    steps/
      01_tokenizer.md
      02_parser.md
      03_catalog.md
      ...
  simpledb/
    __init__.py
    db.py              # Database.open(), db.execute()
    errors.py          # custom exceptions
    result.py          # QueryResult / CommandOk
    lexer.py           # SQL-like tokenizer
    parser.py          # parse -> AST
    ast.py             # AST node definitions
    catalog.py         # schema objects + catalog persistence
    storage/
      __init__.py
      heap.py          # table storage (file)
      codec.py         # row encode/decode
    index/
      __init__.py
      hash_index.py    # basic equality index
    exec/
      __init__.py
      executor.py      # executes AST against catalog/storage/index
      join.py          # join logic (nested loop first)
  repl.py              # interactive shell using the library
  tests/
    test_lexer.py
    test_parser.py
    ...

Roadmap (high-level steps, aligned to your confirmed Phase 1 SQL subset)
Tokenizer (lexegir) for the SQL-like language
Parser → produces an AST for each statement
Catalog / schema objects + persistence (store table definitions)
Storage engine (heap files) + row encoding/decoding
Executor for CRUD (table scans + WHERE = + AND)
Constraints: PRIMARY KEY / UNIQUE / NOT NULL enforcement
Basic indexing: CREATE INDEX, use for WHERE col = literal
JOIN: INNER JOIN equality (nested loop)
REPL wrapper (library-powered)
Finance app demo calling db.execute(...)