from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .catalog import Catalog
from .exec.executor import Executor
from .parser import parse_sql


@dataclass
class Database:
    root_dir: Path
    catalog: Catalog

    @classmethod
    def open(cls, path: str | Path) -> "Database":
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        catalog = Catalog.load(root)
        return cls(root_dir=root, catalog=catalog)

    def execute(self, sql: str):
        stmt = parse_sql(sql)
        ex = Executor(db_dir=self.root_dir, catalog=self.catalog)
        return ex.execute(stmt)
#step4changes above

# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path

# from .catalog import Catalog
# from .exec.executor import Executor
# from .parser import parse_sql


# @dataclass
# class Database:
#     """
#     SimpleDB entrypoint.

#     Step 3:
#       - tokenize + parse
#       - catalog load/save
#       - executes CREATE TABLE / CREATE INDEX
#     """
#     root_dir: Path
#     catalog: Catalog

#     @classmethod
#     def open(cls, path: str | Path) -> "Database":
#         root = Path(path)
#         root.mkdir(parents=True, exist_ok=True)
#         catalog = Catalog.load(root)
#         return cls(root_dir=root, catalog=catalog)

#     def execute(self, sql: str):
#         stmt = parse_sql(sql)
#         ex = Executor(db_dir=self.root_dir, catalog=self.catalog)
#         return ex.execute(stmt)

#------------step3change above


# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path

# from .parser import parse_sql
# from .result import CommandOk


# @dataclass
# class Database:
#     """
#     SimpleDB entrypoint.

#     Step 2:
#       - tokenize + parse works
#       - execution engine not implemented yet
#     """
#     root_dir: Path

#     @classmethod
#     def open(cls, path: str | Path) -> "Database":
#         root = Path(path)
#         root.mkdir(parents=True, exist_ok=True)
#         return cls(root_dir=root)

#     def execute(self, sql: str):
#         stmt = parse_sql(sql)
#         return CommandOk(message=f"OK (parsed: {type(stmt).__name__})")



# from __future__ import annotations

# from dataclasses import dataclass
# from pathlib import Path

# from .errors import ExecutionError
# from .lexer import tokenize
# from .result import CommandOk


# @dataclass
# class Database:
#     """
#     SimpleDB entrypoint.

#     Current step:
#       - supports lexing via execute(), but does not parse/execute yet.
#     """
#     root_dir: Path

#     @classmethod
#     def open(cls, path: str | Path) -> "Database":
#         root = Path(path)
#         root.mkdir(parents=True, exist_ok=True)
#         return cls(root_dir=root)

#     def execute(self, sql: str):
#         """
#         Later steps: tokenize -> parse -> execute -> return QueryResult / CommandOk.

#         For now (Step 1): only tokenize to validate SQL-like input shape.
#         """
#         _ = tokenize(sql)  # raises SqlSyntaxError if invalid tokenization
#         # Placeholder until parser+executor arrive.
#         return CommandOk(message="OK (lexed)")