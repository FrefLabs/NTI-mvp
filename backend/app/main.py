"""NTI MVP backend — FastAPI application entry point."""

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import database, scheduler
from .config import CORS_ORIGINS
from .routers import search, tickers


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    task = asyncio.create_task(scheduler.run_scheduler())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(
    title="NTI MVP API",
    description=(
        "Neuronal Trading Intelligence — decision-support API. "
        "NTI never executes trades and does not provide professional "
        "financial advice (ERS §6.1)."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(tickers.router)
app.include_router(search.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
