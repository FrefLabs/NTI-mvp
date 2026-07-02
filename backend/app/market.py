"""Market data layer: fetches quotes, charts and fundamentals from yfinance.

All Yahoo Finance access goes through this module. Errors from yfinance are
wrapped in :class:`MarketDataError` so the API layer can return a clean
error response instead of a stack trace (RNF-14).
"""

import math
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from .config import ALLOWED_TICKERS, CHART_RANGES
from .database import cache_get, cache_set


class UnknownTickerError(ValueError):
    """Raised when a ticker outside the allowed set is requested."""


class MarketDataError(RuntimeError):
    """Raised when yfinance fails or returns unusable data."""


def _validate(ticker: str) -> str:
    symbol = ticker.upper()
    if symbol not in ALLOWED_TICKERS:
        raise UnknownTickerError(symbol)
    return symbol


def _clean(value: Any) -> Any:
    """Convert NaN/inf to None so payloads are valid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def get_quote(ticker: str) -> dict[str, Any]:
    """Current price plus daily context for *ticker* (RF-06)."""
    symbol = _validate(ticker)
    cache_key = f"quote:{symbol}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        info = yf.Ticker(symbol).fast_info
        price = info["last_price"]
        previous_close = info["previous_close"]
    except UnknownTickerError:
        raise
    except Exception as exc:
        raise MarketDataError(f"Could not fetch quote for {symbol}") from exc

    if price is None or previous_close in (None, 0):
        raise MarketDataError(f"Yahoo Finance returned no price for {symbol}")

    change = price - previous_close
    payload = {
        "ticker": symbol,
        "name": ALLOWED_TICKERS[symbol],
        "price": _clean(round(price, 4)),
        "previous_close": _clean(round(previous_close, 4)),
        "change": _clean(round(change, 4)),
        "change_percent": _clean(round(change / previous_close * 100, 4)),
        "currency": info.get("currency"),
        "day_high": _clean(info.get("day_high")),
        "day_low": _clean(info.get("day_low")),
        "volume": _clean(info.get("last_volume")),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    cache_set(cache_key, payload)
    return payload


def get_chart(ticker: str, range_key: str) -> dict[str, Any]:
    """Historical OHLCV series for the interactive chart (RF-04 / RF-22)."""
    symbol = _validate(ticker)
    if range_key not in CHART_RANGES:
        raise ValueError(f"Invalid range: {range_key}")
    cache_key = f"chart:{symbol}:{range_key}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    period, interval = CHART_RANGES[range_key]
    try:
        history = yf.Ticker(symbol).history(period=period, interval=interval)
    except Exception as exc:
        raise MarketDataError(f"Could not fetch chart for {symbol}") from exc

    if history.empty:
        raise MarketDataError(f"Yahoo Finance returned no history for {symbol}")

    points = [
        {
            "time": index.isoformat(),
            "open": _clean(round(row["Open"], 4)),
            "high": _clean(round(row["High"], 4)),
            "low": _clean(round(row["Low"], 4)),
            "close": _clean(round(row["Close"], 4)),
            "volume": _clean(int(row["Volume"])) if math.isfinite(row["Volume"]) else None,
        }
        for index, row in history.iterrows()
    ]
    payload = {
        "ticker": symbol,
        "range": range_key,
        "interval": interval,
        "points": points,
    }
    cache_set(cache_key, payload)
    return payload


def get_history_frame(ticker: str, period: str = "1y", interval: str = "1d"):
    """Raw pandas DataFrame of historical data, for internal consumers
    (e.g. the prediction module). Not exposed over HTTP."""
    symbol = _validate(ticker)
    try:
        history = yf.Ticker(symbol).history(period=period, interval=interval)
    except Exception as exc:
        raise MarketDataError(f"Could not fetch history for {symbol}") from exc
    if history.empty:
        raise MarketDataError(f"Yahoo Finance returned no history for {symbol}")
    return history


_FUNDAMENTAL_FIELDS = {
    "sector": "sector",
    "industry": "industry",
    "website": "website",
    "market_cap": "marketCap",
    "trailing_pe": "trailingPE",
    "forward_pe": "forwardPE",
    "dividend_yield": "dividendYield",
    "beta": "beta",
    "fifty_two_week_high": "fiftyTwoWeekHigh",
    "fifty_two_week_low": "fiftyTwoWeekLow",
    "average_volume": "averageVolume",
    "long_business_summary": "longBusinessSummary",
}


def get_fundamentals(ticker: str) -> dict[str, Any]:
    """Company fundamentals for *ticker* (RF-20)."""
    symbol = _validate(ticker)
    cache_key = f"fundamentals:{symbol}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        info = yf.Ticker(symbol).info
    except Exception as exc:
        raise MarketDataError(f"Could not fetch fundamentals for {symbol}") from exc

    if not info or "symbol" not in info:
        raise MarketDataError(f"Yahoo Finance returned no fundamentals for {symbol}")

    payload: dict[str, Any] = {
        "ticker": symbol,
        "name": ALLOWED_TICKERS[symbol],
    }
    for field, yf_key in _FUNDAMENTAL_FIELDS.items():
        payload[field] = _clean(info.get(yf_key))
    cache_set(cache_key, payload)
    return payload
