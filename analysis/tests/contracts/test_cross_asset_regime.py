from datetime import datetime, timezone

import pytest

from orderscope_local.contracts.cross_asset_regime import (
    CrossAssetRegimeAssessment,
    CrossAssetRegimeRating,
    CrossAssetRegimeType,
)
from orderscope_local.contracts import ContractViolation


UTC = timezone.utc
START = datetime(2026, 9, 21, 13, 30, tzinfo=UTC)
END = datetime(2026, 9, 21, 20, 0, tzinfo=UTC)
GENERATED = datetime(2026, 9, 21, 20, 5, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 21, 20, 6, tzinfo=UTC)


def assessment(**overrides) -> CrossAssetRegimeAssessment:
    values = dict(
        regime_type=CrossAssetRegimeType.CRYPTO_RISK_ON,
        rating=CrossAssetRegimeRating.SUPPORT,
        subject_ref="market.regime.cross_asset",
        observed_window_start=START,
        observed_window_end=END,
        traditional_risk_metric_refs=(),
        crypto_market_metric_refs=("metric.btc.return",),
        crypto_derivatives_metric_refs=("metric.btc.oi",),
        crypto_flow_metric_refs=("metric.btc.etf.net_flow",),
        macro_commodity_interpretation_refs=(),
        volatility_metric_refs=(),
        contradicting_evidence_refs=(),
        generated_at=GENERATED,
    )
    values.update(overrides)
    return CrossAssetRegimeAssessment(**values)


def test_crypto_risk_on_requires_crypto_plus_flow_or_derivatives_confirmation() -> None:
    item = assessment()
    record = item.to_interpretation(record_id="interp.regime.crypto.1", accepted_at=ACCEPTED)

    assert record.interpretation_type == "crypto_risk_on"
    assert record.statement["rating"] == "SUPPORT"
    assert record.statement["crypto_market_signal_count"] == 1
    assert record.statement["crypto_flow_signal_count"] == 1


def test_single_btc_price_move_cannot_establish_crypto_risk_on() -> None:
    with pytest.raises(ContractViolation, match="at least 3 independent signal classes"):
        assessment(
            crypto_derivatives_metric_refs=(),
            crypto_flow_metric_refs=(),
        )


def test_crypto_risk_on_without_flow_or_derivatives_is_rejected_even_when_other_classes_exist() -> None:
    with pytest.raises(ContractViolation, match="ETF-flow or derivatives confirmation"):
        assessment(
            crypto_derivatives_metric_refs=(),
            crypto_flow_metric_refs=(),
            macro_commodity_interpretation_refs=("interp.oil.disinflation",),
            volatility_metric_refs=("metric.btc.iv",),
        )


def test_broad_risk_on_requires_traditional_risk_asset_evidence() -> None:
    with pytest.raises(ContractViolation, match="traditional risk-asset evidence"):
        assessment(
            regime_type=CrossAssetRegimeType.BROAD_RISK_ON,
        )


def test_broad_risk_on_accepts_cross_asset_confirmation() -> None:
    item = assessment(
        regime_type=CrossAssetRegimeType.BROAD_RISK_ON,
        traditional_risk_metric_refs=("metric.spx.return",),
    )
    assert item.regime_type is CrossAssetRegimeType.BROAD_RISK_ON


def test_partial_regime_requires_two_independent_signal_classes() -> None:
    item = assessment(
        rating=CrossAssetRegimeRating.PARTIAL,
        crypto_derivatives_metric_refs=(),
    )
    assert item.rating is CrossAssetRegimeRating.PARTIAL

    with pytest.raises(ContractViolation, match="at least 2 independent signal classes"):
        assessment(
            rating=CrossAssetRegimeRating.PARTIAL,
            crypto_derivatives_metric_refs=(),
            crypto_flow_metric_refs=(),
        )


def test_unknown_regime_carries_no_directional_evidence() -> None:
    item = assessment(
        rating=CrossAssetRegimeRating.UNKNOWN,
        traditional_risk_metric_refs=(),
        crypto_market_metric_refs=(),
        crypto_derivatives_metric_refs=(),
        crypto_flow_metric_refs=(),
    )
    assert item.basis_record_ids == ()

    with pytest.raises(ContractViolation, match="UNKNOWN regime"):
        assessment(
            rating=CrossAssetRegimeRating.UNKNOWN,
            crypto_derivatives_metric_refs=(),
            crypto_flow_metric_refs=(),
        )


def test_contradict_regime_requires_contradicting_evidence() -> None:
    with pytest.raises(ContractViolation, match="requires contradicting evidence"):
        assessment(
            rating=CrossAssetRegimeRating.CONTRADICT,
            traditional_risk_metric_refs=(),
            crypto_market_metric_refs=(),
            crypto_derivatives_metric_refs=(),
            crypto_flow_metric_refs=(),
        )


def test_signal_classes_cannot_reuse_same_reference() -> None:
    with pytest.raises(ContractViolation, match="cannot reuse record references"):
        assessment(
            crypto_market_metric_refs=("record.same",),
            crypto_derivatives_metric_refs=("record.same",),
        )
