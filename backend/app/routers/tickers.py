"""HTTP endpoints for ticker market data
(RF-04, RF-06, RF-07, RF-20, RF-22, RF-23)."""

import csv
import io
from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from .. import database, market
from ..config import CHART_RANGES, DEFAULT_CHART_RANGE, DEFAULT_TICKERS
from ..prediction import predict, run_backtest

router = APIRouter(prefix="/api/tickers", tags=["tickers"])


def _handle(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except market.UnknownTickerError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{exc}' not found on Yahoo Finance.",
        ) from exc
    except market.MarketDataError as exc:
        # RNF-14: upstream failures become a clean JSON error, not a 500.
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _validate_range(range_key: str) -> None:
    if range_key not in CHART_RANGES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid range '{range_key}'. Valid ranges: "
            + ", ".join(CHART_RANGES),
        )


@router.get("")
def list_tickers() -> list[dict[str, str]]:
    return [
        {"ticker": symbol, "name": name}
        for symbol, name in sorted(DEFAULT_TICKERS.items())
    ]


@router.get("/{ticker}/quote")
def quote(ticker: str) -> dict:
    return _handle(market.get_quote, ticker)


@router.get("/{ticker}/chart")
def chart(
    ticker: str,
    range: str = Query(DEFAULT_CHART_RANGE, alias="range"),
) -> dict:
    _validate_range(range)
    return _handle(market.get_chart, ticker, range)


@router.get("/{ticker}/chart/export")
def chart_export(
    ticker: str,
    range: str = Query(DEFAULT_CHART_RANGE, alias="range"),
) -> Response:
    """Historical OHLCV data as a downloadable CSV file."""
    _validate_range(range)
    data = _handle(market.get_chart, ticker, range)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
    for point in data["points"]:
        writer.writerow(
            [
                point["time"],
                point["open"],
                point["high"],
                point["low"],
                point["close"],
                point["volume"],
            ]
        )
    filename = f"{data['ticker']}_{range}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{ticker}/fundamentals")
def fundamentals(ticker: str) -> dict:
    return _handle(market.get_fundamentals, ticker)


@router.get("/{ticker}/news")
def news(ticker: str) -> list[dict]:
    """Recent news for the ticker, cached for one hour (RF-07, RF-23)."""
    return _handle(market.get_news, ticker)


@router.get("/{ticker}/prediction")
def prediction(ticker: str) -> dict:
    """AI buy/hold/sell suggestion with confidence (RF-08, RF-15, RF-24)."""
    result = asdict(_handle(predict, ticker))
    database.log_prediction(
        ticker=result["ticker"],
        signal=result["signal"],
        confidence=result["confidence"],
        score=result["score"],
        indicators=result["indicators"],
        as_of=result["as_of"],
    )
    return result


class BacktestRequest(BaseModel):
    start_date: date
    end_date: date
    initial_capital: float = Field(default=10000, gt=0)


@router.post("/{ticker}/backtest")
def backtest(ticker: str, body: BacktestRequest) -> dict:
    """Replay the heuristic model over historical data."""
    try:
        return _handle(
            run_backtest,
            ticker,
            body.start_date,
            body.end_date,
            body.initial_capital,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
