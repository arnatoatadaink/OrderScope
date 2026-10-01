from datetime import datetime, timezone

import pytest

from orderscope_local.crypto_canary import (
    CanaryLayerState,
    NearBtcCanaryInput,
    NearBtcCanaryState,
    evaluate_near_btc_canary,
)

UTC = timezone.utc
TS = datetime(2026, 9, 21, 0, 0, tzinfo=UTC)
S = CanaryLayerState.SUPPORTING
C = CanaryLayerState.CONTRADICTING
M = CanaryLayerState.MISSING


def _input(**overrides):
    values = dict(
        observed_at=TS,
        btc_direction=S,
        near_direction=S,
        btc_relative_strength=S,
        derivatives_positioning=S,
        liquidation_context=S,
        weekend_liquidity_context=M,
        catalyst_context=S,
    )
    values.update(overrides)
    return NearBtcCanaryInput(**values)


def test_multi_layer_confirmation_requires_core_layers():
    result = evaluate_near_btc_canary(_input())
    assert result.state == NearBtcCanaryState.MULTI_LAYER_CONFIRMATION_CANDIDATE
    assert result.causal_status == "candidate_only"


def test_btc_move_without_near_confirmation_is_false_positive():
    result = evaluate_near_btc_canary(_input(near_direction=M, btc_relative_strength=M))
    assert result.state == NearBtcCanaryState.BTC_ONLY_MOVE


def test_near_move_without_btc_confirmation_is_idiosyncratic_candidate():
    result = evaluate_near_btc_canary(_input(btc_direction=M))
    assert result.state == NearBtcCanaryState.NEAR_IDIOSYNCRATIC_MOVE


def test_liquidation_only_does_not_become_new_directional_positioning():
    result = evaluate_near_btc_canary(
        _input(
            btc_direction=M,
            near_direction=M,
            btc_relative_strength=M,
            derivatives_positioning=M,
            liquidation_context=S,
            catalyst_context=M,
        )
    )
    assert result.state == NearBtcCanaryState.LIQUIDATION_ONLY_AMPLIFICATION


def test_weekend_context_without_btc_or_catalyst_is_not_macro_confirmation():
    result = evaluate_near_btc_canary(
        _input(
            btc_direction=M,
            near_direction=M,
            btc_relative_strength=M,
            derivatives_positioning=M,
            liquidation_context=M,
            weekend_liquidity_context=S,
            catalyst_context=M,
        )
    )
    assert result.state == NearBtcCanaryState.WEEKEND_THIN_LIQUIDITY_CANDIDATE


def test_any_contradiction_forces_conflicting_evidence():
    result = evaluate_near_btc_canary(_input(btc_relative_strength=C))
    assert result.state == NearBtcCanaryState.CONFLICTING_EVIDENCE
    assert "btc_relative_strength" in result.contradicting_layers


def test_missing_core_layers_remain_insufficient():
    result = evaluate_near_btc_canary(
        _input(btc_relative_strength=M, derivatives_positioning=M, liquidation_context=M)
    )
    assert result.state == NearBtcCanaryState.INSUFFICIENT_EVIDENCE


def test_layer_lineage_is_preserved():
    result = evaluate_near_btc_canary(_input(weekend_liquidity_context=S, catalyst_context=M))
    assert "weekend_liquidity_context" in result.supporting_layers
    assert "catalyst_context" in result.missing_layers


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError):
        _input(observed_at=datetime(2026, 9, 21, 0, 0))


def test_assessment_does_not_claim_trader_identity_or_nationality():
    result = evaluate_near_btc_canary(_input())
    assert not hasattr(result, "trader_identity")
    assert not hasattr(result, "participant_nationality")
