from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import (
    MacroReleaseFamily as ExportedMacroReleaseFamily,
    MacroReleaseObservation as ExportedMacroReleaseObservation,
    MacroReleaseValueRole as ExportedMacroReleaseValueRole,
)
from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.contracts.macro_release import (
    MacroReleaseFamily,
    MacroReleaseObservation,
    MacroReleaseValueRole,
)
from orderscope_local.contracts.provenance import (
    ContentHash,
    Provenance,
    SourceReference,
    SourceTimestamp,
)


UTC = timezone.utc
RELEASED = datetime(2026, 9, 30, 12, 30, tzinfo=UTC)
ACCEPTED = datetime(2026, 9, 30, 12, 31, tzinfo=UTC)


def provenance(source: str = "bea:pce:2026-08") -> Provenance:
    return Provenance(
        source_ref=SourceReference(source),
        content_hash=ContentHash("b" * 64),
        retrieved_at=ACCEPTED,
        available_at=RELEASED,
        accepted_at=ACCEPTED,
        event_time=SourceTimestamp.at(RELEASED),
    )


def observation(**overrides: object) -> MacroReleaseObservation:
    values: dict[str, object] = {
        "release_id": "us.pce.2026-08",
        "family": MacroReleaseFamily.PCE,
        "metric_id": "core_pce_yoy",
        "period_ref": "2026-08",
        "value_role": MacroReleaseValueRole.ACTUAL,
        "value": 2.8,
        "unit": "percent_yoy",
        "released_at": SourceTimestamp.at(RELEASED),
        "accepted_at": ACCEPTED,
        "provenance": provenance(),
    }
    values.update(overrides)
    return MacroReleaseObservation(**values)  # type: ignore[arg-type]


def test_public_contract_exports_match_implementation_types() -> None:
    assert ExportedMacroReleaseFamily is MacroReleaseFamily
    assert ExportedMacroReleaseObservation is MacroReleaseObservation
    assert ExportedMacroReleaseValueRole is MacroReleaseValueRole


def test_actual_release_materializes_as_observation_fact() -> None:
    item = observation()

    fact = item.to_fact(
        record_id="fact.macro.release.us.pce.2026-08.core_pce_yoy.actual",
        evidence_record_ids=("evidence.macro.release.1",),
    )

    assert fact.schema_version == "macro-release-observation-v0.1"
    assert fact.fact_type == "macro_release.pce.actual"
    assert fact.subject_ref == "macro.release.us.pce.2026-08.core_pce_yoy"
    assert fact.value == 2.8
    assert fact.unit == "percent_yoy"
    assert fact.period_start == SourceTimestamp.at(RELEASED)
    assert fact.provenance.source_ref == SourceReference("bea:pce:2026-08")


@pytest.mark.parametrize("family", [MacroReleaseFamily.PCE, MacroReleaseFamily.DURABLE_GOODS])
def test_initial_release_families_are_explicit(family: MacroReleaseFamily) -> None:
    item = observation(family=family)
    assert item.family is family


def test_consensus_and_prior_are_explicit_roles_not_backfilled_fields() -> None:
    consensus = observation(
        value_role=MacroReleaseValueRole.CONSENSUS,
        value=2.7,
        provenance=provenance("consensus:core_pce_yoy:2026-08"),
    )
    prior = observation(
        value_role=MacroReleaseValueRole.PRIOR,
        period_ref="2026-07",
        value=2.6,
    )

    assert consensus.value_role is MacroReleaseValueRole.CONSENSUS
    assert prior.value_role is MacroReleaseValueRole.PRIOR
    assert not hasattr(consensus, "actual")
    assert not hasattr(consensus, "prior")


def test_revised_prior_requires_explicit_revision_target() -> None:
    with pytest.raises(ContractViolation, match="revision_of_period_ref"):
        observation(
            value_role=MacroReleaseValueRole.REVISED_PRIOR,
            period_ref="2026-07",
            value=2.7,
        )

    revised = observation(
        value_role=MacroReleaseValueRole.REVISED_PRIOR,
        period_ref="2026-07",
        revision_of_period_ref="2026-07",
        value=2.7,
    )
    assert revised.revision_of_period_ref == "2026-07"


def test_non_revision_cannot_claim_revision_target() -> None:
    with pytest.raises(ContractViolation, match="only valid for revised_prior"):
        observation(revision_of_period_ref="2026-07")
