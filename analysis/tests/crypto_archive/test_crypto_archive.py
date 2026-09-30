from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.crypto_archive import (
    ArchiveDisposition,
    CatchUpState,
    CryptoArchiveError,
    SnapshotArchive,
    detect_missing_windows,
    envelope_from_observation,
    transition_catchup,
)
from orderscope_local.crypto_derivatives import ContractType, CryptoDerivativeObservation, MarginType

UTC = timezone.utc


def _dt(minute: int) -> datetime:
    return datetime(2026, 9, 20, 0, minute, tzinfo=UTC)


def _obs(minute: int = 0, *, oi: float = 100.0, accepted_offset: int = 1, revision: str | None = None) -> CryptoDerivativeObservation:
    return CryptoDerivativeObservation(
        observation_id=f"binance-near-{minute}-{oi}",
        venue="binance",
        instrument_id="NEARUSDT",
        contract_type=ContractType.PERPETUAL,
        margin_type=MarginType.LINEAR,
        quote_asset="USDT",
        observed_at=_dt(minute),
        available_at=_dt(minute) + timedelta(seconds=5),
        accepted_at=_dt(minute) + timedelta(seconds=accepted_offset),
        source_ref="binance:test",
        source_revision=revision,
        open_interest_usd=oi,
    )


def test_envelope_is_deterministic_and_hash_stable() -> None:
    first = envelope_from_observation(_obs())
    second = envelope_from_observation(_obs())
    assert first.snapshot_key == second.snapshot_key
    assert first.payload_sha256 == second.payload_sha256
    assert len(first.payload_sha256) == 64


def test_snapshot_key_is_series_and_observed_time_scoped() -> None:
    first = envelope_from_observation(_obs(0))
    second = envelope_from_observation(_obs(1))
    assert first.snapshot_key != second.snapshot_key
    assert "binance|NEARUSDT|" in first.snapshot_key


def test_archive_insert_then_identical_replay_is_idempotent() -> None:
    archive = SnapshotArchive()
    item = envelope_from_observation(_obs())
    assert archive.put(item) is ArchiveDisposition.INSERTED
    assert archive.put(item) is ArchiveDisposition.DUPLICATE_IDENTICAL
    assert len(archive.all()) == 1


def test_newer_revision_replaces_same_snapshot_key() -> None:
    archive = SnapshotArchive()
    first = envelope_from_observation(_obs(oi=100.0, accepted_offset=10, revision="r1"))
    revised = envelope_from_observation(_obs(oi=105.0, accepted_offset=20, revision="r2"))
    assert archive.put(first) is ArchiveDisposition.INSERTED
    assert archive.put(revised) is ArchiveDisposition.REVISION_REPLACED
    assert archive.get(first.snapshot_key).payload_sha256 == revised.payload_sha256


def test_older_revision_cannot_replace_newer_archive_record() -> None:
    archive = SnapshotArchive()
    newer = envelope_from_observation(_obs(oi=105.0, accepted_offset=20, revision="r2"))
    older = envelope_from_observation(_obs(oi=100.0, accepted_offset=10, revision="r1"))
    archive.put(newer)
    with pytest.raises(CryptoArchiveError):
        archive.put(older)


def test_missing_snapshots_are_coalesced_into_catchup_window() -> None:
    snapshots = [envelope_from_observation(_obs(0)), envelope_from_observation(_obs(3))]
    windows = detect_missing_windows(
        snapshots,
        venue="binance",
        instrument_id="NEARUSDT",
        start_at=_dt(0),
        end_at=_dt(4),
        cadence_seconds=60,
        detected_at=_dt(10),
    )
    assert len(windows) == 1
    assert windows[0].start_at == _dt(1)
    assert windows[0].end_at == _dt(3)
    assert windows[0].state is CatchUpState.PENDING


def test_no_gap_returns_no_catchup_windows() -> None:
    snapshots = [envelope_from_observation(_obs(i)) for i in range(4)]
    assert detect_missing_windows(
        snapshots,
        venue="binance",
        instrument_id="NEARUSDT",
        start_at=_dt(0),
        end_at=_dt(4),
        cadence_seconds=60,
        detected_at=_dt(10),
    ) == ()


def test_catchup_lifecycle_pending_running_complete() -> None:
    window = detect_missing_windows(
        [], venue="binance", instrument_id="NEARUSDT", start_at=_dt(0), end_at=_dt(1), cadence_seconds=60, detected_at=_dt(10)
    )[0]
    running = transition_catchup(window, CatchUpState.RUNNING)
    complete = transition_catchup(running, CatchUpState.COMPLETE)
    assert complete.state is CatchUpState.COMPLETE


def test_terminal_catchup_state_cannot_be_reopened() -> None:
    window = detect_missing_windows(
        [], venue="binance", instrument_id="NEARUSDT", start_at=_dt(0), end_at=_dt(1), cadence_seconds=60, detected_at=_dt(10)
    )[0]
    terminal = transition_catchup(window, CatchUpState.UNRECOVERABLE)
    with pytest.raises(CryptoArchiveError):
        transition_catchup(terminal, CatchUpState.RUNNING)


def test_invalid_cadence_rejected() -> None:
    with pytest.raises(CryptoArchiveError):
        detect_missing_windows(
            [], venue="binance", instrument_id="NEARUSDT", start_at=_dt(0), end_at=_dt(1), cadence_seconds=0, detected_at=_dt(10)
        )
