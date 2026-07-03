"""News endpoint: real yfinance data, one-hour cache, 404 for unknown
tickers (RF-07 / RF-23)."""

from app import market


def test_news_valid_ticker(client):
    response = client.get("/api/tickers/NVDA/news")
    assert response.status_code == 200
    items = response.json()
    assert items
    for item in items:
        assert set(item) == {
            "title",
            "description",
            "url",
            "publisher",
            "published_at",
        }
        assert item["title"]


def test_news_served_from_cache(client, monkeypatch):
    first = client.get("/api/tickers/KO/news")
    assert first.status_code == 200

    def boom(*args, **kwargs):
        raise ConnectionError("yahoo is down")

    monkeypatch.setattr(market.yf, "Ticker", boom)
    second = client.get("/api/tickers/KO/news")
    assert second.status_code == 200
    assert second.json() == first.json()


def test_news_unknown_ticker_returns_404(client):
    response = client.get("/api/tickers/ZZZZZZZZZZ/news")
    assert response.status_code == 404
