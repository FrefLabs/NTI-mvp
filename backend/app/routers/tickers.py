"""HTTP endpoints for ticker market data (RF-04, RF-06, RF-20, RF-22)."""

from fastapi import APIRouter, HTTPException, Query

from .. import market
from ..config import ALLOWED_TICKERS, CHART_RANGES, DEFAULT_CHART_RANGE

router = APIRouter(prefix="/api/tickers", tags=["tickers"])


def _handle(func, *args):
    try:
        return func(*args)
    except market.UnknownTickerError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown ticker '{exc}'. Available tickers: "
            + ", ".join(sorted(ALLOWED_TICKERS)),
        ) from exc
    except market.MarketDataError as exc:
        # RNF-14: upstream failures become a clean JSON error, not a 500.
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("")
def list_tickers() -> list[dict[str, str]]:
    return [
        {"ticker": symbol, "name": name}
        for symbol, name in sorted(ALLOWED_TICKERS.items())
    ]


@router.get("/{ticker}/quote")
def quote(ticker: str) -> dict:
    return _handle(market.get_quote, ticker)


@router.get("/{ticker}/chart")
def chart(
    ticker: str,
    range: str = Query(DEFAULT_CHART_RANGE, alias="range"),
) -> dict:
    if range not in CHART_RANGES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid range '{range}'. Valid ranges: "
            + ", ".join(CHART_RANGES),
        )
    return _handle(market.get_chart, ticker, range)


@router.get("/{ticker}/fundamentals")
def fundamentals(ticker: str) -> dict:
    return _handle(market.get_fundamentals, ticker)
