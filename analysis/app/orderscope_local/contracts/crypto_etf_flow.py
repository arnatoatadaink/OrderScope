"""UWBS-084 source-neutral U.S. spot-Bitcoin ETF flow contract.

Fund-level signed daily net flow is stored as the source-grounded Fact. Market-wide
aggregate flow is intentionally derived from normalized fund-level records so a
provider's precomputed total cannot silently become the canonical source truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite

from .errors import ContractViolation
from .fact_store import DerivedMetric, Fact, FactAssertionKind
from .provenance import Provenance, SourceTimestamp, TimestampPrecision


@dataclass(frozen=True, kw_only=True)
class BtcSpotEtfFlowObservation:
    fund_ref: str
    ticker: str
    flow_date: SourceTimestamp
    net_flow_usd: float
    accepted_at: datetime
    provenance: Provenance

    def __post_init__(self) -> None:
        for value, field in ((self.fund_ref, "fund_ref"), (self.ticker, "ticker")):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if self.fund_ref.lower() in {"aggregate", "total", "all"}:
            raise ContractViolation("BTC spot ETF flow Fact must identify one fund, not an aggregate")
        if not isinstance(self.flow_date, SourceTimestamp) or self.flow_date.precision is not TimestampPrecision.DATE_ONLY:
            raise ContractViolation("flow_date must be a date-only SourceTimestamp")
        if isinstance(self.net_flow_usd, bool) or not isinstance(self.net_flow_usd, (int, float)) or not isfinite(float(self.net_flow_usd)):
            raise ContractViolation("net_flow_usd must be a finite signed numeric value")
        if self.accepted_at.tzinfo is None or self.accepted_at.utcoffset() != timedelta(0):
            raise ContractViolation("accepted_at must be normalized to UTC")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be Provenance")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("accepted_at must match provenance.accepted_at")

    def to_fact(self, *, record_id: str, evidence_record_ids: tuple[str, ...]) -> Fact:
        return Fact(
            record_id=record_id,
            schema_version="btc-spot-etf-flow-observation-v0.1",
            subject_ref=self.fund_ref,
            accepted_at=self.accepted_at,
            created_at=self.accepted_at,
            provenance=self.provenance,
            fact_type="crypto_etf.btc_spot_net_flow",
            value=float(self.net_flow_usd),
            assertion_kind=FactAssertionKind.OBSERVATION,
            evidence_record_ids=evidence_record_ids,
            unit="usd",
            period_start=self.flow_date,
            period_end=self.flow_date,
        )


def aggregate_btc_spot_etf_flow(
    *,
    record_id: str,
    flow_date: SourceTimestamp,
    accepted_at: datetime,
    fund_flow_facts: tuple[Fact, ...],
) -> DerivedMetric:
    if not isinstance(flow_date, SourceTimestamp) or flow_date.precision is not TimestampPrecision.DATE_ONLY:
        raise ContractViolation("aggregate flow_date must be date-only")
    if accepted_at.tzinfo is None or accepted_at.utcoffset() != timedelta(0):
        raise ContractViolation("accepted_at must be normalized to UTC")
    if not fund_flow_facts:
        raise ContractViolation("aggregate BTC spot ETF flow requires fund-level Facts")
    seen_subjects: set[str] = set()
    total = 0.0
    ids: list[str] = []
    for fact in fund_flow_facts:
        if not isinstance(fact, Fact) or fact.fact_type != "crypto_etf.btc_spot_net_flow":
            raise ContractViolation("aggregate input must be BTC spot ETF fund-flow Facts")
        if fact.period_start != flow_date or fact.period_end != flow_date:
            raise ContractViolation("aggregate inputs must share the requested flow_date")
        if fact.subject_ref in seen_subjects:
            raise ContractViolation("aggregate cannot contain duplicate fund subjects")
        if fact.unit != "usd" or isinstance(fact.value, bool) or not isinstance(fact.value, (int, float)):
            raise ContractViolation("aggregate input must carry numeric USD flow")
        seen_subjects.add(fact.subject_ref)
        ids.append(fact.record_id)
        total += float(fact.value)
    return DerivedMetric(
        record_id=record_id,
        schema_version="btc-spot-etf-aggregate-flow-v0.1",
        subject_ref="crypto.btc.spot_etf.aggregate",
        accepted_at=accepted_at,
        created_at=accepted_at,
        metric_name="crypto_etf.btc_spot_aggregate_net_flow",
        value=total,
        calculation_method="sum_fund_level_net_flow",
        method_version="btc-spot-etf-aggregate-v0.1",
        as_of=accepted_at,
        input_record_ids=tuple(ids),
        unit="usd",
    )
