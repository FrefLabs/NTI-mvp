"""Application configuration, driven by environment variables."""

import os
from pathlib import Path

# Featured tickers shown by default in the UI (MVP R2 scope). Any valid
# Yahoo Finance ticker is accepted by the API; these are just the defaults.
DEFAULT_TICKERS: dict[str, str] = {
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

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parent.parent / "nti.db"))
)
SCHEDULER_TIME = os.getenv("SCHEDULER_TIME", "17:00")
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "America/Argentina/Buenos_Aires")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
API_PORT = int(os.getenv("API_PORT", "8000"))
