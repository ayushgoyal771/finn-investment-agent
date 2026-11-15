"""Small durable store. One connection per operation; never shared across threads."""
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class Store:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def init(self):
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
              CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, at REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS item_state (id TEXT PRIMARY KEY, saved INTEGER NOT NULL DEFAULT 0,
                seen INTEGER NOT NULL DEFAULT 0);
              CREATE TABLE IF NOT EXISTS filings (id TEXT PRIMARY KEY, published_at TEXT NOT NULL, value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS signal_archive (id TEXT PRIMARY KEY, mode TEXT NOT NULL,
                published_at TEXT NOT NULL, value TEXT NOT NULL);
            """)
            db.execute("DELETE FROM cache WHERE at < ?", (time.time() - 30 * 86400,))
            db.execute("DELETE FROM filings WHERE published_at < datetime('now', '-90 days')")
            db.execute("DELETE FROM signal_archive WHERE published_at < datetime('now', '-90 days') AND id NOT IN (SELECT id FROM item_state WHERE saved=1)")

    def get(self, key, default=None):
        with self.connection() as db:
            row = db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def set(self, key, value):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO kv VALUES (?,?)", (key, json.dumps(value)))

    def cached(self, key, ttl):
        with self.connection() as db:
            row = db.execute("SELECT value,at FROM cache WHERE key=?", (key,)).fetchone()
        if row and time.time() - row["at"] <= ttl:
            return json.loads(row["value"])
        return None

    def cache(self, key, value):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (key, json.dumps(value), time.time()))

    def states(self):
        with self.connection() as db:
            return {r["id"]: {"saved": bool(r["saved"]), "seen": bool(r["seen"])}
                    for r in db.execute("SELECT * FROM item_state")}

    def state(self, item_id, saved=None, seen=None):
        with self.connection() as db:
            db.execute("INSERT OR IGNORE INTO item_state (id) VALUES (?)", (item_id,))
            if saved is not None:
                db.execute("UPDATE item_state SET saved=? WHERE id=?", (int(saved), item_id))
            if seen is not None:
                db.execute("UPDATE item_state SET seen=? WHERE id=?", (int(seen), item_id))

    def add_filings(self, items):
        with self.connection() as db:
            db.executemany("INSERT OR IGNORE INTO filings VALUES (?,?,?)",
                           [(x["id"], x["published_at"], json.dumps(x)) for x in items])

    def filings(self):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT value FROM filings ORDER BY published_at DESC")]

    def archive(self, mode, items):
        with self.connection() as db:
            db.executemany("INSERT OR REPLACE INTO signal_archive VALUES (?,?,?,?)",
                           [(x["id"], mode, x["published_at"], json.dumps(x)) for x in items])

    def archived(self, mode):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT value FROM signal_archive WHERE mode=?", (mode,))]
