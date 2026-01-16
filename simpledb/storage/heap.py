from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ..errors import ExecutionError


@dataclass
class HeapTable:
    table_name: str
    data_path: Path
    meta_path: Path

    @classmethod
    def open(cls, db_dir: Path, table_name: str) -> "HeapTable":
        data_dir = db_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        data_path = data_dir / f"{table_name}.jsonl"
        meta_path = data_dir / f"{table_name}.meta.json"

        if not data_path.exists():
            data_path.write_text("", encoding="utf-8")

        if not meta_path.exists():
            meta_path.write_text(json.dumps({"next_rid": 1}, indent=2), encoding="utf-8")

        return cls(table_name=table_name, data_path=data_path, meta_path=meta_path)

    def _load_meta(self) -> dict[str, Any]:
        return json.loads(self.meta_path.read_text(encoding="utf-8"))

    def _save_meta(self, meta: dict[str, Any]) -> None:
        self.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def insert(self, row: dict[str, Any]) -> int:
        meta = self._load_meta()
        rid = int(meta["next_rid"])
        meta["next_rid"] = rid + 1
        self._save_meta(meta)

        stored = {"_rid": rid, **row}
        with self.data_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(stored, separators=(",", ":")) + "\n")
        return rid

    def tombstone(self, rid: int) -> None:
        rec = {"_op": "DELETE", "_rid": int(rid)}
        with self.data_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")

    def scan_active(self) -> Iterable[dict[str, Any]]:
        """
        Reads the whole table log and yields only rows that are not tombstoned.

        Implementation detail: we must see all tombstones before deciding a row is active,
        so we do a full pass.
        """
        deleted: set[int] = set()
        rows: list[dict[str, Any]] = []

        with self.data_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ExecutionError(f"Corrupt record in {self.data_path}: {e}") from e

                # tombstone record
                if obj.get("_op") == "DELETE":
                    rid = obj.get("_rid")
                    if isinstance(rid, int):
                        deleted.add(rid)
                    continue

                # legacy support (older steps wrote _deleted)
                if obj.get("_deleted") is True and isinstance(obj.get("_rid"), int):
                    deleted.add(obj["_rid"])
                    continue

                rows.append(obj)

        for r in rows:
            rid = r.get("_rid")
            if isinstance(rid, int) and rid not in deleted:
                yield r

    # Backward compatible name (older executor called heap.scan())
    def scan(self) -> Iterable[dict[str, Any]]:
        return self.scan_active()
#step6changes above(read md)

# from __future__ import annotations

# import json
# from dataclasses import dataclass
# from pathlib import Path
# from typing import Any, Iterable

# from ..errors import ExecutionError


# @dataclass
# class HeapTable:
#     table_name: str
#     data_path: Path
#     meta_path: Path

#     @classmethod
#     def open(cls, db_dir: Path, table_name: str) -> "HeapTable":
#         data_dir = db_dir / "data"
#         data_dir.mkdir(parents=True, exist_ok=True)

#         data_path = data_dir / f"{table_name}.jsonl"
#         meta_path = data_dir / f"{table_name}.meta.json"

#         if not data_path.exists():
#             data_path.write_text("", encoding="utf-8")

#         if not meta_path.exists():
#             meta_path.write_text(json.dumps({"next_rid": 1}, indent=2), encoding="utf-8")

#         return cls(table_name=table_name, data_path=data_path, meta_path=meta_path)

#     def _load_meta(self) -> dict[str, Any]:
#         return json.loads(self.meta_path.read_text(encoding="utf-8"))

#     def _save_meta(self, meta: dict[str, Any]) -> None:
#         self.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

#     def insert(self, row: dict[str, Any]) -> int:
#         meta = self._load_meta()
#         rid = int(meta["next_rid"])
#         meta["next_rid"] = rid + 1
#         self._save_meta(meta)

#         stored = {"_rid": rid, "_deleted": False, **row}
#         with self.data_path.open("a", encoding="utf-8") as f:
#             f.write(json.dumps(stored, separators=(",", ":")) + "\n")
#         return rid

#     def scan(self) -> Iterable[dict[str, Any]]:
#         """
#         Full table scan. Ignores rows with _deleted=true.
#         """
#         with self.data_path.open("r", encoding="utf-8") as f:
#             for line in f:
#                 line = line.strip()
#                 if not line:
#                     continue
#                 try:
#                     row = json.loads(line)
#                 except json.JSONDecodeError as e:
#                     raise ExecutionError(f"Corrupt row in {self.data_path}: {e}") from e
#                 if row.get("_deleted") is True:
#                     continue
#                 yield row