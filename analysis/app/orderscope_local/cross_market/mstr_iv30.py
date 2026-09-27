"""UWBS-098 MSTR 30-day option-implied-volatility acquisition/normalization contract.

The contract normalizes source observations to annualized 30-day MSTR option IV
while preserving equity-option provenance and keeping MSTR IV distinct from BTC IV.
It does not infer MSTR price direction, BTC direction, leverage, or risk regime from
IV alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import Fact, FactAssertionKind
from orderscope_local.contracts.provenance import Provenance


class MstrIvMethodology(StrEnum):
    ATM_OPTION_SURFACE = "atm_option_surface"
    DELTA_NEUTRAL_COMPOSITE = "delta_neutral_composite"
    PROVIDER_COMPOSITE = "provider_composite"


@dataclass(frozen=True, kw_only=True)
class MstrIv30Observation:
    subject_ref: str
    source_instrument_ref: str
    methodology: MstrIvMethodology
    annualized_iv_percent: Decimal
    horizon_days: int
    observed_at: datetime
    accepted_at: datetime
    provenance: Provenance
    underlying_ref: str = "equity.us.mstr"

    def __post_init__(self) -> None:
        _canonical(self.subject_ref, "subject_ref")
        _canonical(self.source_instrument_ref, "source_instrument_ref")
        _canonical(self.underlying_ref, "underlying_ref")
        if self.underlying_ref != "equity.us.mstr":
            raise ContractViolation("UWBS-098 requires MSTR equity as the underlying")
        if not isinstance(self.methodology, MstrIvMethodology):
            raise ContractViolation("methodology must be MstrIvMethodology")
        if isinstance(self.annualized_iv_percent, bool) or not isinstance(self.annualized_iv_percent, Decimal):
            raise ContractViolation("annualized_iv_percent must be Decimal")
        if not self.annualized_iv_percent.is_finite():
            raise ContractViolation("annualized_iv_percent must be finite")
        if self.annualized_iv_percent < 0:
            raise ContractViolation("annualized_iv_percent cannot be negative")
        if isinstance(self.horizon_days, bool) or not isinstance(self.horizon_days, int):
            raise ContractViolation("horizon_days must be integer")
        if self.horizon_days != 30:
            raise ContractViolation("UWBS-098 normalization requires an explicit 30-day horizon")
        _utc(self.observed_at, "observed_at")
        _utc(self.accepted_at, "accepted_at")
        if self.accepted_at < self.observed_at:
            raise ContractViolation("accepted_at cannot precede observed_at")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")

    @property
    def normalized_fraction(self) -> Decimal:
        return self.annualized_iv_percent / Decimal("100")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        _canonical(record_id, "record_id")
        if not isinstance(evidence_record_ids, tuple) or not evidence_record_ids:
            raise ContractViolation("MSTR IV observation requires evidence lineage")
        for ref in evidence_record_ids:
            _canonical(ref, "evidence_record_ids")
        return Fact(
            record_id=record_id,
            schema_version="mstr-iv30-observation-v0.1",
            subject_ref=self.subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.observed_at,
            provenance=self.provenance,
            fact_type="volatility.equity.mstr.iv30",
            value={
                "source_instrument_ref": self.source_instrument_ref,
                "underlying_ref": self.underlying_ref,
                "methodology": self.methodology.value,
                "horizon_days": self.horizon_days,
                "annualized_iv_percent": str(self.annualized_iv_percent),
                "normalized_fraction": str(self.normalized_fraction),
                "unit": "annualized_volatility_percent",
            },
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
        )


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
