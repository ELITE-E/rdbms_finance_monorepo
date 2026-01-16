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

finance_tracker_project/
│
├── pyproject.toml             # Project metadata and CLI entry point
├── requirements.txt           # fastapi, uvicorn, jinja2, pyjwt, passlib[bcrypt]
│
├── simpledb/                  # THE RDBMS LIBRARY
│   ├── __init__.py            # Public API (Database, Result types, Errors)
│   ├── __main__.py            # Logic for 'python -m simpledb'
│   ├── ast.py                 # Abstract Syntax Tree node definitions
│   ├── catalog.py             # Schema metadata & JSON persistence
│   ├── db.py                  # Main Database class (Public API entry)
│   ├── errors.py              # Custom Exception hierarchy
│   ├── lexer.py               # SQL Tokenizer (Lexical Analysis)
│   ├── parser.py              # Recursive-descent SQL Parser
│   ├── repl.py                # Interactive CLI (formerly repl.py)
│   ├── result.py              # QueryResult and CommandOk dataclasses
│   │
│   ├── exec/                  # EXECUTION ENGINE
│   │   ├── __init__.py
│   │   ├── executor.py        # Central DDL/DML execution logic
│   │   └── join.py            # Inner Join (Nested-loop & Index-nested-loop)
│   │
│   ├── index/                 # INDEXING SUBSYSTEM
│   │   ├── __init__.py
│   │   └── hash_index.py      # Persisted Hash Index (Equality lookups)
│   │
│   └── storage/               # STORAGE SUBSYSTEM (The "Heap")
│       ├── __init__.py
│       ├── heap.py            # Core storage coordinator (JSONL)
│       ├── rid_directory.py   # RID-to-Offset mapping (Random access)
│       └── tombstones.py      # Logical deletion tracking
│
├── app/                       # THE FINANCE TRACKER WEB APP
│   ├── __init__.py
│   ├── main.py                # FastAPI entry point & app factory
│   ├── dependencies.py        # Auth middleware (get_current_user)
│   ├── db_session.py          # Singleton DB instance + Global Thread Lock
│   ├── db_init.py             # App-specific Schema & Index creator
│   ├── security.py            # Password hashing & JWT logic
│   ├── settings.py            # JWT Secrets, Cookie names, and Paths
│   ├── sql_utils.py           # SQL Quoting & Escaping (Security layer)
│   │
│   ├── routes/                # WEB ENDPOINTS
│   │   ├── __init__.py
│   │   ├── auth.py            # Register, Login, Logout
│   │   ├── categories.py      # Category CRUD
│   │   ├── dashboard.py       # Analytics view
│   │   ├── pages.py           # Public landing page
│   │   ├── profile.py         # User settings (Email/Password)
│   │   └── transactions.py    # Ledger CRUD & Filtering
│   │
│   └── services/              # BUSINESS LOGIC
│       ├── __init__.py
│       └── analytics.py       # Python-side Aggregation & Calculations
│
├── templates/                 # JINJA2 HTML VIEWS
│   ├── base.html              # Layout & Flash Messages
│   ├── landing.html           # Public Home Page
│   ├── login.html             # Auth
│   ├── register.html          # Auth
│   ├── dashboard.html         # Main View + Chart.js
│   ├── categories.html        # Category List
│   ├── transactions.html      # Ledger History + Filter
│   ├── transaction_new.html   # Add Form
│   ├── transaction_edit.html  # Edit Form
│   └── profile.html           # Settings
│
└── db/                        # DATA PERSISTENCE (Auto-generated)
    ├── catalog.json           # Global Table/Index Metadata
    ├── data/                  # Table JSONL files and Directories
    │   ├── users.jsonl
    │   ├── users.dir.json
    │   ├── transactions.jsonl
    │   └── ...
    └── indexes/               # Persisted Hash Index files
        ├── idx_users_email.json
        └── ...

        Below is a clean **mono-repo layout** that contains **both** projects under one root, with **consistent tooling** (one virtualenv, one set of lint/format configs, unified run commands). I’ll include **all existing implemented files** exactly as we built them, and I’ll clearly mark the small set of **new “tooling glue” files** you’d add at the repo root.

