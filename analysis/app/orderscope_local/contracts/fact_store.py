"""Immutable, storage-neutral records for the Fact Store logical boundary.

The contract keeps source assertions, evidence, relationships, deterministic
calculations, and assessments distinct.  It intentionally does not define a
physical database schema, temporary-content lifecycle, or prediction record.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias
import re

from .errors import ContractViolation
from .provider import assert_secret_free
from .provenance import ContentHash, Provenance, SourceTimestamp


_IDENTIFIER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,255}")
Scalar: TypeAlias = str | int | float | bool | None
RecordValue: TypeAlias = Scalar | tuple[Scalar, ...] | Mapping[str, Scalar]


def _identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ContractViolation(f"{field} must be a non-blank bounded identifier")


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _source_interval(
    start: SourceTimestamp | None, end: SourceTimestamp | None, prefix: str
) -> None:
    if start is not None and not isinstance(start, SourceTimestamp):
        raise ContractViolation(f"{prefix}_start must be a SourceTimestamp")
    if end is not None and not isinstance(end, SourceTimestamp):
        raise ContractViolation(f"{prefix}_end must be a SourceTimestamp")
    if start is None or end is None or start.precision is not end.precision:
        return
    start_value = start.calendar_date if start.calendar_date is not None else start.instant
    end_value = end.calendar_date if end.calendar_date is not None else end.instant
    if start_value is not None and end_value is not None and start_value > end_value:
        raise ContractViolation(f"{prefix}_start cannot be later than {prefix}_end")


def _refs(values: tuple[str, ...], field: str, *, required: bool = False) -> None:
    if not isinstance(values, tuple):
        raise ContractViolation(f"{field} must be an immutable tuple")
    if required and not values:
        raise ContractViolation(f"{field} cannot be empty")
    if len(values) != len(set(values)):
        raise ContractViolation(f"{field} cannot contain duplicates")
    for value in values:
        _identifier(value, field)


def _value(value: RecordValue, field: str) -> RecordValue:
    if not isinstance(value, (str, int, float, bool, tuple, Mapping)) and value is not None:
        raise ContractViolation(f"{field} must be a storage-neutral typed value")
    if isinstance(value, tuple) and any(not isinstance(item, (str, int, float, bool)) and item is not None for item in value):
        raise ContractViolation(f"{field} tuple members must be scalar values")
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ContractViolation(f"{field} object keys must be strings")
        if any(not isinstance(item, (str, int, float, bool)) and item is not None for item in value.values()):
            raise ContractViolation(f"{field} object members must be scalar values")
    assert_secret_free(value)
    return MappingProxyType(dict(value)) if isinstance(value, Mapping) else value


class RecordType(StrEnum):
    FACT = "fact"
    EVIDENCE = "evidence"
    RELATIONSHIP = "relationship"
    DERIVED_METRIC = "derived_metric"
    INTERPRETATION = "interpretation"


@dataclass(frozen=True, kw_only=True)
class RecordEnvelope:
    record_id: str
    schema_version: str
    subject_ref: str
    accepted_at: datetime
    created_at: datetime
    supersedes_record_id: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.record_id, "record_id")
        _identifier(self.schema_version, "schema_version")
        _identifier(self.subject_ref, "subject_ref")
        _utc(self.accepted_at, "accepted_at")
        _utc(self.created_at, "created_at")
        if self.created_at > self.accepted_at:
            raise ContractViolation("created_at cannot be later than accepted_at")
        if self.supersedes_record_id is not None:
            _identifier(self.supersedes_record_id, "supersedes_record_id")
            if self.supersedes_record_id == self.record_id:
                raise ContractViolation("a record cannot supersede itself")

    @property
    def record_type(self) -> RecordType:
        raise NotImplementedError


class FactAssertionKind(StrEnum):
    OBSERVATION = "observation"
    CORRECTION = "correction"
    AMENDMENT = "amendment"
    WITHDRAWAL = "withdrawal"
    PENDING_REVIEW = "pending_review"


@dataclass(frozen=True, kw_only=True)
class Fact(RecordEnvelope):
    provenance: Provenance
    fact_type: str
    value: RecordValue
    assertion_kind: FactAssertionKind
    evidence_record_ids: tuple[str, ...] = ()
    unit: str | None = None
    period_start: SourceTimestamp | None = None
    period_end: SourceTimestamp | None = None
    extraction_confidence: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be the accepted I0-002 Provenance type")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("record accepted_at must match provenance accepted_at")
        _identifier(self.fact_type, "fact_type")
        object.__setattr__(self, "value", _value(self.value, "value"))
        if not isinstance(self.assertion_kind, FactAssertionKind):
            raise ContractViolation("assertion_kind must be a FactAssertionKind")
        _refs(self.evidence_record_ids, "evidence_record_ids")
        if self.assertion_kind is not FactAssertionKind.PENDING_REVIEW and not self.evidence_record_ids:
            raise ContractViolation("source-grounded Fact requires Evidence")
        if self.unit is not None:
            _identifier(self.unit, "unit")
        if isinstance(self.value, (int, float)) and not isinstance(self.value, bool) and self.unit is None:
            raise ContractViolation("numeric scalar Fact requires unit")
        _source_interval(self.period_start, self.period_end, "period")
        if self.extraction_confidence is not None and not 0 <= self.extraction_confidence <= 1:
            raise ContractViolation("extraction_confidence must be between zero and one")

    @property
    def record_type(self) -> RecordType:
        return RecordType.FACT


class EvidenceKind(StrEnum):
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    CONTEXT = "context"
    EXTRACTION_SPAN = "extraction_span"


class EvidenceQuality(StrEnum):
    TIER_1_OFFICIAL = "tier_1_official"
    PROVIDER = "provider"
    SECONDARY = "secondary"
    UNCLASSIFIED = "unclassified"


class RetentionClass(StrEnum):
    DURABLE_METADATA = "durable_metadata"
    TEMPORARY_SUCCESS = "temporary_success"
    TEMPORARY_EXCEPTION = "temporary_exception"


@dataclass(frozen=True, kw_only=True)
class Evidence(RecordEnvelope):
    provenance: Provenance
    evidence_kind: EvidenceKind
    target_record_ids: tuple[str, ...]
    locator: str
    quality_class: EvidenceQuality
    retention_class: RetentionClass
    excerpt_hash: ContentHash | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.provenance, Provenance):
            raise ContractViolation("provenance must be the accepted I0-002 Provenance type")
        if self.provenance.accepted_at != self.accepted_at:
            raise ContractViolation("record accepted_at must match provenance accepted_at")
        if not isinstance(self.evidence_kind, EvidenceKind):
            raise ContractViolation("evidence_kind must be an EvidenceKind")
        _refs(self.target_record_ids, "target_record_ids", required=True)
        if not self.locator.strip() or len(self.locator) > 2048:
            raise ContractViolation("locator must be non-blank and bounded")
        assert_secret_free({"locator": self.locator})
        if not isinstance(self.quality_class, EvidenceQuality):
            raise ContractViolation("quality_class must be an EvidenceQuality")
        if not isinstance(self.retention_class, RetentionClass):
            raise ContractViolation("retention_class must be a RetentionClass")
        if self.excerpt_hash is not None and not isinstance(self.excerpt_hash, ContentHash):
            raise ContractViolation("excerpt_hash must be a ContentHash")

    @property
    def record_type(self) -> RecordType:
        return RecordType.EVIDENCE


class RelationshipDirection(StrEnum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


class RelationshipAssertionKind(StrEnum):
    ASSERTION = "assertion"
    CORRECTION = "correction"
    TERMINATION = "termination"
    CONTRADICTION = "contradiction"
    PENDING_REVIEW = "pending_review"


@dataclass(frozen=True, kw_only=True)
class Relationship(RecordEnvelope):
    relationship_type: str
    from_ref: str
    to_ref: str
    direction: RelationshipDirection
    assertion_kind: RelationshipAssertionKind
    provenance: Provenance | None = None
    evidence_record_ids: tuple[str, ...] = ()
    registry_basis_ref: str | None = None
    valid_from: SourceTimestamp | None = None
    valid_to: SourceTimestamp | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _identifier(self.relationship_type, "relationship_type")
        _identifier(self.from_ref, "from_ref")
        _identifier(self.to_ref, "to_ref")
        if not isinstance(self.direction, RelationshipDirection):
            raise ContractViolation("direction must be a RelationshipDirection")
        if not isinstance(self.assertion_kind, RelationshipAssertionKind):
            raise ContractViolation("assertion_kind must be a RelationshipAssertionKind")
        _refs(self.evidence_record_ids, "evidence_record_ids")
        external = self.provenance is not None
        if external:
            if not isinstance(self.provenance, Provenance):
                raise ContractViolation("provenance must be the accepted I0-002 Provenance type")
            if self.provenance.accepted_at != self.accepted_at:
                raise ContractViolation("record accepted_at must match provenance accepted_at")
            if self.registry_basis_ref is not None:
                raise ContractViolation("external relationship cannot use registry basis")
            if self.assertion_kind is not RelationshipAssertionKind.PENDING_REVIEW and not self.evidence_record_ids:
                raise ContractViolation("source-grounded relationship requires Evidence")
        else:
            if self.registry_basis_ref is None:
                raise ContractViolation("registry relationship requires registry_basis_ref")
            _identifier(self.registry_basis_ref, "registry_basis_ref")
            if self.evidence_record_ids:
                raise ContractViolation("registry relationship cannot masquerade as source-grounded")
        _source_interval(self.valid_from, self.valid_to, "valid")

    @property
    def record_type(self) -> RecordType:
        return RecordType.RELATIONSHIP


@dataclass(frozen=True, kw_only=True)
class DerivedMetric(RecordEnvelope):
    metric_name: str
    value: RecordValue
    calculation_method: str
    method_version: str
    as_of: datetime
    input_record_ids: tuple[str, ...] = ()
    input_dataset_refs: tuple[str, ...] = ()
    unit: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _identifier(self.metric_name, "metric_name")
        object.__setattr__(self, "value", _value(self.value, "value"))
        _identifier(self.calculation_method, "calculation_method")
        _identifier(self.method_version, "method_version")
        _utc(self.as_of, "as_of")
        _refs(self.input_record_ids, "input_record_ids")
        _refs(self.input_dataset_refs, "input_dataset_refs")
        if not self.input_record_ids and not self.input_dataset_refs:
            raise ContractViolation("DerivedMetric requires complete record or dataset lineage")
        if self.unit is not None:
            _identifier(self.unit, "unit")
        if isinstance(self.value, (int, float)) and not isinstance(self.value, bool) and self.unit is None:
            raise ContractViolation("numeric scalar DerivedMetric requires unit")

    @property
    def record_type(self) -> RecordType:
        return RecordType.DERIVED_METRIC


class InterpretationAssertionKind(StrEnum):
    ASSESSMENT = "assessment"
    REVISION = "revision"
    REJECTION = "rejection"
    EXPIRATION = "expiration"


@dataclass(frozen=True, kw_only=True)
class Interpretation(RecordEnvelope):
    interpretation_type: str
    statement: RecordValue
    basis_record_ids: tuple[str, ...]
    method: str
    assertion_kind: InterpretationAssertionKind
    method_version: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _identifier(self.interpretation_type, "interpretation_type")
        object.__setattr__(self, "statement", _value(self.statement, "statement"))
        _refs(self.basis_record_ids, "basis_record_ids", required=True)
        _identifier(self.method, "method")
        if self.method_version is not None:
            _identifier(self.method_version, "method_version")
        elif self.method != "human":
            raise ContractViolation("non-human Interpretation requires method_version")
        if not isinstance(self.assertion_kind, InterpretationAssertionKind):
            raise ContractViolation("assertion_kind must be an InterpretationAssertionKind")

    @property
    def record_type(self) -> RecordType:
        return RecordType.INTERPRETATION


FactStoreRecord: TypeAlias = Fact | Evidence | Relationship | DerivedMetric | Interpretation


def validate_fact_store(records: tuple[FactStoreRecord, ...]) -> None:
    """Validate references and append-only history across a logical record set."""

    if not isinstance(records, tuple):
        raise ContractViolation("records must be an immutable tuple")
    by_id: dict[str, FactStoreRecord] = {}
    for record in records:
        if not isinstance(record, (Fact, Evidence, Relationship, DerivedMetric, Interpretation)):
            raise ContractViolation("unsupported Fact Store record type")
        if record.record_id in by_id:
            raise ContractViolation("record_id must be unique")
        by_id[record.record_id] = record
        assert_secret_free({field.name: getattr(record, field.name) for field in fields(record)})

    for record in records:
        if record.supersedes_record_id is not None:
            predecessor = by_id.get(record.supersedes_record_id)
            if predecessor is None:
                raise ContractViolation("supersedes_record_id must resolve")
            if predecessor.record_type is not record.record_type:
                raise ContractViolation("a record may supersede only the same logical record type")
            if predecessor.accepted_at > record.accepted_at:
                raise ContractViolation("supersession cannot run backward in acceptance time")

            visited = {record.record_id}
            cursor = predecessor
            while cursor is not None:
                if cursor.record_id in visited:
                    raise ContractViolation("supersession chain cannot contain a cycle")
                visited.add(cursor.record_id)
                cursor = by_id.get(cursor.supersedes_record_id) if cursor.supersedes_record_id else None

        if isinstance(record, (Fact, Relationship)):
            for evidence_id in record.evidence_record_ids:
                evidence = by_id.get(evidence_id)
                if not isinstance(evidence, Evidence) or record.record_id not in evidence.target_record_ids:
                    raise ContractViolation("Evidence references must be reciprocal")
        if isinstance(record, Evidence):
            for target_id in record.target_record_ids:
                target = by_id.get(target_id)
                if target is None or isinstance(target, Evidence):
                    raise ContractViolation("Evidence target must resolve to a non-Evidence record")
        if isinstance(record, DerivedMetric):
            for input_id in record.input_record_ids:
                if input_id not in by_id:
                    raise ContractViolation("DerivedMetric input_record_ids must resolve")
        if isinstance(record, Interpretation):
            for basis_id in record.basis_record_ids:
                if basis_id not in by_id:
                    raise ContractViolation("Interpretation basis_record_ids must resolve")


def records_available_as_of(
    records: tuple[FactStoreRecord, ...], cutoff: datetime
) -> tuple[FactStoreRecord, ...]:
    """Return immutable history that was accepted and consumable by ``cutoff``."""

    _utc(cutoff, "cutoff")
    validate_fact_store(records)
    visible = []
    for record in records:
        if record.accepted_at > cutoff:
            continue
        provenance = getattr(record, "provenance", None)
        if provenance is not None and provenance.available_at > cutoff:
            continue
        if isinstance(record, DerivedMetric) and record.as_of > cutoff:
            continue
        visible.append(record)
    return tuple(sorted(visible, key=lambda item: (item.accepted_at, item.record_id)))
