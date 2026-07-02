"""Application configuration constants."""

from pathlib import Path

# The MVP is restricted to exactly these two tickers (MVP R2 scope).
ALLOWED_TICKERS: dict[str, str] = {
    "KO": "The Coca-Cola Company",
    "NVDA": "NVIDIA Corporation",
}

# Chart ranges accepted by the /chart endpoint, mapped to yfinance
# (period, interval) pairs (RF-04 / RF-22).
CHART_RANGES: dict[str, tuple[str, str]] = {
    "1d": ("1d", "5m"),
    "5d": ("5d", "30m"),
    "1mo": ("1mo", "1d"),
    "6mo": ("6mo", "1d"),
    "1y": ("1y", "1d"),
    "5y": ("5y", "1wk"),
}

DEFAULT_CHART_RANGE = "6mo"

# SQLite cache: avoids hammering Yahoo Finance on every request.
DATABASE_PATH = Path(__file__).resolve().parent.parent / "nti.db"
CACHE_TTL_SECONDS = 300
