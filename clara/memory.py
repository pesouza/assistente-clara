from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

_DB_PATH = Path(__file__).with_name("home") / "clara.db"
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_DDL = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    type TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    meta TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_key_type ON memories(key, type);
"""


@dataclass(frozen=True)
class MemoryRecord:
    id: int
    created_at: datetime
    type: str
    key: str
    value: str
    meta: Optional[str]


class Memory:
    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path) if path else _DB_PATH
        self._local = threading.local()
        self._init()

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return self._local.conn

    def _init(self) -> None:
        with self._conn() as c:
            c.executescript(_DDL)

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        conn = self._conn()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def remember(self, type: str, key: str, value: str, meta: str | None = None) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO memories(type, key, value, meta) VALUES(?,?,?,?)
                ON CONFLICT(key, type) DO UPDATE SET
                  value=excluded.value,
                  meta=excluded.meta,
                  created_at=datetime('now')
                """,
                (type, key, value, meta),
            )

    def recall(self, type: str, key: str) -> Optional[MemoryRecord]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, created_at, type, key, value, meta FROM memories WHERE type=? AND key=?",
                (type, key),
            )
            row = cur.fetchone()
        if not row:
            return None
        return self._row_to_record(row)

    def recall_like(self, type: str, like: str, limit: int = 20) -> List[MemoryRecord]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT id, created_at, type, key, value, meta FROM memories WHERE type=? AND key LIKE ? ORDER BY id DESC LIMIT ?",
                (type, like, int(limit)),
            )
            return [self._row_to_record(row) for row in cur.fetchall()]

    def forget(self, type: str, key: str) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM memories WHERE type=? AND key=?", (type, key))

    def list_keys(self, type: str) -> List[str]:
        with self._cursor() as cur:
            cur.execute("SELECT key FROM memories WHERE type=? ORDER BY key", (type,))
            return [row["key"] for row in cur.fetchall()]

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn:
            try:
                conn.close()
            finally:
                self._local.conn = None

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            type=row["type"],
            key=row["key"],
            value=row["value"],
            meta=row["meta"] if "meta" in row else None,
        )
