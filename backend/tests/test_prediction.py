"""Verification: the prediction module returns a valid signal and
confidence on real historical data, and the rest of the backend only uses
its public interface."""

import re
from pathlib import Path

import pytest

from app.prediction import Prediction, predict

APP_DIR = Path(__file__).resolve().parent.parent / "app"


@pytest.mark.parametrize("ticker", ["KO", "NVDA"])
def test_predict_returns_valid_signal_and_confidence(ticker):
    result = predict(ticker)
    assert isinstance(result, Prediction)
    assert result.ticker == ticker
    assert result.signal in {"buy", "hold", "sell"}
    assert 0 <= result.confidence <= 100
    assert -1.0 <= result.score <= 1.0
    for key in ("sma_short", "sma_long", "rsi", "close"):
        assert key in result.indicators
    assert 0 <= result.indicators["rsi"] <= 100


def test_predict_rejects_unknown_ticker():
    from app.market import UnknownTickerError

    with pytest.raises(UnknownTickerError):
        predict("AAPL")


def test_prediction_endpoint(client):
    response = client.get("/api/tickers/KO/prediction")
    assert response.status_code == 200
    data = response.json()
    assert data["signal"] in {"buy", "hold", "sell"}
    assert 0 <= data["confidence"] <= 100


def test_no_external_imports_of_prediction_internals():
    """Nothing outside app/prediction/ may import its internals; only the
    package root (public interface) is allowed."""
    internal_import = re.compile(
        r"(from\s+[\w.]*prediction\._|import\s+[\w.]*prediction\._)"
    )
    offenders = [
        str(path)
        for path in APP_DIR.rglob("*.py")
        if "prediction" not in path.parts
        and internal_import.search(path.read_text())
    ]
    assert offenders == []
