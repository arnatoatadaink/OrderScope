from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContractViolation,
    DerivedMetric,
    Evidence,
    EvidenceKind,
    EvidenceQuality,
    Fact,
    FactAssertionKind,
    Interpretation,
    InterpretationAssertionKind,
    Provenance,
    ProviderRevision,
    Relationship,
    RelationshipAssertionKind,
    RelationshipDirection,
    RetentionClass,
    SourceReference,
    SourceTimestamp,
    records_available_as_of,
    validate_fact_store,
)


UTC = timezone.utc
T0 = datetime(2026, 8, 4, 20, 16, 24, tzinfo=UTC)


def provenance(accepted_at: datetime, digest: str, *, available_at: datetime | None = None) -> Provenance:
    available = available_at or accepted_at - timedelta(seconds=2)
    return Provenance(
        source_ref=SourceReference(f"https://www.sec.gov/Archives/{digest}.txt"),
        content_hash=ContentHash(digest * 64),
        provider_revision=ProviderRevision(f"revision-{digest}"),
        available_at=available,
        retrieved_at=accepted_at - timedelta(seconds=1),
        accepted_at=accepted_at,
    )


def envelope(record_id: str, accepted_at: datetime = T0) -> dict:
    return {
        "record_id": record_id,
        "schema_version": "fact-store.v1",
        "subject_ref": "instrument:AMD",
        "created_at": accepted_at - timedelta(microseconds=1),
        "accepted_at": accepted_at,
    }


def fixture_records() -> tuple:
    amended_at = T0 + timedelta(hours=1)
    fact = Fact(
        **envelope("fact:filing:original"),
        provenance=provenance(T0, "a"),
        fact_type="filing_submitted.v1",
        value={"form": "10-Q"},
        assertion_kind=FactAssertionKind.OBSERVATION,
        evidence_record_ids=("evidence:filing:original", "evidence:filing:contradiction"),
        period_start=SourceTimestamp.date_only(date(2026, 3, 29)),
        period_end=SourceTimestamp.date_only(date(2026, 6, 27)),
    )
    amendment = Fact(
        **envelope("fact:filing:amendment", amended_at),
        provenance=provenance(amended_at, "b"),
        fact_type="filing_submitted.v1",
        value={"form": "10-Q/A"},
        assertion_kind=FactAssertionKind.AMENDMENT,
        evidence_record_ids=("evidence:filing:amendment",),
        supersedes_record_id=fact.record_id,
    )
    supporting = Evidence(
        **envelope("evidence:filing:original"),
        provenance=provenance(T0, "c"),
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(fact.record_id,),
        locator="sec:0000002488-26-000121",
        quality_class=EvidenceQuality.TIER_1_OFFICIAL,
        retention_class=RetentionClass.DURABLE_METADATA,
    )
    contradicting = Evidence(
        **envelope("evidence:filing:contradiction"),
        provenance=provenance(T0, "d"),
        evidence_kind=EvidenceKind.CONTRADICTING,
        target_record_ids=(fact.record_id,),
        locator="sec:0000002488-26-000122",
        quality_class=EvidenceQuality.TIER_1_OFFICIAL,
        retention_class=RetentionClass.DURABLE_METADATA,
    )
    amendment_evidence = Evidence(
        **envelope("evidence:filing:amendment", amended_at),
        provenance=provenance(amended_at, "e"),
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(amendment.record_id,),
        locator="sec:0000002488-26-000123",
        quality_class=EvidenceQuality.TIER_1_OFFICIAL,
        retention_class=RetentionClass.DURABLE_METADATA,
    )
    relationship = Relationship(
        **envelope("relationship:amd:supplier"),
        provenance=provenance(T0, "f"),
        relationship_type="supplier_of.v1",
        from_ref="company:AMD",
        to_ref="company:CUSTOMER",
        direction=RelationshipDirection.DIRECTED,
        assertion_kind=RelationshipAssertionKind.ASSERTION,
        evidence_record_ids=("evidence:relationship",),
    )
    relationship_evidence = Evidence(
        **envelope("evidence:relationship"),
        provenance=provenance(T0, "1"),
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(relationship.record_id,),
        locator="sec:relationship-span-1",
        quality_class=EvidenceQuality.TIER_1_OFFICIAL,
        retention_class=RetentionClass.TEMPORARY_SUCCESS,
        excerpt_hash=ContentHash("9" * 64),
    )
    metric = DerivedMetric(
        **envelope("metric:filing-count"),
        metric_name="filing_count.v1",
        value=2,
        unit="count",
        calculation_method="count_records",
        method_version="1.0.0",
        input_record_ids=(fact.record_id, amendment.record_id),
        as_of=amended_at,
    )
    interpretation = Interpretation(
        **envelope("interpretation:filing-history", amended_at),
        interpretation_type="filing_history_assessment.v1",
        statement={"status": "amended"},
        basis_record_ids=(fact.record_id, amendment.record_id, metric.record_id),
        method="rule",
        method_version="1.0.0",
        assertion_kind=InterpretationAssertionKind.ASSESSMENT,
    )
    return (
        fact,
        supporting,
        contradicting,
        relationship,
        relationship_evidence,
        amendment,
        amendment_evidence,
        metric,
        interpretation,
    )


