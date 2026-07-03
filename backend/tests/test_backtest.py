"""Backtest endpoint: replays the heuristic over real historical data."""

import pytest


def test_backtest_returns_consistent_results(client):
    response = client.post(
        "/api/tickers/KO/backtest",
        json={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 10000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "KO"
    assert data["period"] == {"start": "2024-01-01", "end": "2024-12-31"}
    assert data["total_trades"] == len(data["trades"]) > 0
    assert 0.0 <= data["win_rate"] <= 1.0
    assert data["final_capital"] == pytest.approx(
        10000 * (1 + data["total_return"]), rel=1e-3
    )
    for trade in data["trades"]:
        assert trade["signal"] in {"buy", "hold", "sell"}
        assert trade["price"] > 0
        assert "2024-01-01" <= trade["date"] <= "2024-12-31"
        assert isinstance(trade["result"], float | int)


def test_backtest_signal_changes_are_logged_in_order(client):
    response = client.post(
        "/api/tickers/NVDA/backtest",
        json={"start_date": "2024-01-01", "end_date": "2024-12-31"},
    )
    assert response.status_code == 200
    trades = response.json()["trades"]
    signals = [trade["signal"] for trade in trades]
    assert all(a != b for a, b in zip(signals, signals[1:]))
    dates = [trade["date"] for trade in trades]
    assert dates == sorted(dates)


def test_backtest_rejects_inverted_period(client):
    response = client.post(
        "/api/tickers/KO/backtest",
        json={"start_date": "2024-12-31", "end_date": "2024-01-01"},
    )
    assert response.status_code == 422


def test_backtest_unknown_ticker_returns_404(client):
    response = client.post(
        "/api/tickers/ZZZZZZZZZZ/backtest",
        json={"start_date": "2024-01-01", "end_date": "2024-12-31"},
    )
    assert response.status_code == 404
