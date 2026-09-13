"""Segment identity history contract for E0-006.

This module models issuer-reported segment identity over time without equating
segments by label alone.  Rename, merge, split, and recast events remain explicit
history edges grounded in filing/accession evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from orderscope_local.contracts import ContractViolation, Provenance


class SegmentClassificationRole(StrEnum):
    REPORTABLE_SEGMENT = "reportable_segment"
    DISAGGREGATED_BUSINESS = "disaggregated_business"
    MARKET_PLATFORM = "market_platform"


class SegmentHistoryChange(StrEnum):
    INTRODUCED = "introduced"
    RENAMED = "renamed"
    MERGED = "merged"
    SPLIT = "split"
    RECAST = "recast"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class SegmentIdentityVersion:
    segment_id: str
    instrument_id: str
    classification_role: SegmentClassificationRole
    issuer_label: str
    valid_from: date
    valid_to: date | None
    as_reported_at: date
    filing_accession: str
    provenance: Provenance
    recast: bool = False

    def __post_init__(self) -> None:
        if self.instrument_id not in {"AMD", "NVDA"}:
            raise ContractViolation("segment identity is outside the corporate canary")
        if not isinstance(self.classification_role, SegmentClassificationRole):
            raise ContractViolation("segment classification role is invalid")
        for field, value, limit in (
            ("segment_id", self.segment_id, 128),
            ("issuer_label", self.issuer_label, 256),
            ("filing_accession", self.filing_accession, 32),
        ):
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ContractViolation(f"segment identity {field} must be bounded text")
        if not isinstance(self.valid_from, date) or not isinstance(self.as_reported_at, date):
            raise ContractViolation("segment identity dates must be explicit")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ContractViolation("segment identity valid_to cannot precede valid_from")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("segment identity requires Provenance")


@dataclass(frozen=True, slots=True)
class SegmentHistoryEdge:
    change: SegmentHistoryChange
    from_segment_ids: tuple[str, ...]
    to_segment_ids: tuple[str, ...]
    effective_on: date
    as_reported_at: date
    filing_accession: str
    provenance: Provenance
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.change, SegmentHistoryChange):
            raise ContractViolation("segment history change is invalid")
        if not self.from_segment_ids and self.change not in {SegmentHistoryChange.INTRODUCED}:
            raise ContractViolation("segment history change requires predecessor segment ids")
        if not self.to_segment_ids and self.change not in {SegmentHistoryChange.RETIRED}:
            raise ContractViolation("segment history change requires successor segment ids")
        for field, values in (("from_segment_ids", self.from_segment_ids), ("to_segment_ids", self.to_segment_ids)):
            if not isinstance(values, tuple) or len(values) != len(set(values)):
                raise ContractViolation(f"{field} must be a unique tuple")
            if any(not isinstance(value, str) or not value for value in values):
                raise ContractViolation(f"{field} contains invalid ids")
        if not isinstance(self.effective_on, date) or not isinstance(self.as_reported_at, date):
            raise ContractViolation("segment history edge dates must be explicit")
        if not isinstance(self.filing_accession, str) or not self.filing_accession:
            raise ContractViolation("segment history edge requires filing_accession")
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("segment history edge requires Provenance")
        if self.note is not None and (not self.note.strip() or len(self.note) > 512):
            raise ContractViolation("segment history note must be bounded text")


@dataclass(frozen=True, slots=True)
class SegmentIdentityHistory:
    versions: tuple[SegmentIdentityVersion, ...]
    edges: tuple[SegmentHistoryEdge, ...]

    def __post_init__(self) -> None:
        if not self.versions:
            raise ContractViolation("segment identity history requires versions")
        if any(not isinstance(item, SegmentIdentityVersion) for item in self.versions):
            raise ContractViolation("segment identity history has invalid versions")
        if any(not isinstance(item, SegmentHistoryEdge) for item in self.edges):
            raise ContractViolation("segment identity history has invalid edges")

        by_id: dict[str, list[SegmentIdentityVersion]] = {}
        for version in self.versions:
            by_id.setdefault(version.segment_id, []).append(version)
        for segment_id, versions in by_id.items():
            ordered = sorted(versions, key=lambda item: (item.valid_from, item.as_reported_at, item.filing_accession))
            for previous, current in zip(ordered, ordered[1:]):
                if previous.valid_to is None or previous.valid_to >= current.valid_from:
                    raise ContractViolation(f"segment identity versions overlap for {segment_id}")

        known = set(by_id)
        for edge in self.edges:
            refs = set(edge.from_segment_ids) | set(edge.to_segment_ids)
            if not refs.issubset(known):
                raise ContractViolation("segment history edge references unknown segment id")
            if edge.change is SegmentHistoryChange.RENAMED:
                if len(edge.from_segment_ids) != 1 or len(edge.to_segment_ids) != 1:
                    raise ContractViolation("rename must be one-to-one")
            if edge.change is SegmentHistoryChange.MERGED:
                if len(edge.from_segment_ids) < 2 or len(edge.to_segment_ids) != 1:
                    raise ContractViolation("merge must be many-to-one")
            if edge.change is SegmentHistoryChange.SPLIT:
                if len(edge.from_segment_ids) != 1 or len(edge.to_segment_ids) < 2:
                    raise ContractViolation("split must be one-to-many")


def resolve_segment_version(
    history: SegmentIdentityHistory,
    *,
    segment_id: str,
    on_date: date,
    classification_role: SegmentClassificationRole | None = None,
) -> SegmentIdentityVersion:
    """Resolve one established segment identity version for a date.

    Resolution is by stable segment_id and validity interval, never by issuer
    label. An optional role guard prevents cross-axis reuse.
    """

    matches = [
        version
        for version in history.versions
        if version.segment_id == segment_id
        and version.valid_from <= on_date
        and (version.valid_to is None or on_date <= version.valid_to)
        and (classification_role is None or version.classification_role is classification_role)
    ]
    if len(matches) != 1:
        raise ContractViolation("segment identity resolution is missing or ambiguous")
    return matches[0]
