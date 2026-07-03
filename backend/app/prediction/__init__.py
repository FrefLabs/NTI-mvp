"""Public interface of the NTI prediction module.

The rest of the backend must import **only** from this package root:

    from app.prediction import predict, Prediction

Everything under :mod:`app.prediction._engine` is an implementation detail.
This boundary exists so the placeholder heuristic can be swapped for a real
TensorFlow/Keras model in a later phase without touching any caller.
"""

from ._engine import Prediction, predict, run_backtest

__all__ = ["Prediction", "predict", "run_backtest"]
