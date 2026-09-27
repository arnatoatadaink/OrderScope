"""UWBS-086 repository-backed historical replay packet completeness contract.

A packet is historical evidence only when all required cross-asset lanes are
backed by repository-addressable evidence over one common replay window and the
expected label is independently evidenced. Synthetic regression fixtures are
never accepted by this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from orderscope_local.contracts.errors import ContractViolation


class HistoricalReplayLane(StrEnum):
    OIL_PRICE = "oil_price"
    COMMODITY_FUNDAMENTAL = "commodity_fundamental"
    COMMODITY_EVENT = "commodity_event"
    COMMODITY_INTERPRETATION = "commodity_interpretation"
    BTC_SPOT_ETF_FLOW = "btc_spot_etf_flow"
    TRADITIONAL_RISK = "traditional_risk"
    CRYPTO_MARKET = "crypto_market"
    CRYPTO_DERIVATIVES = "crypto_derivatives"
    VOLATILITY = "volatility"


REQUIRED_HISTORICAL_REPLAY_LANES = frozenset(HistoricalReplayLane)


@dataclass(frozen=True, kw_only=True)
class HistoricalReplayEvidence:
    lane: HistoricalReplayLane
    evidence_ids: tuple[str, ...]
    window_start: str
    window_end: str
    repository_backed: bool = True
    synthetic: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.lane, HistoricalReplayLane):
            raise ContractViolation("lane must be HistoricalReplayLane")
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids:
            raise ContractViolation("historical replay evidence requires at least one evidence id")
        if any(not isinstance(item, str) or not item.strip() or item != item.strip() for item in self.evidence_ids):
            raise ContractViolation("evidence ids must be canonical non-empty text")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ContractViolation("evidence ids must be unique within a lane")
        _validate_window(self.window_start, self.window_end)
        if not isinstance(self.repository_backed, bool) or not isinstance(self.synthetic, bool):
            raise ContractViolation("repository_backed and synthetic must be boolean")
        if not self.repository_backed:
            raise ContractViolation("historical replay evidence must be repository-backed")
        if self.synthetic:
            raise ContractViolation("synthetic evidence cannot satisfy a historical replay packet")


@dataclass(frozen=True, kw_only=True)
class HistoricalReplayPacket:
    packet_id: str
    window_start: str
    window_end: str
    expected_regime: str
    expected_alert: bool
    expected_label_evidence_ids: tuple[str, ...]
    evidence: tuple[HistoricalReplayEvidence, ...]

    def __post_init__(self) -> None:
        for value, field in ((self.packet_id, "packet_id"), (self.expected_regime, "expected_regime")):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        _validate_window(self.window_start, self.window_end)
        if not isinstance(self.expected_alert, bool):
            raise ContractViolation("expected_alert must be boolean")
        if not isinstance(self.expected_label_evidence_ids, tuple) or not self.expected_label_evidence_ids:
            raise ContractViolation("expected label requires independent evidence")
        if any(
            not isinstance(item, str) or not item.strip() or item != item.strip()
            for item in self.expected_label_evidence_ids
        ):
            raise ContractViolation("expected label evidence ids must be canonical non-empty text")
        if len(set(self.expected_label_evidence_ids)) != len(self.expected_label_evidence_ids):
            raise ContractViolation("expected label evidence ids must be unique")
        if not isinstance(self.evidence, tuple) or not self.evidence:
            raise ContractViolation("historical replay packet requires evidence")
        lanes = [item.lane for item in self.evidence]
        if len(set(lanes)) != len(lanes):
            raise ContractViolation("historical replay packet may contain only one evidence group per lane")
        for item in self.evidence:
            if item.window_start != self.window_start or item.window_end != self.window_end:
                raise ContractViolation("all historical replay evidence must share the packet window")
        source_ids = {source_id for item in self.evidence for source_id in item.evidence_ids}
        if source_ids.intersection(self.expected_label_evidence_ids):
            raise ContractViolation("expected label evidence must be independent of classifier input evidence")

    @property
    def missing_lanes(self) -> tuple[HistoricalReplayLane, ...]:
        present = {item.lane for item in self.evidence}
        return tuple(sorted(REQUIRED_HISTORICAL_REPLAY_LANES - present, key=lambda item: item.value))

    @property
    def is_complete(self) -> bool:
        return not self.missing_lanes

    def require_complete(self) -> None:
        if self.missing_lanes:
            names = ", ".join(item.value for item in self.missing_lanes)
            raise ContractViolation(f"historical replay packet is incomplete; missing lanes: {names}")


def _validate_window(start: str, end: str) -> None:
    for value, field in ((start, "window_start"), (end, "window_end")):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ContractViolation(f"{field} must be canonical non-empty text")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ContractViolation(f"{field} must be an ISO-8601 instant") from error
        if parsed.tzinfo is None:
            raise ContractViolation(f"{field} must include a timezone")
    start_at = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_at = datetime.fromisoformat(end.replace("Z", "+00:00"))
    if start_at >= end_at:
        raise ContractViolation("historical replay window must be non-empty")
