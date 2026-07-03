"""Daily market-close job: refresh stored daily bars for known tickers.

Runs inside the FastAPI lifespan as a plain asyncio task. Every day at
``SCHEDULER_TIME`` (in ``SCHEDULER_TIMEZONE``) it pulls the missing "1d"
bars for every ticker already present in ``market_data``. Tickers with no
stored data are ignored: they are loaded on demand by the API.
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import database, market
from .config import SCHEDULER_TIME, SCHEDULER_TIMEZONE

logger = logging.getLogger(__name__)


def _seconds_until_next_run(now: datetime | None = None) -> float:
    tz = ZoneInfo(SCHEDULER_TIMEZONE)
    hour, minute = (int(part) for part in SCHEDULER_TIME.split(":"))
    now = now or datetime.now(tz)
    target = datetime.combine(now.date(), time(hour, minute), tzinfo=tz)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def refresh_known_tickers() -> None:
    for symbol in database.list_known_tickers():
        try:
            market.refresh_daily_data(symbol)
            logger.info("Refreshed daily data for %s", symbol)
        except Exception:
            logger.exception("Failed to refresh daily data for %s", symbol)


async def run_scheduler() -> None:
    while True:
        await asyncio.sleep(_seconds_until_next_run())
        await asyncio.to_thread(refresh_known_tickers)