def test_distinct_records_preserve_evidence_history_lineage_and_interpretation_basis():
    records = fixture_records()

    validate_fact_store(records)

    assert {record.record_type.value for record in records} == {
        "fact",
        "evidence",
        "relationship",
        "derived_metric",
        "interpretation",
    }
    metric = next(record for record in records if isinstance(record, DerivedMetric))
    interpretation = next(record for record in records if isinstance(record, Interpretation))
    assert len(metric.input_record_ids) == 2
    assert not hasattr(metric, "provenance")
    assert interpretation.basis_record_ids[-1] == metric.record_id


def test_as_of_query_excludes_later_amendment_without_deleting_original_history():
    records = fixture_records()

    early = records_available_as_of(records, T0 + timedelta(minutes=30))
    late = records_available_as_of(records, T0 + timedelta(hours=2))

    assert "fact:filing:original" in {record.record_id for record in early}
    assert "fact:filing:amendment" not in {record.record_id for record in early}
    assert {"fact:filing:original", "fact:filing:amendment"} <= {
        record.record_id for record in late
    }


def test_as_of_visibility_requires_both_source_availability_and_store_acceptance():
    accepted = T0 + timedelta(hours=2)
    staged = Fact(
        **envelope("fact:staged", accepted),
        provenance=provenance(accepted, "7", available_at=T0 + timedelta(hours=1)),
        fact_type="policy_implemented.v1",
        value=True,
        assertion_kind=FactAssertionKind.PENDING_REVIEW,
    )

    assert records_available_as_of((staged,), T0 + timedelta(minutes=30)) == ()
    assert records_available_as_of((staged,), accepted) == (staged,)


def test_registry_relationship_keeps_unknown_validity_and_has_no_fabricated_provenance():
    relationship = Relationship(
        **envelope("relationship:registry"),
        relationship_type="issuer_of.v1",
        from_ref="company:AMD",
        to_ref="instrument:AMD",
        direction=RelationshipDirection.DIRECTED,
        assertion_kind=RelationshipAssertionKind.ASSERTION,
        registry_basis_ref="registry:corporate-canary.v1",
    )

    validate_fact_store((relationship,))
    assert relationship.provenance is None
    assert relationship.valid_from is None
    assert relationship.valid_to is None


def test_cross_record_validation_rejects_broken_lineage_and_mixed_type_supersession():
    records = fixture_records()
    metric = next(record for record in records if isinstance(record, DerivedMetric))
    broken_metric = DerivedMetric(
        **{**envelope("metric:broken"), "supersedes_record_id": records[0].record_id},
        metric_name="broken.v1",
        value=1,
        unit="count",
        calculation_method="count_records",
        method_version="1.0.0",
        input_record_ids=("record:missing",),
        as_of=T0,
    )

    with pytest.raises(ContractViolation, match="same logical record type"):
        validate_fact_store(records + (broken_metric,))
    assert metric.record_type.value == "derived_metric"


def test_records_reject_missing_evidence_incomplete_lineage_and_secret_fields():
    with pytest.raises(ContractViolation, match="requires Evidence"):
        Fact(
            **envelope("fact:no-evidence"),
            provenance=provenance(T0, "8"),
            fact_type="revenue.v1",
            value=1,
            unit="USD",
            assertion_kind=FactAssertionKind.OBSERVATION,
        )
    with pytest.raises(ContractViolation, match="complete record or dataset lineage"):
        DerivedMetric(
            **envelope("metric:no-lineage"),
            metric_name="metric.v1",
            value=1,
            calculation_method="method",
            method_version="1",
            as_of=T0,
        )
    with pytest.raises(ContractViolation, match="secret-like"):
        Interpretation(
            **envelope("interpretation:secret"),
            interpretation_type="assessment.v1",
            statement={"authorization": "fixture-value"},
            basis_record_ids=("fact:any",),
            method="human",
            assertion_kind=InterpretationAssertionKind.ASSESSMENT,
        )


def test_record_values_are_immutable():
    fact = fixture_records()[0]

    with pytest.raises(FrozenInstanceError):
        fact.fact_type = "changed.v1"
    with pytest.raises(TypeError):
        fact.value["form"] = "10-K"


def test_numeric_scalars_require_units():
    with pytest.raises(ContractViolation, match="numeric scalar Fact requires unit"):
        Fact(
            **envelope("fact:unitless-number"),
            provenance=provenance(T0, "6"),
            fact_type="revenue.v1",
            value=42,
            assertion_kind=FactAssertionKind.PENDING_REVIEW,
        )
