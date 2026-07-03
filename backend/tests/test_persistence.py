"""Permanent storage: once fetched, market data is served from SQLite and
survives yfinance being unavailable."""

from app import database, market


def test_chart_data_is_stored_permanently(client):
    response = client.get("/api/tickers/KO/chart?range=1mo")
    assert response.status_code == 200

    rows = database.get_market_data("KO", "1d")
    assert len(rows) >= len(response.json()["points"])
    for row in rows:
        assert set(row) == {"timestamp", "open", "high", "low", "close", "volume"}


def test_chart_served_from_database_without_refetching(client, monkeypatch):
    first = client.get("/api/tickers/KO/chart?range=1mo")
    assert first.status_code == 200

    def boom(*args, **kwargs):
        raise ConnectionError("yahoo is down")

    monkeypatch.setattr(market.yf, "Ticker", boom)
    second = client.get("/api/tickers/KO/chart?range=1mo")
    assert second.status_code == 200
    assert second.json() == first.json()


def test_missing_tail_is_fetched_incrementally(client, monkeypatch):
    first = client.get("/api/tickers/KO/chart?range=1mo")
    assert first.status_code == 200

    calls: list[dict] = []
    original_fetch = market._fetch_history

    def spy(symbol, **kwargs):
        calls.append(kwargs)
        return original_fetch(symbol, **kwargs)

    monkeypatch.setattr(market, "_fetch_history", spy)
    with database._connect() as conn:
        conn.execute(
            "DELETE FROM market_data WHERE ticker = 'KO' AND interval = '1d'"
            " AND timestamp > (SELECT timestamp FROM market_data"
            "   WHERE ticker = 'KO' AND interval = '1d'"
            "   ORDER BY timestamp LIMIT 1 OFFSET 9)"
        )
        conn.execute("UPDATE sync_meta SET synced_at = 0 WHERE ticker = 'KO'")

    second = client.get("/api/tickers/KO/chart?range=1mo")
    assert second.status_code == 200
    assert len(calls) == 1
    assert "start" in calls[0]

    fundamentals = client.get("/api/tickers/KO/fundamentals")
    assert fundamentals.status_code == 200
    meta = database.get_ticker_meta("KO")
    assert meta["payload"]["market_cap"] == fundamentals.json()["market_cap"]
