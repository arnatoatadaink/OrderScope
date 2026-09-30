"""Conservative evaluator for the UWBS-072 NEAR/BTC Canary."""

from __future__ import annotations

from .models import CanaryLayerState, NearBtcCanaryAssessment, NearBtcCanaryInput, NearBtcCanaryState

_LAYER_NAMES = (
    "btc_direction",
    "near_direction",
    "btc_relative_strength",
    "derivatives_positioning",
    "liquidation_context",
    "weekend_liquidity_context",
    "catalyst_context",
)


def evaluate_near_btc_canary(value: NearBtcCanaryInput) -> NearBtcCanaryAssessment:
    states = dict(zip(_LAYER_NAMES, value.layer_states, strict=True))
    supporting = tuple(name for name, state in states.items() if state == CanaryLayerState.SUPPORTING)
    contradicting = tuple(name for name, state in states.items() if state == CanaryLayerState.CONTRADICTING)
    missing = tuple(name for name, state in states.items() if state == CanaryLayerState.MISSING)

    if contradicting:
        state = NearBtcCanaryState.CONFLICTING_EVIDENCE
    elif states["btc_direction"] == CanaryLayerState.SUPPORTING and states["near_direction"] != CanaryLayerState.SUPPORTING:
        state = NearBtcCanaryState.BTC_ONLY_MOVE
    elif states["near_direction"] == CanaryLayerState.SUPPORTING and states["btc_direction"] != CanaryLayerState.SUPPORTING:
        state = NearBtcCanaryState.NEAR_IDIOSYNCRATIC_MOVE
    elif (
        states["liquidation_context"] == CanaryLayerState.SUPPORTING
        and states["derivatives_positioning"] != CanaryLayerState.SUPPORTING
        and states["btc_direction"] != CanaryLayerState.SUPPORTING
    ):
        state = NearBtcCanaryState.LIQUIDATION_ONLY_AMPLIFICATION
    elif (
        states["weekend_liquidity_context"] == CanaryLayerState.SUPPORTING
        and states["btc_direction"] == CanaryLayerState.MISSING
        and states["catalyst_context"] == CanaryLayerState.MISSING
    ):
        state = NearBtcCanaryState.WEEKEND_THIN_LIQUIDITY_CANDIDATE
    elif all(
        states[name] == CanaryLayerState.SUPPORTING
        for name in (
            "btc_direction",
            "near_direction",
            "btc_relative_strength",
            "derivatives_positioning",
        )
    ) and states["liquidation_context"] != CanaryLayerState.CONTRADICTING:
        state = NearBtcCanaryState.MULTI_LAYER_CONFIRMATION_CANDIDATE
    else:
        state = NearBtcCanaryState.INSUFFICIENT_EVIDENCE

    return NearBtcCanaryAssessment(
        state=state,
        observed_at=value.observed_at,
        supporting_layers=supporting,
        contradicting_layers=contradicting,
        missing_layers=missing,
    )
