"""Market data layer: quotes, charts, fundamentals, news and search.

All Yahoo Finance access goes through this module. OHLCV data is stored
permanently in SQLite (``market_data``): before calling yfinance the
requested window is checked against the database and only the missing tail
is fetched. Errors from yfinance are wrapped in :class:`MarketDataError`
so the API layer can return a clean 502 instead of a stack trace (RNF-14).
"""

import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import yfinance as yf

from . import database
from .config import CHART_RANGES, DEFAULT_TICKERS

NEWS_CACHE_SECONDS = 3600
META_CACHE_SECONDS = 86400

_TICKER_RE = re.compile(r"^[A-Z0-9.\-^=]{1,12}$")

_INTERVAL_SECONDS = {
    "5m": 300,
    "30m": 1800,
    "1d": 86400,
    "1wk": 604800,
}

_PERIOD_DAYS = {
    "1d": 1,
    "5d": 7,
    "1mo": 31,
    "6mo": 183,
    "1y": 366,
    "2y": 732,
    "5y": 1830,
}


class UnknownTickerError(ValueError):
    """Raised when a ticker does not exist on Yahoo Finance."""


class MarketDataError(RuntimeError):
    """Raised when yfinance fails or returns unusable data."""


def _validate(ticker: str) -> str:
    symbol = ticker.upper()
    if not _TICKER_RE.match(symbol):
        raise UnknownTickerError(symbol)
    return symbol


