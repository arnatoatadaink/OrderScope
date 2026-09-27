from dataclasses import replace
from pathlib import Path

import pytest

from orderscope_local.contracts.cross_asset_regime import (
    CrossAssetRegimeRating,
    CrossAssetRegimeType,
)
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.historical_replay_manifest import load_historical_replay_manifest
from orderscope_local.cross_market.historical_replay_packet import HistoricalReplayLane
from orderscope_local.cross_market.historical_replay_runner import (
    build_canary_result,
    classify_historical_manifest,
)


MANIFEST = Path("analysis/config/cross_market/uwbs-086-2024-08-05-risk-off-v0.1.json")


def test_august_2024_packet_classifies_as_supported_risk_off() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    result = classify_historical_manifest(manifest)
    assert result.assessment.regime_type is CrossAssetRegimeType.RISK_OFF
    assert result.assessment.rating is CrossAssetRegimeRating.SUPPORT
    assert result.observed_alert is True


def test_august_2024_replay_uses_multiple_independent_support_classes() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    result = classify_historical_manifest(manifest)
    assert set(result.support_classes) == {
        "traditional_risk",
        "crypto_market",
        "crypto_derivatives",
        "btc_spot_etf_flow",
        "macro_commodity",
        "volatility",
    }


def test_august_2024_replay_matches_independent_expected_label() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    classification = classify_historical_manifest(manifest)
    result = build_canary_result(manifest, classification)
    assert result.expected_regime == "risk_off"
    assert result.observed_regime == "risk_off"
    assert result.expected_alert is True
    assert result.observed_alert is True
    assert result.regime_match
    assert result.alert_match


def test_expected_label_does_not_participate_in_classification() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    altered = replace(
        manifest,
        packet=replace(manifest.packet, expected_regime="broad_risk_on", expected_alert=False),
    )
    original = classify_historical_manifest(manifest)
    changed = classify_historical_manifest(altered)
    assert changed.assessment.regime_type is original.assessment.regime_type
    assert changed.assessment.rating is original.assessment.rating
    assert changed.support_classes == original.support_classes


def test_traditional_risk_lane_detects_more_than_two_percent_drawdown() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    result = classify_historical_manifest(manifest)
    assert result.assessment.traditional_risk_metric_refs == ("input-fred-sp500",)


def test_vix_lane_detects_risk_off_spike() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    result = classify_historical_manifest(manifest)
    assert result.assessment.volatility_metric_refs == ("input-fred-vix",)


def test_etf_flow_lane_detects_multi_day_net_outflow() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    result = classify_historical_manifest(manifest)
    assert result.assessment.crypto_flow_metric_refs == ("input-farside-btc-etf-flow",)


def test_derivatives_lane_uses_pre_event_positioning_as_confirmation() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    result = classify_historical_manifest(manifest)
    assert result.assessment.crypto_derivatives_metric_refs == ("input-cftc-btc-futures-2024-07-30",)


def test_runner_rejects_non_numeric_market_observation() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    payload = dict(manifest.raw_lanes)[HistoricalReplayLane.TRADITIONAL_RISK]
    payload["observations"][0]["close"] = "not-a-number"
    with pytest.raises(ContractViolation, match="traditional close must be numeric"):
        classify_historical_manifest(manifest)
