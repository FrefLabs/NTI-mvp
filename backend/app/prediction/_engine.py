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
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

import pandas as pd

from .. import market

BACKTEST_WARMUP_DAYS = 120

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


def _evaluate(closes: pd.Series) -> tuple[Signal, int, float, dict[str, float]]:
    """Score a series of daily closes and derive (signal, confidence,
    score, indicators). The series must have at least SMA_LONG + 1 points."""
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

    indicators = {
        "sma_short": round(sma_short, 4),
        "sma_long": round(sma_long, 4),
        "rsi": round(rsi, 4),
        "close": round(float(closes.iloc[-1]), 4),
    }
    return signal, max(0, min(100, confidence)), round(score, 4), indicators


def predict(ticker: str) -> Prediction:
    """Compute a buy/hold/sell signal with confidence for *ticker*.

    Raises :class:`app.market.UnknownTickerError` for tickers that do not
    exist on Yahoo Finance and :class:`app.market.MarketDataError` if
    historical data cannot be fetched.
    """
    history = market.get_history_frame(ticker, period="1y", interval="1d")
    closes = history["Close"]
    if len(closes) < SMA_LONG + 1:
        raise market.MarketDataError(
            f"Not enough history to compute indicators for {ticker}"
        )

    signal, confidence, score, indicators = _evaluate(closes)
    return Prediction(
        ticker=ticker.upper(),
        signal=signal,
        confidence=confidence,
        score=score,
        indicators=indicators,
        as_of=datetime.now(timezone.utc).isoformat(),
    )


def run_backtest(
    ticker: str,
    start_date: date,
    end_date: date,
    initial_capital: float,
) -> dict[str, Any]:
    """Replay the heuristic day by day over [start_date, end_date].

    A trade is logged every time the signal changes; its result is the
    price return between the signal change and the next one (held until
    the signal changes), signed by direction: positive for a buy followed
    by a rise or a sell followed by a fall. Capital follows a long-only
    simulation: invested while the signal is buy, in cash otherwise.
    """
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")

    warmup_start = datetime.combine(
        start_date - timedelta(days=BACKTEST_WARMUP_DAYS),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    end = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
    history = market.get_history_frame(
        ticker, interval="1d", start=warmup_start, end=end
    )
    closes = history["Close"]

    signals: list[tuple[date, str, float]] = []
    for position in range(SMA_LONG + 1, len(closes) + 1):
        day = closes.index[position - 1].date()
        if day < start_date or day > end_date:
            continue
        signal, _, _, _ = _evaluate(closes.iloc[:position])
        signals.append((day, signal, float(closes.iloc[position - 1])))

    if not signals:
        raise market.MarketDataError(
            f"Not enough history to backtest {ticker} in the requested period"
        )

    trades: list[dict[str, Any]] = []
    capital = initial_capital
    current: tuple[date, str, float] | None = None
    for day, signal, price in signals:
        if current is not None and signal == current[1]:
            continue
        if current is not None:
            capital = _close_trade(trades, current, price, capital)
        current = (day, signal, price)
    if current is not None:
        capital = _close_trade(trades, current, signals[-1][2], capital)

    directional = [t for t in trades if t["signal"] in ("buy", "sell")]
    wins = sum(1 for t in directional if t["result"] > 0)
    return {
        "ticker": ticker.upper(),
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "total_trades": len(trades),
        "win_rate": round(wins / len(directional), 4) if directional else 0.0,
        "total_return": round(capital / initial_capital - 1, 4),
        "final_capital": round(capital, 2),
        "trades": trades,
    }


def _close_trade(
    trades: list[dict[str, Any]],
    entry: tuple[date, str, float],
    exit_price: float,
    capital: float,
) -> float:
    day, signal, price = entry
    price_return = exit_price / price - 1
    if signal == "buy":
        result = price_return
        capital *= 1 + price_return
    elif signal == "sell":
        result = -price_return
    else:
        result = 0.0
    trades.append(
        {
            "date": day.isoformat(),
            "signal": signal,
            "price": round(price, 4),
            "result": round(result, 4),
        }
    )
    return capital
