"""Ticker search against real Yahoo Finance results."""

from app import market


def test_search_finds_known_ticker(client):
    response = client.get("/api/search?q=coca-cola")
    assert response.status_code == 200
    results = response.json()
    assert results
    for item in results:
        assert set(item) == {"ticker", "name", "type", "exchange"}
    assert "KO" in [item["ticker"] for item in results]


def test_search_no_matches_returns_empty_list(client):
    response = client.get("/api/search?q=zzqqxxjjkkwwyy")
    assert response.status_code == 200
    assert response.json() == []


def test_search_requires_query(client):
    response = client.get("/api/search")
    assert response.status_code == 422


def test_search_upstream_failure_returns_502(client, monkeypatch):
    def boom(*args, **kwargs):
        raise ConnectionError("yahoo is down")

    monkeypatch.setattr(market.yf, "Search", boom)
    response = client.get("/api/search?q=coca")
    assert response.status_code == 502
