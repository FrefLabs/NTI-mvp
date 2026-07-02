"""SQLite-backed response cache.

The ERS specifies MariaDB; SQLite is a deliberate MVP adjustment. The database stores cached yfinance payloads so repeated
requests within the TTL don't hit Yahoo Finance again.
"""

import json
import sqlite3
import time
from typing import Any

from .config import CACHE_TTL_SECONDS, DATABASE_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_cache (
    cache_key  TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    fetched_at REAL NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(_SCHEMA)
    return conn


def cache_get(key: str) -> Any | None:
    """Return the cached payload for *key* if it is still fresh."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload, fetched_at FROM api_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
    if row is None:
        return None
    payload, fetched_at = row
    if time.time() - fetched_at > CACHE_TTL_SECONDS:
        return None
    return json.loads(payload)


def cache_set(key: str, payload: Any) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO api_cache (cache_key, payload, fetched_at)"
            " VALUES (?, ?, ?)",
            (key, json.dumps(payload), time.time()),
        )
