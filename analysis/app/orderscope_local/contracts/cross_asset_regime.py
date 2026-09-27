"""UWBS-085 cross-asset Risk-On / Crypto Risk-On interpretation boundary.

This module classifies candidate regimes from multiple independent signal classes.
It deliberately prevents a single BTC price move, ETF-flow observation, or
commodity interpretation from establishing a broad cross-asset regime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .errors import ContractViolation
from .fact_store import Interpretation, InterpretationAssertionKind


class CrossAssetRegimeType(StrEnum):
    BROAD_RISK_ON = "broad_risk_on"
    CRYPTO_RISK_ON = "crypto_risk_on"
    RISK_OFF = "risk_off"
    DIVERGENT = "divergent"


class CrossAssetRegimeRating(StrEnum):
    SUPPORT = "SUPPORT"
    PARTIAL = "PARTIAL"
    CONTRADICT = "CONTRADICT"
    UNKNOWN = "UNKNOWN"


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _refs(values: tuple[str, ...], field: str) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 255:
            raise ContractViolation(f"{field} must contain bounded canonical references")


@dataclass(frozen=True, kw_only=True)
class CrossAssetRegimeAssessment:
    regime_type: CrossAssetRegimeType
    rating: CrossAssetRegimeRating
    subject_ref: str
    observed_window_start: datetime
    observed_window_end: datetime
    traditional_risk_metric_refs: tuple[str, ...]
    crypto_market_metric_refs: tuple[str, ...]
    crypto_derivatives_metric_refs: tuple[str, ...] = ()
    crypto_flow_metric_refs: tuple[str, ...] = ()
    macro_commodity_interpretation_refs: tuple[str, ...] = ()
    volatility_metric_refs: tuple[str, ...] = ()
    contradicting_evidence_refs: tuple[str, ...] = ()
    generated_at: datetime
    method_version: str = "cross-asset-regime-v0.1"

    def __post_init__(self) -> None:
        if not isinstance(self.regime_type, CrossAssetRegimeType):
            raise ContractViolation("regime_type must be CrossAssetRegimeType")
        if not isinstance(self.rating, CrossAssetRegimeRating):
            raise ContractViolation("rating must be CrossAssetRegimeRating")
        if not isinstance(self.subject_ref, str) or not self.subject_ref.strip() or self.subject_ref != self.subject_ref.strip():
            raise ContractViolation("subject_ref must be canonical non-empty text")
        if not isinstance(self.method_version, str) or not self.method_version.strip():
            raise ContractViolation("method_version cannot be blank")
        _utc(self.observed_window_start, "observed_window_start")
        _utc(self.observed_window_end, "observed_window_end")
        _utc(self.generated_at, "generated_at")
        if self.observed_window_start >= self.observed_window_end:
            raise ContractViolation("observed window must be non-empty and half-open")
        if self.generated_at < self.observed_window_end:
            raise ContractViolation("generated_at cannot precede observed window end")

        groups = (
            (self.traditional_risk_metric_refs, "traditional_risk_metric_refs"),
            (self.crypto_market_metric_refs, "crypto_market_metric_refs"),
            (self.crypto_derivatives_metric_refs, "crypto_derivatives_metric_refs"),
            (self.crypto_flow_metric_refs, "crypto_flow_metric_refs"),
            (self.macro_commodity_interpretation_refs, "macro_commodity_interpretation_refs"),
            (self.volatility_metric_refs, "volatility_metric_refs"),
            (self.contradicting_evidence_refs, "contradicting_evidence_refs"),
        )
        for values, field in groups:
            _refs(values, field)

        sets = [set(values) for values, _ in groups]
        for index, left in enumerate(sets):
            for right in sets[index + 1 :]:
                if left & right:
                    raise ContractViolation("regime signal classes cannot reuse record references")

        supporting = (
            self.traditional_risk_metric_refs,
            self.crypto_market_metric_refs,
            self.crypto_derivatives_metric_refs,
            self.crypto_flow_metric_refs,
            self.macro_commodity_interpretation_refs,
            self.volatility_metric_refs,
        )
        supporting_class_count = sum(bool(values) for values in supporting)

        if self.rating is CrossAssetRegimeRating.UNKNOWN:
            if supporting_class_count or self.contradicting_evidence_refs:
                raise ContractViolation("UNKNOWN regime cannot carry directional evidence")
            return

        if self.rating is CrossAssetRegimeRating.CONTRADICT:
            if not self.contradicting_evidence_refs:
                raise ContractViolation("CONTRADICT regime requires contradicting evidence")
            return

        minimum_classes = 3 if self.rating is CrossAssetRegimeRating.SUPPORT else 2
        if supporting_class_count < minimum_classes:
            raise ContractViolation(f"{self.rating.value} regime requires at least {minimum_classes} independent signal classes")

        if self.regime_type is CrossAssetRegimeType.BROAD_RISK_ON:
            if not self.traditional_risk_metric_refs:
                raise ContractViolation("broad Risk-On requires traditional risk-asset evidence")
            if not (
                self.crypto_market_metric_refs
                or self.macro_commodity_interpretation_refs
                or self.volatility_metric_refs
            ):
                raise ContractViolation("broad Risk-On requires cross-asset confirmation outside traditional risk assets")

        if self.regime_type is CrossAssetRegimeType.CRYPTO_RISK_ON:
            if not self.crypto_market_metric_refs:
                raise ContractViolation("Crypto Risk-On requires crypto market evidence")
            if not (self.crypto_derivatives_metric_refs or self.crypto_flow_metric_refs):
                raise ContractViolation("Crypto Risk-On requires ETF-flow or derivatives confirmation")

        if self.regime_type is CrossAssetRegimeType.RISK_OFF and not (
            self.traditional_risk_metric_refs or self.volatility_metric_refs
        ):
            raise ContractViolation("Risk-Off requires traditional-risk or volatility evidence")

        if self.regime_type is CrossAssetRegimeType.DIVERGENT:
            if not self.traditional_risk_metric_refs or not self.crypto_market_metric_refs:
                raise ContractViolation("divergent regime requires both traditional and crypto evidence")

    @property
    def basis_record_ids(self) -> tuple[str, ...]:
        return (
            self.traditional_risk_metric_refs
            + self.crypto_market_metric_refs
            + self.crypto_derivatives_metric_refs
            + self.crypto_flow_metric_refs
            + self.macro_commodity_interpretation_refs
            + self.volatility_metric_refs
            + self.contradicting_evidence_refs
        )

    def to_interpretation(
        self,
        *,
        record_id: str,
        accepted_at: datetime,
        supersedes_record_id: str | None = None,
    ) -> Interpretation:
        _utc(accepted_at, "accepted_at")
        if accepted_at < self.generated_at:
            raise ContractViolation("accepted_at cannot precede generated_at")
        if not self.basis_record_ids:
            raise ContractViolation("Fact Store Interpretation requires evidence lineage")
        return Interpretation(
            record_id=record_id,
            schema_version="cross-asset-regime-interpretation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=accepted_at,
            created_at=self.generated_at,
            supersedes_record_id=supersedes_record_id,
            interpretation_type=self.regime_type.value,
            statement={
                "rating": self.rating.value,
                "observed_window_start": self.observed_window_start.isoformat(),
                "observed_window_end": self.observed_window_end.isoformat(),
                "traditional_risk_signal_count": len(self.traditional_risk_metric_refs),
                "crypto_market_signal_count": len(self.crypto_market_metric_refs),
                "crypto_derivatives_signal_count": len(self.crypto_derivatives_metric_refs),
                "crypto_flow_signal_count": len(self.crypto_flow_metric_refs),
                "macro_commodity_signal_count": len(self.macro_commodity_interpretation_refs),
                "volatility_signal_count": len(self.volatility_metric_refs),
                "contradicting_count": len(self.contradicting_evidence_refs),
            },
            basis_record_ids=self.basis_record_ids,
            method="cross_asset_regime_rule",
            method_version=self.method_version,
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )
