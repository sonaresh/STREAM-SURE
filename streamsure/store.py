from __future__ import annotations
import sqlite3, json, threading, os
from dataclasses import asdict
from pathlib import Path
from .models import Certificate, Outcome


class SQLiteStore:
    """Thread-safe SQLite evidence store optimized for append-heavy certification.

    v1.4.1 keeps WAL persistence and adds NORMAL synchronous mode, memory temp
    storage, a larger page cache, a busy timeout, and explicit batched writes.
    Certification semantics are unchanged; only persistence transport is tuned.
    """

    def __init__(self, path: str = "streamsure.db"):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._closed = False
        self.conn = sqlite3.connect(path, check_same_thread=False, timeout=30.0)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _ensure_open(self):
        if self._closed:
            raise RuntimeError("SQLiteStore is closed")

    def _init(self):
        with self._lock:
            if self.path != ":memory:":
                self.conn.execute("PRAGMA journal_mode=WAL;")
                # NORMAL preserves WAL durability while avoiding a full fsync per commit.
                self.conn.execute("PRAGMA synchronous=NORMAL;")
                self.conn.execute("PRAGMA wal_autocheckpoint=2000;")
            self.conn.execute("PRAGMA temp_store=MEMORY;")
            self.conn.execute("PRAGMA cache_size=-32768;")  # ~32 MiB
            self.conn.execute("PRAGMA busy_timeout=5000;")
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS certificates(
              certificate_id TEXT PRIMARY KEY,
              state_id TEXT NOT NULL,
              state_version INTEGER NOT NULL,
              decision_id TEXT NOT NULL,
              decision_class INTEGER NOT NULL,
              outcome TEXT NOT NULL,
              issued_at REAL NOT NULL,
              digest TEXT NOT NULL,
              payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cert_state ON certificates(state_id,state_version);
            CREATE TABLE IF NOT EXISTS consumers(
              certificate_id TEXT NOT NULL,
              consumer_id TEXT NOT NULL,
              UNIQUE(certificate_id, consumer_id)
            );
            CREATE TABLE IF NOT EXISTS repairs(
              old_certificate_id TEXT NOT NULL,
              new_certificate_id TEXT NOT NULL,
              repaired_at REAL NOT NULL,
              UNIQUE(old_certificate_id,new_certificate_id)
            );
            """)
            self.conn.commit()

    @staticmethod
    def _row(cert: Certificate):
        d = asdict(cert)
        d["outcome"] = cert.outcome.value
        return (
            cert.certificate_id, cert.state_id, cert.state_version, cert.decision_id,
            cert.decision_class, cert.outcome.value, cert.issued_at, cert.digest,
            json.dumps(d, sort_keys=True, separators=(",", ":")),
        )

    def save_certificate(self, cert: Certificate):
        self.save_certificates([cert])

    def save_certificates(self, certs: list[Certificate]):
        """Persist many certificates in one SQLite transaction."""
        self._ensure_open()
        if not certs:
            return
        rows = [self._row(c) for c in certs]
        with self._lock:
            self.conn.executemany(
                "INSERT OR REPLACE INTO certificates VALUES(?,?,?,?,?,?,?,?,?)", rows
            )
            self.conn.commit()

    def get_certificate(self, certificate_id: str) -> Certificate | None:
        self._ensure_open()
        with self._lock:
            row = self.conn.execute(
                "SELECT payload FROM certificates WHERE certificate_id=?", (certificate_id,)
            ).fetchone()
        if not row:
            return None
        d = json.loads(row[0]); d["outcome"] = Outcome(d["outcome"])
        return Certificate(**d)

    def latest_for_state(self, state_id: str) -> Certificate | None:
        self._ensure_open()
        with self._lock:
            row = self.conn.execute(
                "SELECT payload FROM certificates WHERE state_id=? ORDER BY issued_at DESC LIMIT 1",
                (state_id,),
            ).fetchone()
        if not row:
            return None
        d = json.loads(row[0]); d["outcome"] = Outcome(d["outcome"])
        return Certificate(**d)

    def register_consumer(self, certificate_id: str, consumer_id: str):
        self._ensure_open()
        with self._lock:
            self.conn.execute("INSERT OR IGNORE INTO consumers VALUES(?,?)", (certificate_id, consumer_id))
            self.conn.commit()

    def consumers(self, certificate_id: str) -> list[str]:
        self._ensure_open()
        with self._lock:
            return [r[0] for r in self.conn.execute(
                "SELECT consumer_id FROM consumers WHERE certificate_id=? ORDER BY consumer_id", (certificate_id,)
            )]

    def register_repair(self, old_id: str, new_id: str, repaired_at: float):
        self._ensure_open()
        with self._lock:
            self.conn.execute("INSERT OR IGNORE INTO repairs VALUES(?,?,?)", (old_id, new_id, repaired_at))
            self.conn.commit()

    def close(self):
        with self._lock:
            if self._closed: return
            try:
                self.conn.commit()
                if self.path != ":memory:":
                    try: self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                    except sqlite3.DatabaseError: pass
            finally:
                self.conn.close(); self._closed = True

    def __enter__(self):
        self._ensure_open(); return self

    def __exit__(self, exc_type, exc, tb):
        self.close(); return False
