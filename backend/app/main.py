"""NTI MVP backend — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import tickers

app = FastAPI(
    title="NTI MVP API",
    description=(
        "Neuronal Trading Intelligence — decision-support API. "
        "NTI never executes trades and does not provide professional "
        "financial advice (ERS §6.1)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(tickers.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
