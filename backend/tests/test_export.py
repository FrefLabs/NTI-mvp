"""CSV export of stored OHLCV data."""

import csv
import io


def test_chart_export_returns_csv_attachment(client):
    response = client.get("/api/tickers/KO/chart/export?range=1mo")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="KO_1mo.csv"'
    )

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == ["timestamp", "open", "high", "low", "close", "volume"]
    assert len(rows) > 5
    for row in rows[1:]:
        assert len(row) == 6
        assert float(row[4]) > 0


def test_chart_export_invalid_range_rejected(client):
    response = client.get("/api/tickers/KO/chart/export?range=99y")
    assert response.status_code == 422


def test_chart_export_unknown_ticker_returns_404(client):
    response = client.get("/api/tickers/ZZZZZZZZZZ/chart/export?range=1mo")
    assert response.status_code == 404
