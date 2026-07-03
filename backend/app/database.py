"""Permanent SQLite storage layer.

The ERS specifies MariaDB; SQLite is a deliberate MVP adjustment. Market
data fetched from yfinance is accumulated permanently in ``market_data``
(no TTL): subsequent requests are served from disk and only the missing
tail is fetched from Yahoo Finance.
"""

import json
import sqlite3
import time
from typing import Any

from .config import DATABASE_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_data (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker    TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open      REAL,
    high      REAL,
    low       REAL,
    close     REAL,
    volume    INTEGER,
    interval  TEXT NOT NULL,
    UNIQUE (ticker, timestamp, interval)
);
CREATE INDEX IF NOT EXISTS idx_market_data_lookup
    ON market_data (ticker, interval, timestamp);

CREATE TABLE IF NOT EXISTS ticker_meta (
    ticker       TEXT PRIMARY KEY,
    name         TEXT,
    sector       TEXT,
    industry     TEXT,
    market_cap   INTEGER,
    payload_json TEXT,
    updated_at   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL,
    signal          TEXT NOT NULL,
    confidence      INTEGER NOT NULL,
    score           REAL NOT NULL,
    indicators_json TEXT NOT NULL,
    as_of           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news_cache (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker       TEXT NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT,
    url          TEXT,
    publisher    TEXT,
    published_at TEXT,
    fetched_at   REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_news_cache_ticker ON news_cache (ticker);

CREATE TABLE IF NOT EXISTS sync_meta (
    ticker    TEXT NOT NULL,
    interval  TEXT NOT NULL,
    synced_at REAL NOT NULL,
    UNIQUE (ticker, interval)
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def init_db() -> None:
    with _connect():
        pass


# --- market_data ---------------------------------------------------------


def upsert_market_data(ticker: str, interval: str, rows: list[dict[str, Any]]) -> None:
    with _connect() as conn:
        conn.executemany(
            "INSERT INTO market_data"
            " (ticker, timestamp, open, high, low, close, volume, interval)"
            " VALUES (:ticker, :timestamp, :open, :high, :low, :close, :volume, :interval)"
            " ON CONFLICT (ticker, timestamp, interval) DO UPDATE SET"
            " open = excluded.open, high = excluded.high, low = excluded.low,"
            " close = excluded.close, volume = excluded.volume",
            [{**row, "ticker": ticker, "interval": interval} for row in rows],
        )


def get_market_data(
    ticker: str,
    interval: str,
    start: str | None = None,
    end: str | None = None,
) -> list[dict[str, Any]]:
    query = (
        "SELECT timestamp, open, high, low, close, volume FROM market_data"
        " WHERE ticker = ? AND interval = ?"
    )
    params: list[Any] = [ticker, interval]
    if start is not None:
        query += " AND timestamp >= ?"
        params.append(start)
    if end is not None:
        query += " AND timestamp <= ?"
        params.append(end)
    query += " ORDER BY timestamp"
    with _connect() as conn:
        return [dict(row) for row in conn.execute(query, params)]


def get_coverage(ticker: str, interval: str) -> tuple[str | None, str | None, float | None]:
    """(first_timestamp, last_timestamp, synced_at) for a ticker/interval."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT MIN(timestamp), MAX(timestamp) FROM market_data"
            " WHERE ticker = ? AND interval = ?",
            (ticker, interval),
        ).fetchone()
        sync = conn.execute(
            "SELECT synced_at FROM sync_meta WHERE ticker = ? AND interval = ?",
            (ticker, interval),
        ).fetchone()
    return row[0], row[1], sync[0] if sync else None


def mark_synced(ticker: str, interval: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sync_meta (ticker, interval, synced_at) VALUES (?, ?, ?)"
            " ON CONFLICT (ticker, interval) DO UPDATE SET synced_at = excluded.synced_at",
            (ticker, interval, time.time()),
        )


def has_market_data(ticker: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM market_data WHERE ticker = ? LIMIT 1", (ticker,)
        ).fetchone()
    return row is not None


def list_known_tickers() -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ticker FROM market_data ORDER BY ticker"
        ).fetchall()
    return [row[0] for row in rows]


# --- ticker_meta ----------------------------------------------------------


def get_ticker_meta(ticker: str, max_age_seconds: float | None = None) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM ticker_meta WHERE ticker = ?", (ticker,)
        ).fetchone()
    if row is None:
        return None
    if max_age_seconds is not None and time.time() - row["updated_at"] > max_age_seconds:
        return None
    meta = dict(row)
    meta["payload"] = json.loads(meta.pop("payload_json") or "{}")
    return meta


def upsert_ticker_meta(ticker: str, payload: dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO ticker_meta"
            " (ticker, name, sector, industry, market_cap, payload_json, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (ticker) DO UPDATE SET"
            " name = excluded.name, sector = excluded.sector,"
            " industry = excluded.industry, market_cap = excluded.market_cap,"
            " payload_json = excluded.payload_json, updated_at = excluded.updated_at",
            (
                ticker,
                payload.get("name"),
                payload.get("sector"),
                payload.get("industry"),
                payload.get("market_cap"),
                json.dumps(payload),
                time.time(),
            ),
        )


# --- prediction_log -------------------------------------------------------


def log_prediction(
    ticker: str,
    signal: str,
    confidence: int,
    score: float,
    indicators: dict[str, Any],
    as_of: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO prediction_log"
            " (ticker, signal, confidence, score, indicators_json, as_of)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (ticker, signal, confidence, score, json.dumps(indicators), as_of),
        )


# --- news_cache -----------------------------------------------------------


def get_cached_news(ticker: str, max_age_seconds: float) -> list[dict[str, Any]] | None:
    """Cached news for *ticker*, or None if the cache is missing or stale."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT MAX(fetched_at) FROM news_cache WHERE ticker = ?", (ticker,)
        ).fetchone()
        if row[0] is None or time.time() - row[0] > max_age_seconds:
            return None
        rows = conn.execute(
            "SELECT title, description, url, publisher, published_at"
            " FROM news_cache WHERE ticker = ? ORDER BY published_at DESC, id",
            (ticker,),
        ).fetchall()
    return [dict(r) for r in rows]


def replace_news(ticker: str, items: list[dict[str, Any]]) -> None:
    now = time.time()
    with _connect() as conn:
        conn.execute("DELETE FROM news_cache WHERE ticker = ?", (ticker,))
        conn.executemany(
            "INSERT INTO news_cache"
            " (ticker, title, description, url, publisher, published_at, fetched_at)"
            " VALUES (:ticker, :title, :description, :url, :publisher, :published_at, :fetched_at)",
            [{**item, "ticker": ticker, "fetched_at": now} for item in items],
        )
