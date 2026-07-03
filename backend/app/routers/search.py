"""Ticker search endpoint backed by Yahoo Finance."""

from fastapi import APIRouter, HTTPException, Query

from .. import market

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(q: str = Query(min_length=1, max_length=50)) -> list[dict]:
    """Search Yahoo Finance for tickers matching the query."""
    try:
        return market.search_tickers(q)
    except market.MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
