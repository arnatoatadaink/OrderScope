"""BTC-relative crypto context models and deterministic metrics."""

from .interpretation import BtcContextState, build_btc_context_interpretation
from .metrics import btc_adjusted_residual_metric, mean_altcoin_return_metric, same_direction_breadth_metric
from .models import BtcRelativePair, CryptoBreadthObservation, CryptoReturnObservation

__all__ = [
    "BtcContextState",
    "BtcRelativePair",
    "CryptoBreadthObservation",
    "CryptoReturnObservation",
    "btc_adjusted_residual_metric",
    "build_btc_context_interpretation",
    "mean_altcoin_return_metric",
    "same_direction_breadth_metric",
]
