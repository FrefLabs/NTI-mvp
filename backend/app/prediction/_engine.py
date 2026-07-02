"""Placeholder prediction engine: SMA crossover + RSI heuristic.

This is deliberately **not** a neural network (deliberate MVP adjustment
n°2): a simple, explainable heuristic over basic technical
indicators drives the full prediction flow end-to-end until a real
TensorFlow/Keras model replaces this file.

Signal
------
A composite score in ``[-1, +1]`` combines two components computed on one
year of daily closes from yfinance:

* **Trend** (weight 0.6): relative gap between the 20-day and 50-day simple
  moving averages, ``(SMA20 - SMA50) / SMA50``, divided by 0.04 and clipped
  to ``[-1, +1]`` — a gap of ±4% or more saturates the component.
* **Momentum** (weight 0.4): 14-day RSI mapped linearly around its neutral
  point, ``(50 - RSI) / 20``, clipped to ``[-1, +1]`` — RSI ≤ 30 (oversold)
  saturates to +1 (buy pressure), RSI ≥ 70 (overbought) to -1.

``score = 0.6 * trend + 0.4 * momentum``. The signal is **buy** if
``score > 0.15``, **sell** if ``score < -0.15``, **hold** otherwise.

Confidence formula
------------------
Confidence expresses how far the score sits from the decision boundaries,
as an integer in ``[0, 100]``:

* buy/sell: ``round(|score| * 100)`` — a stronger composite score means a
  more confident directional call.
* hold: ``round((1 - |score| / 0.15) * 100)`` — a score near 0 is a
  confident hold; a score just inside the ±0.15 band is a weak one.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import pandas as pd

from .. import market

SMA_SHORT = 20
SMA_LONG = 50
RSI_PERIOD = 14
TREND_SATURATION = 0.04
TREND_WEIGHT = 0.6
MOMENTUM_WEIGHT = 0.4
SIGNAL_THRESHOLD = 0.15

Signal = Literal["buy", "hold", "sell"]


@dataclass(frozen=True)
class Prediction:
    ticker: str
    signal: Signal
    confidence: int  # 0-100
    score: float
    indicators: dict[str, float]
    as_of: str


def _rsi(closes: pd.Series, period: int = RSI_PERIOD) -> float:
    delta = closes.diff()
    gains = delta.clip(lower=0).rolling(period).mean()
    losses = (-delta.clip(upper=0)).rolling(period).mean()
    last_gain = float(gains.iloc[-1])
    last_loss = float(losses.iloc[-1])
    if last_loss == 0:
        return 100.0
    rs = last_gain / last_loss
    return 100.0 - 100.0 / (1.0 + rs)


def _clip(value: float) -> float:
    return max(-1.0, min(1.0, value))


def predict(ticker: str) -> Prediction:
    """Compute a buy/hold/sell signal with confidence for *ticker*.

    Raises :class:`app.market.UnknownTickerError` for tickers outside the
    allowed set and :class:`app.market.MarketDataError` if historical data
    cannot be fetched.
    """
    history = market.get_history_frame(ticker, period="1y", interval="1d")
    closes = history["Close"]
    if len(closes) < SMA_LONG + 1:
        raise market.MarketDataError(
            f"Not enough history to compute indicators for {ticker}"
        )

    sma_short = float(closes.rolling(SMA_SHORT).mean().iloc[-1])
    sma_long = float(closes.rolling(SMA_LONG).mean().iloc[-1])
    rsi = _rsi(closes)

    trend = _clip((sma_short - sma_long) / sma_long / TREND_SATURATION)
    momentum = _clip((50.0 - rsi) / 20.0)
    score = TREND_WEIGHT * trend + MOMENTUM_WEIGHT * momentum

    if score > SIGNAL_THRESHOLD:
        signal: Signal = "buy"
    elif score < -SIGNAL_THRESHOLD:
        signal = "sell"
    else:
        signal = "hold"

    if signal == "hold":
        confidence = round((1.0 - abs(score) / SIGNAL_THRESHOLD) * 100)
    else:
        confidence = round(abs(score) * 100)

    return Prediction(
        ticker=ticker.upper(),
        signal=signal,
        confidence=max(0, min(100, confidence)),
        score=round(score, 4),
        indicators={
            "sma_short": round(sma_short, 4),
            "sma_long": round(sma_long, 4),
            "rsi": round(rsi, 4),
            "close": round(float(closes.iloc[-1]), 4),
        },
        as_of=datetime.now(timezone.utc).isoformat(),
    )
