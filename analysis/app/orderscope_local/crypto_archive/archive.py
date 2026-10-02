"""Deterministic in-memory reference implementation for UWBS-074 lifecycle semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime
from typing import Iterable

from orderscope_local.crypto_derivatives import CryptoDerivativeObservation

from .models import ArchiveDisposition, CatchUpState, CatchUpWindow, CryptoArchiveError, SnapshotEnvelope


def snapshot_key(observation: CryptoDerivativeObservation) -> str:
    return f"{observation.venue}|{observation.instrument_id}|{observation.observed_at.isoformat()}"


def envelope_from_observation(observation: CryptoDerivativeObservation) -> SnapshotEnvelope:
    payload = {
        "observation_id": observation.observation_id,
        "venue": observation.venue,
        "instrument_id": observation.instrument_id,
        "contract_type": observation.contract_type.value,
        "margin_type": observation.margin_type.value,
        "quote_asset": observation.quote_asset,
        "observed_at": observation.observed_at.isoformat(),
        "available_at": observation.available_at.isoformat(),
        "accepted_at": observation.accepted_at.isoformat(),
        "source_ref": observation.source_ref,
        "source_revision": observation.source_revision,
        "open_interest_contracts": observation.open_interest_contracts,
        "open_interest_base": observation.open_interest_base,
        "open_interest_usd": observation.open_interest_usd,
        "funding_rate": observation.funding_rate,
        "funding_interval_seconds": observation.funding_interval_seconds,
        "mark_price": observation.mark_price,
        "index_price": observation.index_price,
        "basis": observation.basis,
        "derivatives_volume_usd": observation.derivatives_volume_usd,
    }
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    return SnapshotEnvelope(
        snapshot_key=snapshot_key(observation),
        venue=observation.venue,
        instrument_id=observation.instrument_id,
        observed_at=observation.observed_at,
        accepted_at=observation.accepted_at,
        source_revision=observation.source_revision,
        payload_sha256=digest,
        payload_json=payload_json,
    )


class SnapshotArchive:
    """Reference archive with deterministic duplicate/revision behavior."""

    def __init__(self) -> None:
        self._records: dict[str, SnapshotEnvelope] = {}

    def put(self, envelope: SnapshotEnvelope) -> ArchiveDisposition:
        prior = self._records.get(envelope.snapshot_key)
        if prior is None:
            self._records[envelope.snapshot_key] = envelope
            return ArchiveDisposition.INSERTED
        if prior.payload_sha256 == envelope.payload_sha256:
            return ArchiveDisposition.DUPLICATE_IDENTICAL
        if envelope.accepted_at < prior.accepted_at:
            raise CryptoArchiveError("older accepted revision cannot replace newer archive record")
        self._records[envelope.snapshot_key] = envelope
        return ArchiveDisposition.REVISION_REPLACED

    def get(self, key: str) -> SnapshotEnvelope | None:
        return self._records.get(key)

    def all(self) -> tuple[SnapshotEnvelope, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: (item.venue, item.instrument_id, item.observed_at)))


def detect_missing_windows(
    snapshots: Iterable[SnapshotEnvelope],
    *,
    venue: str,
    instrument_id: str,
    start_at: datetime,
    end_at: datetime,
    cadence_seconds: int,
    detected_at: datetime,
) -> tuple[CatchUpWindow, ...]:
    if cadence_seconds <= 0:
        raise CryptoArchiveError("cadence_seconds must be positive")
    if start_at >= end_at:
        raise CryptoArchiveError("start_at must be earlier than end_at")
    known = {item.observed_at for item in snapshots if item.venue == venue and item.instrument_id == instrument_id}
    from datetime import timedelta
    step = timedelta(seconds=cadence_seconds)
    missing: list[datetime] = []
    cursor = start_at
    while cursor < end_at:
        if cursor not in known:
            missing.append(cursor)
        cursor += step
    if not missing:
        return ()
    windows: list[CatchUpWindow] = []
    run_start = missing[0]
    previous = missing[0]
    for point in missing[1:]:
        if point != previous + step:
            windows.append(_window(venue, instrument_id, run_start, previous + step, detected_at))
            run_start = point
        previous = point
    windows.append(_window(venue, instrument_id, run_start, previous + step, detected_at))
    return tuple(windows)


def _window(venue: str, instrument_id: str, start_at: datetime, end_at: datetime, detected_at: datetime) -> CatchUpWindow:
    ident = hashlib.sha256(f"{venue}|{instrument_id}|{start_at.isoformat()}|{end_at.isoformat()}".encode()).hexdigest()[:24]
    return CatchUpWindow(catchup_id=ident, venue=venue, instrument_id=instrument_id, start_at=start_at, end_at=end_at, detected_at=detected_at)


def transition_catchup(window: CatchUpWindow, new_state: CatchUpState) -> CatchUpWindow:
    allowed = {
        CatchUpState.PENDING: {CatchUpState.RUNNING, CatchUpState.UNRECOVERABLE},
        CatchUpState.RUNNING: {CatchUpState.COMPLETE, CatchUpState.UNRECOVERABLE},
        CatchUpState.COMPLETE: set(),
        CatchUpState.UNRECOVERABLE: set(),
    }
    if new_state not in allowed[window.state]:
        raise CryptoArchiveError(f"invalid catch-up transition: {window.state} -> {new_state}")
    return replace(window, state=new_state)
