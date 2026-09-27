import json
from pathlib import Path

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.cross_market.historical_replay_manifest import load_historical_replay_manifest
from orderscope_local.cross_market.historical_replay_packet import (
    HistoricalReplayLane,
    REQUIRED_HISTORICAL_REPLAY_LANES,
)


MANIFEST = Path("analysis/config/cross_market/uwbs-086-2024-08-05-risk-off-v0.1.json")


def test_august_2024_manifest_loads_as_complete_repository_packet() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    assert manifest.packet.is_complete
    assert {item.lane for item in manifest.packet.evidence} == REQUIRED_HISTORICAL_REPLAY_LANES


def test_august_2024_expected_label_is_independently_evidenced_risk_off() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    assert manifest.packet.expected_regime == "risk_off"
    assert manifest.packet.expected_alert is True
    classifier_ids = {item for evidence in manifest.packet.evidence for item in evidence.evidence_ids}
    assert classifier_ids.isdisjoint(manifest.packet.expected_label_evidence_ids)


def test_august_2024_manifest_uses_all_nine_required_lanes_once() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    lanes = [lane for lane, _ in manifest.raw_lanes]
    assert len(lanes) == 9
    assert len(set(lanes)) == 9


def test_btc_derivatives_input_does_not_use_post_event_august_6_cot_snapshot() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    payload = dict(manifest.raw_lanes)[HistoricalReplayLane.CRYPTO_DERIVATIVES]
    observation = payload["observations"][0]
    assert observation["as_of"] == "2024-07-30"
    assert observation["open_interest_contracts"] == 28_605


def test_product_supplied_remains_source_semantics_not_final_demand() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    payload = dict(manifest.raw_lanes)[HistoricalReplayLane.COMMODITY_FUNDAMENTAL]
    assert "Product supplied" in payload["note"]
    assert "not renamed final demand" in payload["note"]


def test_manifest_preserves_countervailing_opec_supply_tightness() -> None:
    manifest = load_historical_replay_manifest(MANIFEST)
    event = dict(manifest.raw_lanes)[HistoricalReplayLane.COMMODITY_EVENT]["observations"][0]
    assert event["event"] == "production_policy_action"
    assert event["state"] == "active"


def test_manifest_rejects_unknown_lane_source(tmp_path: Path) -> None:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw["lanes"][0]["evidence_ids"] = ["not-a-source"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ContractViolation, match="unknown source"):
        load_historical_replay_manifest(path)


def test_manifest_rejects_expected_label_source_as_classifier_input(tmp_path: Path) -> None:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw["lanes"][0]["evidence_ids"] = ["label-bis-bulletin-90"]
    path = tmp_path / "bad-role.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ContractViolation, match="classifier_input"):
        load_historical_replay_manifest(path)


def test_manifest_rejects_classifier_source_as_expected_label(tmp_path: Path) -> None:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw["expected_label"]["evidence_ids"] = ["input-fred-vix"]
    path = tmp_path / "bad-label-role.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ContractViolation, match="expected_label"):
        load_historical_replay_manifest(path)
