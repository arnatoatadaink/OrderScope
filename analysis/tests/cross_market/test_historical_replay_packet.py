import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.historical_replay_packet import (
    HistoricalReplayEvidence,
    HistoricalReplayLane,
    HistoricalReplayPacket,
)


START = "2026-09-01T00:00:00+00:00"
END = "2026-09-08T00:00:00+00:00"


def evidence(lane: HistoricalReplayLane, **overrides) -> HistoricalReplayEvidence:
    values = dict(
        lane=lane,
        evidence_ids=(f"repo:evidence:{lane.value}",),
        window_start=START,
        window_end=END,
    )
    values.update(overrides)
    return HistoricalReplayEvidence(**values)


def complete_evidence() -> tuple[HistoricalReplayEvidence, ...]:
    return tuple(evidence(lane) for lane in HistoricalReplayLane)


def packet(**overrides) -> HistoricalReplayPacket:
    values = dict(
        packet_id="historical-cross-asset-2026-09-01",
        window_start=START,
        window_end=END,
        expected_regime="broad_risk_on",
        expected_alert=True,
        expected_label_evidence_ids=("repo:label:independent-review",),
        evidence=complete_evidence(),
    )
    values.update(overrides)
    return HistoricalReplayPacket(**values)


def test_complete_repository_backed_packet_is_complete() -> None:
    item = packet()
    assert item.is_complete
    assert item.missing_lanes == ()
    item.require_complete()


def test_missing_lane_is_reported_without_synthetic_imputation() -> None:
    items = tuple(item for item in complete_evidence() if item.lane is not HistoricalReplayLane.VOLATILITY)
    item = packet(evidence=items)
    assert not item.is_complete
    assert item.missing_lanes == (HistoricalReplayLane.VOLATILITY,)
    with pytest.raises(ContractViolation, match="volatility"):
        item.require_complete()


def test_synthetic_fixture_cannot_satisfy_historical_packet() -> None:
    with pytest.raises(ContractViolation, match="synthetic"):
        evidence(HistoricalReplayLane.CRYPTO_MARKET, synthetic=True)


def test_non_repository_source_cannot_satisfy_historical_packet() -> None:
    with pytest.raises(ContractViolation, match="repository-backed"):
        evidence(HistoricalReplayLane.OIL_PRICE, repository_backed=False)


def test_all_lanes_must_share_one_replay_window() -> None:
    mismatched = evidence(
        HistoricalReplayLane.VOLATILITY,
        window_start="2026-09-02T00:00:00+00:00",
    )
    items = tuple(
        mismatched if item.lane is HistoricalReplayLane.VOLATILITY else item
        for item in complete_evidence()
    )
    with pytest.raises(ContractViolation, match="share the packet window"):
        packet(evidence=items)


def test_duplicate_lane_is_rejected() -> None:
    with pytest.raises(ContractViolation, match="one evidence group per lane"):
        packet(evidence=complete_evidence() + (evidence(HistoricalReplayLane.OIL_PRICE),))


def test_expected_label_requires_independent_evidence() -> None:
    with pytest.raises(ContractViolation, match="independent"):
        packet(expected_label_evidence_ids=("repo:evidence:oil_price",))


def test_expected_label_evidence_cannot_be_empty() -> None:
    with pytest.raises(ContractViolation, match="independent evidence"):
        packet(expected_label_evidence_ids=())


def test_replay_window_must_be_non_empty() -> None:
    with pytest.raises(ContractViolation, match="non-empty"):
        evidence(HistoricalReplayLane.OIL_PRICE, window_end=START)
