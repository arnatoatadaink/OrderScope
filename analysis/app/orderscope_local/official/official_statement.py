"""Source-grounded OfficialStatement semantic Facts for O0-003.

One official document may produce multiple semantic Facts.  Statement, proposal,
formal decision, and implementation are never collapsed into a document-level
classification, and missing source timestamps are never synthesized.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from orderscope_local.contracts import (
    ContractViolation,
    Evidence,
    EvidenceKind,
    EvidenceQuality,
    Fact,
    FactAssertionKind,
    Provenance,
    RetentionClass,
    SourceTimestamp,
    TimestampPrecision,
)

from .feed_adapter import OfficialDiscoveredItem, OfficialItemAvailability
from .registry import get_official_actor, get_official_source


class OfficialPolicyFactKind(StrEnum):
    STATEMENT = "official.statement"
    PROPOSAL = "official.proposal"
    DECISION = "official.decision"
    IMPLEMENTATION = "official.implementation"


@dataclass(frozen=True, slots=True)
class OfficialPolicyObservation:
    fact_id: str
    evidence_record_id: str
    policy_thread_id: str
    actor_id: str
    item: OfficialDiscoveredItem
    fact_kind: OfficialPolicyFactKind
    normalized_assertion: str
    available_at: datetime
    accepted_at: datetime
    decision_at: SourceTimestamp | None = None
    effective_at: SourceTimestamp | None = None
    effective_expression: str | None = None
    event_at: SourceTimestamp | None = None

    def __post_init__(self) -> None:
        for field, value, limit in (
            ("fact_id", self.fact_id, 256),
            ("evidence_record_id", self.evidence_record_id, 256),
            ("policy_thread_id", self.policy_thread_id, 256),
            ("actor_id", self.actor_id, 128),
            ("normalized_assertion", self.normalized_assertion, 512),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > limit:
                raise ContractViolation(f"official policy {field} must be bounded canonical text")
        if not isinstance(self.item, OfficialDiscoveredItem):
            raise ContractViolation("official policy observation requires OfficialDiscoveredItem")
        if self.item.availability is not OfficialItemAvailability.PRESENT:
            raise ContractViolation("official policy Fact requires a present canonical source item")
        if not isinstance(self.fact_kind, OfficialPolicyFactKind):
            raise ContractViolation("official policy fact_kind is invalid")
        get_official_actor(self.actor_id)
        get_official_source(self.item.source_id)
        for field, value in (("decision_at", self.decision_at), ("effective_at", self.effective_at), ("event_at", self.event_at)):
            if value is not None and not isinstance(value, SourceTimestamp):
                raise ContractViolation(f"official policy {field} must use SourceTimestamp")
        if self.effective_expression is not None:
            if not self.effective_expression.strip() or self.effective_expression != self.effective_expression.strip() or len(self.effective_expression) > 512:
                raise ContractViolation("official policy effective_expression must be bounded canonical text")
        for field, value in (("available_at", self.available_at), ("accepted_at", self.accepted_at)):
            if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
                raise ContractViolation(f"official policy {field} must be normalized to UTC")
        if self.available_at > self.item.retrieved_at:
            raise ContractViolation("official policy available_at cannot be later than retrieved_at")
        if self.item.retrieved_at > self.accepted_at:
            raise ContractViolation("official policy retrieved_at cannot be later than accepted_at")
        self._validate_semantic_times()

    def _validate_semantic_times(self) -> None:
        if self.fact_kind in {OfficialPolicyFactKind.STATEMENT, OfficialPolicyFactKind.PROPOSAL}:
            if self.decision_at is not None or self.effective_at is not None or self.effective_expression is not None:
                raise ContractViolation("statement/proposal cannot be promoted with decision/effective semantics")
            return
        if self.fact_kind is OfficialPolicyFactKind.DECISION:
            if self.decision_at is None:
                raise ContractViolation("official decision requires source-grounded decision_at")
            if self.effective_at is not None or self.effective_expression is not None:
                raise ContractViolation("official decision must not carry implementation-effective semantics")
            return
        if self.fact_kind is OfficialPolicyFactKind.IMPLEMENTATION:
            if self.decision_at is not None:
                raise ContractViolation("official implementation must not reuse decision_at")
            if (self.effective_at is None) == (self.effective_expression is None):
                raise ContractViolation("official implementation requires exactly one effective_at or effective_expression")


@dataclass(frozen=True, slots=True)
class OfficialPolicyFactBundle:
    fact: Fact
    evidence: Evidence

    def __post_init__(self) -> None:
        if self.evidence.record_id not in self.fact.evidence_record_ids:
            raise ContractViolation("official policy Evidence must be linked from the Fact")
        if self.fact.record_id not in self.evidence.target_record_ids:
            raise ContractViolation("official policy Evidence must target the Fact")


def build_official_policy_fact(observation: OfficialPolicyObservation) -> OfficialPolicyFactBundle:
    """Build one Fact/Evidence pair without synthesizing source semantics."""

    provenance = Provenance(
        source_ref=__import__("orderscope_local.contracts", fromlist=["SourceReference"]).SourceReference(
            observation.item.canonical_item_url
        ),
        content_hash=observation.item.content_hash,
        retrieved_at=observation.item.retrieved_at,
        available_at=observation.available_at,
        accepted_at=observation.accepted_at,
        event_time=observation.item.event_time,
        published_at=observation.item.published_at,
    )
    value = {
        "policy_thread_id": observation.policy_thread_id,
        "actor_id": observation.actor_id,
        "source_id": observation.item.source_id,
        "canonical_url": observation.item.canonical_item_url,
        "semantic_kind": observation.fact_kind.value,
        "normalized_assertion": observation.normalized_assertion,
    }
    _put_timestamp(value, "decision", observation.decision_at)
    _put_timestamp(value, "effective", observation.effective_at)
    _put_timestamp(value, "event", observation.event_at)
    if observation.effective_expression is not None:
        value["effective_expression"] = observation.effective_expression

    fact = Fact(
        record_id=observation.fact_id,
        schema_version="official-policy-fact-v0.1",
        subject_ref=observation.policy_thread_id,
        accepted_at=observation.accepted_at,
        created_at=observation.accepted_at,
        provenance=provenance,
        fact_type=observation.fact_kind.value,
        value=value,
        assertion_kind=FactAssertionKind.OBSERVATION,
        evidence_record_ids=(observation.evidence_record_id,),
    )
    evidence = Evidence(
        record_id=observation.evidence_record_id,
        schema_version="official-policy-evidence-v0.1",
        subject_ref=observation.policy_thread_id,
        accepted_at=observation.accepted_at,
        created_at=observation.accepted_at,
        provenance=provenance,
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(observation.fact_id,),
        locator=observation.item.canonical_item_url,
        quality_class=EvidenceQuality.TIER_1_OFFICIAL,
        retention_class=RetentionClass.DURABLE_METADATA,
    )
    return OfficialPolicyFactBundle(fact=fact, evidence=evidence)


def build_official_policy_facts(
    observations: tuple[OfficialPolicyObservation, ...],
) -> tuple[OfficialPolicyFactBundle, ...]:
    """Build multiple semantic Facts, including multiple Facts from one document."""

    if not isinstance(observations, tuple) or not observations:
        raise ContractViolation("official policy extraction requires an immutable non-empty observation tuple")
    if len({item.fact_id for item in observations}) != len(observations):
        raise ContractViolation("official policy observations cannot repeat fact_id")
    if len({item.evidence_record_id for item in observations}) != len(observations):
        raise ContractViolation("official policy observations cannot repeat evidence_record_id")
    return tuple(build_official_policy_fact(item) for item in observations)


def _put_timestamp(target: dict[str, object], prefix: str, value: SourceTimestamp | None) -> None:
    if value is None:
        return
    target[f"{prefix}_precision"] = value.precision.value
    if value.precision is TimestampPrecision.DATE_ONLY:
        assert value.calendar_date is not None
        target[f"{prefix}_date"] = value.calendar_date.isoformat()
    else:
        assert value.instant is not None
        target[f"{prefix}_at"] = value.instant.isoformat()
    if value.source_timezone is not None:
        target[f"{prefix}_source_timezone"] = value.source_timezone