---

# Mono-repo layout (recommended)

```
finance-tracker-monorepo/
  README.md                          # (NEW) root readme with quickstart commands
  pyproject.toml                     # (NEW) tooling config (ruff/black/pytest/mypy), not packaging
  .gitignore                         # (NEW) ignore venv + DB runtime files
  Makefile                           # (NEW) common commands: install, run-repl, run-web, format, lint

  simple_rdbms/                      # (EXISTING project, unchanged)
    pyproject.toml                   # (EXISTING) packaging for simpledb + console script
    repl.py                          # (EXISTING) interactive shell
    simpledb/
      __init__.py
      __main__.py
      ast.py
      catalog.py
      db.py
      errors.py
      lexer.py
      parser.py
      result.py
      exec/
        executor.py
        join.py
      index/
        hash_index.py
      storage/
        heap.py
        rid_directory.py
        tombstones.py

  finance_tracker/                   # (EXISTING app, unchanged)
    app/
      __init__.py
      main.py
      settings.py
      db_core.py
      db_init.py
      deps.py
      security.py
      sql.py
      repos/
        __init__.py
        users_repo.py
        categories_repo.py
        transactions_repo.py
      routes/
        __init__.py
        pages.py
        auth.py
        dashboard.py
        categories.py
        transactions.py
      services/
        dashboard_service.py
    templates/
      base.html
      login.html
      register.html
      dashboard.html
      categories.html
      transactions.html
      transaction_new.html
      transaction_edit.html
    static/
      # optional (may be empty)

    db/                              # runtime-created SimpleDB files (SHOULD BE GITIGNORED)
      # catalog.json, data/, indexes/, etc.
```

This keeps your existing code intact, but gives you **one root** to manage:
- install/dev env
- formatting/linting
- running either the REPL or the web app

---

# “Consistent tooling” (what it means)
You work from the repo root, create **one** venv, then install:
- your RDBMS library (`simple_rdbms`) in editable mode
- the finance app dependencies (FastAPI, Jinja2, etc.)

Then you can run:
- the RDBMS REPL
- the finance web server
from the same environment.

---

# New root-level tooling files (minimal and practical)

## 1) `finance-tracker-monorepo/.gitignore` (NEW)
Key point: ignore the app’s runtime DB folder.
```
.venv/
__pycache__/
*.pyc

# runtime DB files for the web app demo
finance_tracker/db/

# optional editor stuff
.vscode/
.idea/
.DS_Store
```

## 2) `finance-tracker-monorepo/pyproject.toml` (NEW, tooling only)
This file is **not** for packaging the whole monorepo; it’s only for shared tool configs.
Example sections you might put here:
- `[tool.ruff]`
- `[tool.black]`
- `[tool.pytest.ini_options]`

## 3) `finance-tracker-monorepo/Makefile` (NEW)
Provides “one-command” workflows:
- `make venv`
- `make install`
- `make repl`
- `make web`
- `make format`
- `make lint`

---

# Root-level workflow (how you’d use it)

From `finance-tracker-monorepo/`:

1) Create env + install everything:
```bash
python -m venv .venv
source .venv/bin/activate

pip install -e ./simple_rdbms
pip install fastapi uvicorn jinja2 pyjwt passlib[bcrypt]
```

2) Run REPL:
```bash
python simple_rdbms/repl.py ./some_db_dir
# or (because you added packaging):
python -m simpledb ./some_db_dir
```

3) Run web app:
```bash
cd finance_tracker
uvicorn app.main:app --reload --workers 1
```

---

If you want, I can provide the exact contents of the **root** `README.md`, `pyproject.toml` (tooling-only), and `Makefile` matching this mono-repo so you can literally paste them in and run immediately.