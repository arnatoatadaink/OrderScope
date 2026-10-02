"""Conservative interpretation builders for BTC-relative crypto context."""

from __future__ import annotations

from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import Interpretation, InterpretationAssertionKind


class BtcContextState(StrEnum):
    BTC_LED_SYNCHRONIZATION_CANDIDATE = "btc_led_synchronization_candidate"
    ALTCOIN_RELATIVE_STRENGTH = "altcoin_relative_strength"
    ALTCOIN_RELATIVE_WEAKNESS = "altcoin_relative_weakness"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


def build_btc_context_interpretation(
    *,
    record_id: str,
    subject_ref: str,
    accepted_at,
    created_at,
    residual_metric_id: str,
    breadth_metric_id: str,
    residual_return: float,
    same_direction_breadth: float,
    residual_threshold: float = 0.02,
    breadth_threshold: float = 0.6,
) -> Interpretation:
    if not 0 <= same_direction_breadth <= 1:
        raise ContractViolation("same_direction_breadth must be between zero and one")
    if residual_threshold < 0 or not 0 <= breadth_threshold <= 1:
        raise ContractViolation("thresholds are invalid")

    if same_direction_breadth >= breadth_threshold:
        if residual_return >= residual_threshold:
            state = BtcContextState.ALTCOIN_RELATIVE_STRENGTH
        elif residual_return <= -residual_threshold:
            state = BtcContextState.ALTCOIN_RELATIVE_WEAKNESS
        else:
            state = BtcContextState.BTC_LED_SYNCHRONIZATION_CANDIDATE
    else:
        state = BtcContextState.INSUFFICIENT_EVIDENCE

    return Interpretation(
        record_id=record_id,
        schema_version="uwbs-069.v1",
        subject_ref=subject_ref,
        accepted_at=accepted_at,
        created_at=created_at,
        interpretation_type="btc_relative_crypto_context",
        statement={
            "state": state.value,
            "causal_status": "candidate_only",
            "btc_is_configured_proxy": True,
        },
        basis_record_ids=(residual_metric_id, breadth_metric_id),
        method="rules",
        method_version="uwbs-069.v1",
        assertion_kind=InterpretationAssertionKind.ASSESSMENT,
    )
