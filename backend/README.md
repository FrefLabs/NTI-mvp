# NTI MVP — Backend

FastAPI backend serving real market data (Yahoo Finance via `yfinance`) for
the two MVP tickers: **KO** and **NVDA**. Uses SQLite as a short-TTL response
cache (deliberate MVP adjustment; the ERS specifies MariaDB for later phases).

## Run

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

| Endpoint | Requirement | Description |
| --- | --- | --- |
| `GET /api/health` | — | Liveness check |
| `GET /api/tickers` | — | Available tickers (KO, NVDA) |
| `GET /api/tickers/{ticker}/quote` | RF-06 | Current price, change, day range, volume |
| `GET /api/tickers/{ticker}/chart?range=1d\|5d\|1mo\|6mo\|1y\|5y` | RF-04, RF-22 | Historical OHLCV series for the chart |
| `GET /api/tickers/{ticker}/fundamentals` | RF-20 | Company fundamentals |

Unknown tickers return `404`; upstream Yahoo Finance failures return a clean
`502` JSON error (RNF-14). Responses are cached in SQLite (`backend/nti.db`)
for 5 minutes.

## Tests

```bash
cd backend
source .venv/bin/activate
pytest
```
