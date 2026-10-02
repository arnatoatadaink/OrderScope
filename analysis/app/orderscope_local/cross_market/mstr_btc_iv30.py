"""UWBS-099 MSTR/BTC 30-day implied-volatility differential contract.

This module compares accepted UWBS-097 BTC IV30 and UWBS-098 MSTR IV30
observations without converting the arithmetic result into a directional,
causal, leverage, NAV-premium, or risk-regime interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.fact_store import DerivedMetric
from orderscope_local.cross_market.btc_iv30 import BtcIv30Observation
from orderscope_local.cross_market.mstr_iv30 import MstrIv30Observation


@dataclass(frozen=True, kw_only=True)
class MstrBtcIv30Differential:
    """Deterministic MSTR IV30 minus BTC IV30 comparison."""

    mstr: MstrIv30Observation
    btc: BtcIv30Observation
    calculated_at: datetime
    accepted_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.mstr, MstrIv30Observation):
            raise ContractViolation("mstr must be an accepted MstrIv30Observation")
        if not isinstance(self.btc, BtcIv30Observation):
            raise ContractViolation("btc must be an accepted BtcIv30Observation")
        _utc(self.calculated_at, "calculated_at")
        _utc(self.accepted_at, "accepted_at")
        if self.calculated_at < self.as_of:
            raise ContractViolation("calculated_at cannot precede the latest input observation")
        if self.accepted_at < self.calculated_at:
            raise ContractViolation("accepted_at cannot precede calculated_at")

    @property
    def as_of(self) -> datetime:
        return max(self.mstr.observed_at, self.btc.observed_at)

    @property
    def differential_percentage_points(self) -> Decimal:
        """Return MSTR annualized IV minus BTC annualized IV in percentage points."""

        return self.mstr.annualized_iv_percent - self.btc.annualized_iv_percent

    @property
    def differential_fraction(self) -> Decimal:
        return self.mstr.normalized_fraction - self.btc.normalized_fraction

    def to_derived_metric(
        self,
        *,
        record_id: str,
        subject_ref: str,
        input_record_ids: tuple[str, str],
    ) -> DerivedMetric:
        _canonical(record_id, "record_id")
        _canonical(subject_ref, "subject_ref")
        if not isinstance(input_record_ids, tuple) or len(input_record_ids) != 2:
            raise ContractViolation("UWBS-099 requires exactly two input record ids")
        for ref in input_record_ids:
            _canonical(ref, "input_record_ids")
        if input_record_ids[0] == input_record_ids[1]:
            raise ContractViolation("UWBS-099 input record ids must be distinct")

        return DerivedMetric(
            record_id=record_id,
            schema_version="mstr-btc-iv30-differential-v0.1",
            subject_ref=subject_ref,
            accepted_at=self.accepted_at,
            created_at=self.calculated_at,
            metric_name="volatility.mstr_btc.iv30_differential",
            value={
                "mstr_annualized_iv_percent": str(self.mstr.annualized_iv_percent),
                "btc_annualized_iv_percent": str(self.btc.annualized_iv_percent),
                "differential_percentage_points": str(self.differential_percentage_points),
                "differential_fraction": str(self.differential_fraction),
                "mstr_observed_at": self.mstr.observed_at.isoformat(),
                "btc_observed_at": self.btc.observed_at.isoformat(),
                "horizon_days": 30,
            },
            calculation_method="mstr_iv30_minus_btc_iv30",
            method_version="v0.1",
            as_of=self.as_of,
            input_record_ids=input_record_ids,
            unit="annualized_volatility_percentage_points",
        )


def _canonical(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 256:
        raise ContractViolation(f"{field} must be canonical non-empty text")


def _utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
