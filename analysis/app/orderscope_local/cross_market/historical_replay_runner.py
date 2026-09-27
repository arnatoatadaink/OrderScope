"""UWBS-086 deterministic historical replay runner.

The runner derives an observed cross-asset regime from repository-backed lane
payloads. Expected labels are consulted only after classification, when building
the Canary result; they never participate in the classification rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from orderscope_local.contracts.cross_asset_canary import CrossAssetCanaryResult
from orderscope_local.contracts.cross_asset_regime import (
    CrossAssetRegimeAssessment,
    CrossAssetRegimeRating,
    CrossAssetRegimeType,
)
from orderscope_local.contracts.errors import ContractViolation
from .historical_replay_manifest import HistoricalReplayManifest
from .historical_replay_packet import HistoricalReplayLane


@dataclass(frozen=True, slots=True)
class HistoricalReplayClassification:
    assessment: CrossAssetRegimeAssessment
    observed_alert: bool
    support_classes: tuple[str, ...]


def classify_historical_manifest(manifest: HistoricalReplayManifest) -> HistoricalReplayClassification:
    """Classify one complete historical packet without reading its expected label."""

    manifest.packet.require_complete()
    lanes = dict(manifest.raw_lanes)

    traditional_refs = _lane_refs(lanes, HistoricalReplayLane.TRADITIONAL_RISK) if _traditional_risk_off(lanes) else ()
    crypto_refs = _lane_refs(lanes, HistoricalReplayLane.CRYPTO_MARKET) if _crypto_risk_off(lanes) else ()
    derivatives_refs = _lane_refs(lanes, HistoricalReplayLane.CRYPTO_DERIVATIVES) if _derivatives_risk_off(lanes) else ()
    flow_refs = _lane_refs(lanes, HistoricalReplayLane.BTC_SPOT_ETF_FLOW) if _etf_flow_risk_off(lanes) else ()
    macro_refs = _lane_refs(lanes, HistoricalReplayLane.COMMODITY_INTERPRETATION) if _commodity_growth_risk(lanes) else ()
    volatility_refs = _lane_refs(lanes, HistoricalReplayLane.VOLATILITY) if _volatility_risk_off(lanes) else ()

    support_classes = tuple(
        name
        for name, refs in (
            ("traditional_risk", traditional_refs),
            ("crypto_market", crypto_refs),
            ("crypto_derivatives", derivatives_refs),
            ("btc_spot_etf_flow", flow_refs),
            ("macro_commodity", macro_refs),
            ("volatility", volatility_refs),
        )
        if refs
    )

    if len(support_classes) >= 3 and (traditional_refs or volatility_refs):
        regime_type = CrossAssetRegimeType.RISK_OFF
        rating = CrossAssetRegimeRating.SUPPORT
    elif len(support_classes) >= 2 and (traditional_refs or volatility_refs):
        regime_type = CrossAssetRegimeType.RISK_OFF
        rating = CrossAssetRegimeRating.PARTIAL
    else:
        regime_type = CrossAssetRegimeType.DIVERGENT
        rating = CrossAssetRegimeRating.PARTIAL
        # The contract requires both traditional and crypto evidence for DIVERGENT.
        traditional_refs = traditional_refs or _lane_refs(lanes, HistoricalReplayLane.TRADITIONAL_RISK)
        crypto_refs = crypto_refs or _lane_refs(lanes, HistoricalReplayLane.CRYPTO_MARKET)

    start = _instant(manifest.packet.window_start)
    end = _instant(manifest.packet.window_end)
    assessment = CrossAssetRegimeAssessment(
        regime_type=regime_type,
        rating=rating,
        subject_ref="cross-asset:historical-replay",
        observed_window_start=start,
        observed_window_end=end,
        traditional_risk_metric_refs=traditional_refs,
        crypto_market_metric_refs=crypto_refs,
        crypto_derivatives_metric_refs=derivatives_refs,
        crypto_flow_metric_refs=flow_refs,
        macro_commodity_interpretation_refs=macro_refs,
        volatility_metric_refs=volatility_refs,
        generated_at=end,
        method_version="historical-replay-runner-v0.1",
    )
    observed_alert = assessment.regime_type is CrossAssetRegimeType.RISK_OFF and assessment.rating in {
        CrossAssetRegimeRating.SUPPORT,
        CrossAssetRegimeRating.PARTIAL,
    }
    return HistoricalReplayClassification(
        assessment=assessment,
        observed_alert=observed_alert,
        support_classes=support_classes,
    )


def build_canary_result(
    manifest: HistoricalReplayManifest,
    classification: HistoricalReplayClassification,
) -> CrossAssetCanaryResult:
    """Compare the independently classified observation with the held-out label."""

    return CrossAssetCanaryResult(
        scenario_id=manifest.packet.packet_id,
        expected_regime=manifest.packet.expected_regime,
        observed_regime=classification.assessment.regime_type.value,
        expected_alert=manifest.packet.expected_alert,
        observed_alert=classification.observed_alert,
    )


def _lane_refs(
    lanes: dict[HistoricalReplayLane, dict[str, Any]],
    lane: HistoricalReplayLane,
) -> tuple[str, ...]:
    payload = lanes.get(lane)
    if payload is None:
        raise ContractViolation(f"historical replay lane missing: {lane.value}")
    refs = payload.get("evidence_ids")
    if not isinstance(refs, list) or not refs:
        raise ContractViolation(f"historical replay lane has no evidence ids: {lane.value}")
    return tuple(_text(item, f"{lane.value} evidence id") for item in refs)


def _observations(
    lanes: dict[HistoricalReplayLane, dict[str, Any]],
    lane: HistoricalReplayLane,
) -> list[dict[str, Any]]:
    payload = lanes.get(lane)
    if payload is None:
        raise ContractViolation(f"historical replay lane missing: {lane.value}")
    values = payload.get("observations")
    if not isinstance(values, list) or not values or any(not isinstance(item, dict) for item in values):
        raise ContractViolation(f"historical replay observations are invalid: {lane.value}")
    return values


def _traditional_risk_off(lanes: dict[HistoricalReplayLane, dict[str, Any]]) -> bool:
    observations = _observations(lanes, HistoricalReplayLane.TRADITIONAL_RISK)
    closes = [_number(item.get("close"), "traditional close") for item in observations]
    return _drawdown(closes) <= -0.02


def _crypto_risk_off(lanes: dict[HistoricalReplayLane, dict[str, Any]]) -> bool:
    observations = _observations(lanes, HistoricalReplayLane.CRYPTO_MARKET)
    changes = [
        _number(item.get("daily_change_percent"), "crypto daily_change_percent")
        for item in observations
        if "daily_change_percent" in item
    ]
    return bool(changes) and min(changes) <= -5.0


def _derivatives_risk_off(lanes: dict[HistoricalReplayLane, dict[str, Any]]) -> bool:
    observations = _observations(lanes, HistoricalReplayLane.CRYPTO_DERIVATIVES)
    for item in observations:
        long_value = _number(item.get("noncommercial_long"), "noncommercial_long")
        short_value = _number(item.get("noncommercial_short"), "noncommercial_short")
        oi_change = _number(item.get("weekly_open_interest_change"), "weekly_open_interest_change")
        if short_value > long_value and oi_change < 0:
            return True
    return False


def _etf_flow_risk_off(lanes: dict[HistoricalReplayLane, dict[str, Any]]) -> bool:
    observations = _observations(lanes, HistoricalReplayLane.BTC_SPOT_ETF_FLOW)
    total = sum(_number(item.get("aggregate_usd_millions"), "aggregate_usd_millions") for item in observations)
    negative_days = sum(
        _number(item.get("aggregate_usd_millions"), "aggregate_usd_millions") < 0
        for item in observations
    )
    return total < 0 and negative_days >= 2


def _commodity_growth_risk(lanes: dict[HistoricalReplayLane, dict[str, Any]]) -> bool:
    observations = _observations(lanes, HistoricalReplayLane.COMMODITY_INTERPRETATION)
    allowed = {
        "oil_down_demand_weakness_candidate",
        "growth_risk_warning_candidate",
    }
    for item in observations:
        interpretation = item.get("interpretation")
        rating = item.get("rating")
        if interpretation in allowed and rating in {"SUPPORT", "PARTIAL"}:
            return True
    return False


def _volatility_risk_off(lanes: dict[HistoricalReplayLane, dict[str, Any]]) -> bool:
    observations = _observations(lanes, HistoricalReplayLane.VOLATILITY)
    closes = [_number(item.get("close"), "volatility close") for item in observations]
    if not closes or closes[0] <= 0:
        return False
    return max(closes) >= 30.0 and (max(closes) / closes[0] - 1.0) >= 0.25


def _drawdown(values: list[float]) -> float:
    if len(values) < 2 or values[0] <= 0:
        raise ContractViolation("historical replay price series requires at least two positive observations")
    return min(values) / values[0] - 1.0


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractViolation(f"{field} must be numeric")
    return float(value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ContractViolation(f"{field} must be canonical non-empty text")
    return value


def _instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ContractViolation("historical replay instant must include timezone")
    return result.astimezone(timezone.utc)