def _clean(value: Any) -> Any:
    """Convert NaN/inf to None so payloads are valid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _frame_to_rows(history: pd.DataFrame) -> list[dict[str, Any]]:
    index = history.index
    if index.tz is None:
        index = index.tz_localize("UTC")
    else:
        index = index.tz_convert("UTC")
    rows = []
    for ts, row in zip(index, history.itertuples()):
        volume = getattr(row, "Volume", None)
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "open": _clean(round(float(row.Open), 4)),
                "high": _clean(round(float(row.High), 4)),
                "low": _clean(round(float(row.Low), 4)),
                "close": _clean(round(float(row.Close), 4)),
                "volume": int(volume) if volume is not None and math.isfinite(volume) else None,
            }
        )
    return rows


def _fetch_history(symbol: str, **kwargs) -> pd.DataFrame:
    try:
        return yf.Ticker(symbol).history(**kwargs)
    except Exception as exc:
        raise MarketDataError(f"Could not fetch history for {symbol}") from exc


def _is_fresh(interval: str, synced_at: float | None) -> bool:
    if synced_at is None:
        return False
    age = _now().timestamp() - synced_at
    if interval in ("1d", "1wk"):
        return age < _INTERVAL_SECONDS["1d"]
    return age < _INTERVAL_SECONDS[interval]


def ensure_market_data(
    symbol: str,
    interval: str,
    *,
    period: str | None = None,
    start: datetime | None = None,
) -> None:
    """Guarantee that ``market_data`` covers the requested window, fetching
    only what is missing from yfinance and storing it before returning."""
    first, last, synced_at = database.get_coverage(symbol, interval)
    tolerance = timedelta(days=1 if interval in ("5m", "30m") else 10)
    explicit_start = start is not None
    if start is None and period is not None:
        start = _now() - timedelta(days=_PERIOD_DAYS[period])

    covers_start = first is not None and (
        start is None or datetime.fromisoformat(first) <= start + tolerance
    )
    if covers_start and _is_fresh(interval, synced_at):
        return

    if covers_start:
        last_dt = datetime.fromisoformat(last)
        if _now() - last_dt < timedelta(seconds=_INTERVAL_SECONDS[interval]):
            database.mark_synced(symbol, interval)
            return
        if interval in ("5m", "30m") and _now() - last_dt > timedelta(days=55):
            # yfinance only serves recent intraday data; refetch the window.
            history = _fetch_history(symbol, period=period or "5d", interval=interval)
        else:
            history = _fetch_history(symbol, start=last_dt, interval=interval)
    elif explicit_start:
        history = _fetch_history(symbol, start=start, interval=interval)
    else:
        # period-based fetch lets yfinance anchor to the last trading day
        # (a start= fetch over a weekend/holiday would come back empty).
        history = _fetch_history(symbol, period=period or "1y", interval=interval)

    if history.empty:
        if first is None:
            raise UnknownTickerError(symbol)
        database.mark_synced(symbol, interval)
        return

    database.upsert_market_data(symbol, interval, _frame_to_rows(history))
    database.mark_synced(symbol, interval)


def _ticker_exists(symbol: str) -> bool:
    if database.has_market_data(symbol) or database.get_ticker_meta(symbol):
        return True
    history = _fetch_history(symbol, period="5d", interval="1d")
    if history.empty:
        return False
    database.upsert_market_data(symbol, "1d", _frame_to_rows(history))
    return True


def _display_name(symbol: str) -> str:
    if symbol in DEFAULT_TICKERS:
        return DEFAULT_TICKERS[symbol]
    meta = database.get_ticker_meta(symbol)
    if meta and meta.get("name"):
        return meta["name"]
    return symbol


def get_quote(ticker: str) -> dict[str, Any]:
    """Current price plus daily context for *ticker* (RF-06)."""
    symbol = _validate(ticker)
    try:
        info = yf.Ticker(symbol).fast_info
        price = info["last_price"]
        previous_close = info["previous_close"]
    except Exception as exc:
        if not _ticker_exists(symbol):
            raise UnknownTickerError(symbol) from exc
        raise MarketDataError(f"Could not fetch quote for {symbol}") from exc

    if price is None or previous_close in (None, 0):
        if not _ticker_exists(symbol):
            raise UnknownTickerError(symbol)
        raise MarketDataError(f"Yahoo Finance returned no price for {symbol}")

    change = price - previous_close
    return {
        "ticker": symbol,
        "name": _display_name(symbol),
        "price": _clean(round(price, 4)),
        "previous_close": _clean(round(previous_close, 4)),
        "change": _clean(round(change, 4)),
        "change_percent": _clean(round(change / previous_close * 100, 4)),
        "currency": info.get("currency"),
        "day_high": _clean(info.get("day_high")),
        "day_low": _clean(info.get("day_low")),
        "volume": _clean(info.get("last_volume")),
        "fetched_at": _now().isoformat(),
    }


def get_chart(ticker: str, range_key: str) -> dict[str, Any]:
    """Historical OHLCV series for the interactive chart, served from the
    permanent ``market_data`` store (RF-04 / RF-22)."""
    symbol = _validate(ticker)
    if range_key not in CHART_RANGES:
        raise ValueError(f"Invalid range: {range_key}")
    period, interval = CHART_RANGES[range_key]
    ensure_market_data(symbol, interval, period=period)

    rows = database.get_market_data(symbol, interval)
    if not rows:
        raise UnknownTickerError(symbol)
    last_dt = datetime.fromisoformat(rows[-1]["timestamp"])
    window_start = (last_dt - timedelta(days=_PERIOD_DAYS[period])).isoformat()
    points = [
        {
            "time": row["timestamp"],
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
        }
        for row in rows
        if row["timestamp"] >= window_start
    ]
    return {
        "ticker": symbol,
        "range": range_key,
        "interval": interval,
        "points": points,
    }


def get_history_frame(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    """Historical data as a pandas DataFrame, for internal consumers
    (e.g. the prediction module). Served from ``market_data``."""
    symbol = _validate(ticker)
    ensure_market_data(symbol, interval, period=period, start=start)
    rows = database.get_market_data(
        symbol,
        interval,
        start=start.isoformat() if start else None,
        end=end.isoformat() if end else None,
    )
    if start is None and rows:
        last_dt = datetime.fromisoformat(rows[-1]["timestamp"])
        window_start = (last_dt - timedelta(days=_PERIOD_DAYS[period])).isoformat()
        rows = [row for row in rows if row["timestamp"] >= window_start]
    if not rows:
        raise MarketDataError(f"No historical data available for {symbol}")
    frame = pd.DataFrame(rows)
    frame.index = pd.to_datetime(frame.pop("timestamp"))
    frame.columns = ["Open", "High", "Low", "Close", "Volume"]
    return frame


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
    """Company fundamentals for *ticker*, cached in ``ticker_meta`` (RF-20)."""
    symbol = _validate(ticker)
    meta = database.get_ticker_meta(symbol, max_age_seconds=META_CACHE_SECONDS)
    if meta is not None and meta["payload"]:
        return meta["payload"]

    try:
        info = yf.Ticker(symbol).info
    except Exception as exc:
        raise MarketDataError(f"Could not fetch fundamentals for {symbol}") from exc

    if not info or info.get("symbol") is None:
        raise UnknownTickerError(symbol)

    payload: dict[str, Any] = {
        "ticker": symbol,
        "name": info.get("shortName") or info.get("longName") or _display_name(symbol),
    }
    for field, yf_key in _FUNDAMENTAL_FIELDS.items():
        payload[field] = _clean(info.get(yf_key))
    database.upsert_ticker_meta(symbol, payload)
    return payload


def get_news(ticker: str) -> list[dict[str, Any]]:
    """Recent news for *ticker*, cached in ``news_cache`` for one hour
    (RF-07 / RF-23)."""
    symbol = _validate(ticker)
    cached = database.get_cached_news(symbol, NEWS_CACHE_SECONDS)
    if cached is not None:
        return cached

    try:
        raw_items = yf.Ticker(symbol).news or []
    except Exception as exc:
        raise MarketDataError(f"Could not fetch news for {symbol}") from exc

    items = [item for item in (_normalize_news(raw) for raw in raw_items) if item]
    if not items and not _ticker_exists(symbol):
        raise UnknownTickerError(symbol)
    database.replace_news(symbol, items)
    return database.get_cached_news(symbol, NEWS_CACHE_SECONDS) or []


def _normalize_news(raw: dict[str, Any]) -> dict[str, Any] | None:
    content = raw.get("content") or raw
    title = content.get("title")
    if not title:
        return None
    url = content.get("canonicalUrl") or {}
    provider = content.get("provider") or {}
    published = content.get("pubDate") or raw.get("providerPublishTime")
    if isinstance(published, (int, float)):
        published = datetime.fromtimestamp(published, tz=timezone.utc).isoformat()
    return {
        "title": title,
        "description": content.get("summary") or content.get("description"),
        "url": url.get("url") if isinstance(url, dict) else raw.get("link"),
        "publisher": provider.get("displayName") or raw.get("publisher"),
        "published_at": published,
    }


def search_tickers(query: str) -> list[dict[str, Any]]:
    """Search Yahoo Finance for tickers matching *query*."""
    try:
        results = yf.Search(query, max_results=10).quotes or []
    except Exception as exc:
        raise MarketDataError(f"Ticker search failed for '{query}'") from exc
    return [
        {
            "ticker": item["symbol"],
            "name": item.get("shortname") or item.get("longname"),
            "type": item.get("quoteType"),
            "exchange": item.get("exchange"),
        }
        for item in results
        if item.get("symbol")
    ]


def refresh_daily_data(symbol: str) -> None:
    """Pull the missing daily bars for a ticker already present in the
    database. Used by the market-close scheduler job."""
    _, last, _ = database.get_coverage(symbol, "1d")
    if last is None:
        return
    history = _fetch_history(symbol, start=datetime.fromisoformat(last), interval="1d")
    if not history.empty:
        database.upsert_market_data(symbol, "1d", _frame_to_rows(history))
    database.mark_synced(symbol, "1d")
