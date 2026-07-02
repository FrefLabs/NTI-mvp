"""Endpoint tests: valid tickers hit real yfinance data; invalid tickers
are rejected; upstream failures produce a clean error response (RNF-14)."""

import pytest

from app import market


def test_list_tickers(client):
    response = client.get("/api/tickers")
    assert response.status_code == 200
    assert [t["ticker"] for t in response.json()] == ["KO", "NVDA"]


@pytest.mark.parametrize("ticker", ["KO", "NVDA"])
def test_quote_valid_ticker(client, ticker):
    response = client.get(f"/api/tickers/{ticker}/quote")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == ticker
    assert data["price"] > 0
    assert data["previous_close"] > 0
    assert isinstance(data["change_percent"], float)


@pytest.mark.parametrize("ticker", ["KO", "NVDA"])
def test_chart_valid_ticker(client, ticker):
    response = client.get(f"/api/tickers/{ticker}/chart?range=1mo")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == ticker
    assert data["range"] == "1mo"
    assert len(data["points"]) > 5
    point = data["points"][0]
    assert set(point) == {"time", "open", "high", "low", "close", "volume"}
    assert point["close"] > 0


def test_fundamentals_valid_ticker(client):
    response = client.get("/api/tickers/KO/fundamentals")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "KO"
    assert data["name"] == "The Coca-Cola Company"
    assert data["market_cap"] and data["market_cap"] > 0


@pytest.mark.parametrize(
    "path",
    [
        "/api/tickers/AAPL/quote",
        "/api/tickers/AAPL/chart",
        "/api/tickers/AAPL/fundamentals",
        "/api/tickers/lowercase-junk/quote",
    ],
)
def test_invalid_ticker_rejected(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert "Available tickers: KO, NVDA" in response.json()["detail"]


def test_invalid_chart_range_rejected(client):
    response = client.get("/api/tickers/KO/chart?range=99y")
    assert response.status_code == 422
    assert "Invalid range" in response.json()["detail"]


def test_yfinance_failure_returns_clean_error(client, monkeypatch):
    """RNF-14: an upstream failure must yield a structured JSON error."""

    def boom(*args, **kwargs):
        raise ConnectionError("yahoo is down")

    monkeypatch.setattr(market.yf, "Ticker", boom)

    for path in (
        "/api/tickers/KO/quote",
        "/api/tickers/KO/chart?range=1mo",
        "/api/tickers/KO/fundamentals",
    ):
        response = client.get(path)
        assert response.status_code == 502
        detail = response.json()["detail"]
        assert "KO" in detail
        assert "Traceback" not in detail
