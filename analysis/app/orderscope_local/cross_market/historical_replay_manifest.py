"""Loader for repository-backed UWBS-086 historical replay manifests."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from orderscope_local.contracts.errors import ContractViolation
from .historical_replay_packet import (
    HistoricalReplayEvidence,
    HistoricalReplayLane,
    HistoricalReplayPacket,
)

HISTORICAL_REPLAY_MANIFEST_SCHEMA_VERSION = "uwbs-086-historical-replay-manifest-v0.1"


@dataclass(frozen=True, slots=True)
class HistoricalReplaySource:
    source_id: str
    authority: str
    repository_ref: str
    external_url: str | None
    known_at: str
    role: str


@dataclass(frozen=True, slots=True)
class HistoricalReplayManifest:
    packet: HistoricalReplayPacket
    sources: tuple[HistoricalReplaySource, ...]
    raw_lanes: tuple[tuple[HistoricalReplayLane, dict[str, Any]], ...]


def load_historical_replay_manifest(path: Path) -> HistoricalReplayManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractViolation("historical replay manifest must be readable JSON") from exc
    if not isinstance(raw, dict):
        raise ContractViolation("historical replay manifest root must be an object")
    if raw.get("schema_version") != HISTORICAL_REPLAY_MANIFEST_SCHEMA_VERSION:
        raise ContractViolation("unsupported historical replay manifest schema version")

    sources_raw = raw.get("sources")
    if not isinstance(sources_raw, list) or not sources_raw:
        raise ContractViolation("historical replay manifest sources must be a non-empty list")
    sources: list[HistoricalReplaySource] = []
    for item in sources_raw:
        if not isinstance(item, dict):
            raise ContractViolation("historical replay source entries must be objects")
        source = HistoricalReplaySource(
            source_id=_text(item, "source_id"),
            authority=_text(item, "authority"),
            repository_ref=_text(item, "repository_ref"),
            external_url=_optional_text(item, "external_url"),
            known_at=_text(item, "known_at"),
            role=_text(item, "role"),
        )
        if source.role not in {"classifier_input", "expected_label"}:
            raise ContractViolation("historical replay source role must be classifier_input or expected_label")
        sources.append(source)
    if len({item.source_id for item in sources}) != len(sources):
        raise ContractViolation("historical replay source_id values must be unique")
    source_by_id = {item.source_id: item for item in sources}

    window = raw.get("window")
    if not isinstance(window, dict):
        raise ContractViolation("historical replay manifest window must be an object")
    window_start = _text(window, "start")
    window_end = _text(window, "end")

    lanes_raw = raw.get("lanes")
    if not isinstance(lanes_raw, list) or not lanes_raw:
        raise ContractViolation("historical replay manifest lanes must be a non-empty list")
    evidence: list[HistoricalReplayEvidence] = []
    lane_payloads: list[tuple[HistoricalReplayLane, dict[str, Any]]] = []
    for item in lanes_raw:
        if not isinstance(item, dict):
            raise ContractViolation("historical replay lane entries must be objects")
        try:
            lane = HistoricalReplayLane(_text(item, "lane"))
        except ValueError as exc:
            raise ContractViolation("historical replay lane is unsupported") from exc
        evidence_ids_raw = item.get("evidence_ids")
        if not isinstance(evidence_ids_raw, list) or not evidence_ids_raw:
            raise ContractViolation("historical replay lane evidence_ids must be a non-empty list")
        evidence_ids = tuple(_canonical_text(value, "evidence id") for value in evidence_ids_raw)
        for source_id in evidence_ids:
            source = source_by_id.get(source_id)
            if source is None:
                raise ContractViolation(f"historical replay evidence references unknown source: {source_id}")
            if source.role != "classifier_input":
                raise ContractViolation("classifier lane evidence must use classifier_input sources")
        evidence.append(
            HistoricalReplayEvidence(
                lane=lane,
                evidence_ids=evidence_ids,
                window_start=window_start,
                window_end=window_end,
            )
        )
        lane_payloads.append((lane, item))

    label = raw.get("expected_label")
    if not isinstance(label, dict):
        raise ContractViolation("historical replay expected_label must be an object")
    label_ids_raw = label.get("evidence_ids")
    if not isinstance(label_ids_raw, list) or not label_ids_raw:
        raise ContractViolation("historical replay expected label evidence_ids must be a non-empty list")
    label_ids = tuple(_canonical_text(value, "expected label evidence id") for value in label_ids_raw)
    for source_id in label_ids:
        source = source_by_id.get(source_id)
        if source is None:
            raise ContractViolation(f"expected label references unknown source: {source_id}")
        if source.role != "expected_label":
            raise ContractViolation("expected label evidence must use expected_label sources")

    packet = HistoricalReplayPacket(
        packet_id=_text(raw, "packet_id"),
        window_start=window_start,
        window_end=window_end,
        expected_regime=_text(label, "regime"),
        expected_alert=_bool(label, "alert"),
        expected_label_evidence_ids=label_ids,
        evidence=tuple(evidence),
    )
    packet.require_complete()
    return HistoricalReplayManifest(packet=packet, sources=tuple(sources), raw_lanes=tuple(lane_payloads))


def _text(mapping: dict[str, Any], field: str) -> str:
    return _canonical_text(mapping.get(field), field)


def _optional_text(mapping: dict[str, Any], field: str) -> str | None:
    value = mapping.get(field)
    if value is None:
        return None
    return _canonical_text(value, field)


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ContractViolation(f"{field} must be canonical non-empty text")
    return value


def _bool(mapping: dict[str, Any], field: str) -> bool:
    value = mapping.get(field)
    if not isinstance(value, bool):
        raise ContractViolation(f"{field} must be boolean")
    return value
