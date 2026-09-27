from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, SourceTimestamp
from orderscope_local.official import (
    OfficialDiscoveredItem,
    OfficialPolicyFactKind,
    OfficialPolicyObservation,
    build_official_policy_fact,
    build_official_policy_facts,
)


RETRIEVED = datetime(2026, 1, 15, 6, 0, tzinfo=timezone.utc)
AVAILABLE = datetime(2026, 1, 15, 5, 59, tzinfo=timezone.utc)
ACCEPTED = datetime(2026, 1, 15, 6, 1, tzinfo=timezone.utc)


def _item(
    *,
    source_id: str = "official-white-house-presidential-actions",
    url: str = "https://www.whitehouse.gov/presidential-actions/2026/01/example-action/",
    published_at: SourceTimestamp | None = None,
) -> OfficialDiscoveredItem:
    return OfficialDiscoveredItem(
        source_id=source_id,
        canonical_item_url=url,
        content_hash=ContentHash("a" * 64),
        retrieved_at=RETRIEVED,
        published_at=published_at,
    )


def _observation(
    *,
    fact_id: str,
    evidence_id: str,
    kind: OfficialPolicyFactKind,
    assertion: str,
    item: OfficialDiscoveredItem | None = None,
    actor_id: str = "actor-person-us-president-2026",
    decision_at: SourceTimestamp | None = None,
    effective_at: SourceTimestamp | None = None,
    effective_expression: str | None = None,
    event_at: SourceTimestamp | None = None,
) -> OfficialPolicyObservation:
    return OfficialPolicyObservation(
        fact_id=fact_id,
        evidence_record_id=evidence_id,
        policy_thread_id="policy.us.semiconductor-232.2026",
        actor_id=actor_id,
        item=item or _item(),
        fact_kind=kind,
        normalized_assertion=assertion,
        available_at=AVAILABLE,
        accepted_at=ACCEPTED,
        decision_at=decision_at,
        effective_at=effective_at,
        effective_expression=effective_expression,
        event_at=event_at,
    )


def test_statement_and_proposal_cannot_be_promoted_to_effective() -> None:
    effective = SourceTimestamp.date_only(date(2026, 1, 15))
    for kind in (OfficialPolicyFactKind.STATEMENT, OfficialPolicyFactKind.PROPOSAL):
        with pytest.raises(ContractViolation):
            _observation(
                fact_id=f"fact.{kind.name.lower()}",
                evidence_id=f"evidence.{kind.name.lower()}",
                kind=kind,
                assertion="future policy intent",
                effective_at=effective,
            )


def test_decision_requires_decision_timestamp_and_keeps_effective_separate() -> None:
    with pytest.raises(ContractViolation):
        _observation(
            fact_id="fact.decision.missing-time",
            evidence_id="evidence.decision.missing-time",
            kind=OfficialPolicyFactKind.DECISION,
            assertion="signed formal action",
        )

    decision = SourceTimestamp.date_only(date(2026, 1, 14))
    effective = SourceTimestamp.date_only(date(2026, 1, 15))
    with pytest.raises(ContractViolation):
        _observation(
            fact_id="fact.decision.mixed",
            evidence_id="evidence.decision.mixed",
            kind=OfficialPolicyFactKind.DECISION,
            assertion="signed formal action",
            decision_at=decision,
            effective_at=effective,
        )


def test_implementation_requires_explicit_effective_semantics() -> None:
    with pytest.raises(ContractViolation):
        _observation(
            fact_id="fact.impl.missing-effective",
            evidence_id="evidence.impl.missing-effective",
            kind=OfficialPolicyFactKind.IMPLEMENTATION,
            assertion="tariff becomes operative",
        )

    relative = _observation(
        fact_id="fact.impl.relative",
        evidence_id="evidence.impl.relative",
        kind=OfficialPolicyFactKind.IMPLEMENTATION,
        assertion="rule becomes effective after publication",
        effective_expression="90 days after publication in the Federal Register",
    )
    bundle = build_official_policy_fact(relative)
    assert dict(bundle.fact.value)["effective_expression"] == "90 days after publication in the Federal Register"
    assert "effective_date" not in dict(bundle.fact.value)


def test_date_only_decision_precision_is_not_promoted_to_midnight() -> None:
    observation = _observation(
        fact_id="fact.decision.date-only",
        evidence_id="evidence.decision.date-only",
        kind=OfficialPolicyFactKind.DECISION,
        assertion="final rule issued",
        decision_at=SourceTimestamp.date_only(date(2024, 10, 28)),
    )
    value = dict(build_official_policy_fact(observation).fact.value)
    assert value["decision_precision"] == "date_only"
    assert value["decision_date"] == "2024-10-28"
    assert "decision_at" not in value


def test_one_white_house_document_can_generate_decision_implementation_and_statement() -> None:
    item = _item(published_at=SourceTimestamp.date_only(date(2026, 1, 14)))
    decision = _observation(
        fact_id="fact.wh.semi.decision",
        evidence_id="evidence.wh.semi.decision",
        kind=OfficialPolicyFactKind.DECISION,
        assertion="covered products receive a 25 percent tariff",
        item=item,
        decision_at=SourceTimestamp.date_only(date(2026, 1, 14)),
    )
    implementation = _observation(
        fact_id="fact.wh.semi.implementation",
        evidence_id="evidence.wh.semi.implementation",
        kind=OfficialPolicyFactKind.IMPLEMENTATION,
        assertion="covered-product tariff becomes effective",
        item=item,
        effective_at=SourceTimestamp.at(
            datetime(2026, 1, 15, 5, 1, tzinfo=timezone.utc),
            source_timezone="EST",
        ),
    )
    statement = _observation(
        fact_id="fact.wh.semi.statement",
        evidence_id="evidence.wh.semi.statement",
        kind=OfficialPolicyFactKind.STATEMENT,
        assertion="broader semiconductor tariffs may be considered later",
        item=item,
    )

    bundles = build_official_policy_facts((decision, implementation, statement))
    assert [bundle.fact.fact_type for bundle in bundles] == [
        "official.decision",
        "official.implementation",
        "official.statement",
    ]
    assert len({bundle.fact.record_id for bundle in bundles}) == 3
    assert len({bundle.fact.provenance.source_ref.value for bundle in bundles}) == 1


def test_fomc_decision_and_forward_guidance_remain_distinct_facts() -> None:
    item = _item(
        source_id="official-fed-board-press",
        url="https://www.federalreserve.gov/monetarypolicy/monetary20250730a.htm",
    )
    decision = _observation(
        fact_id="fact.fomc.2025-07-30.decision",
        evidence_id="evidence.fomc.2025-07-30.decision",
        kind=OfficialPolicyFactKind.DECISION,
        assertion="target range decision",
        item=item,
        actor_id="actor-gov-us-fomc",
        decision_at=SourceTimestamp.at(
            datetime(2025, 7, 30, 18, 0, tzinfo=timezone.utc),
            source_timezone="EDT",
        ),
    )
    guidance = _observation(
        fact_id="fact.fomc.2025-07-30.guidance",
        evidence_id="evidence.fomc.2025-07-30.guidance",
        kind=OfficialPolicyFactKind.STATEMENT,
        assertion="future adjustments remain under consideration",
        item=item,
        actor_id="actor-gov-us-fomc",
    )
    bundles = build_official_policy_facts((decision, guidance))
    assert bundles[0].fact.fact_type == "official.decision"
    assert bundles[1].fact.fact_type == "official.statement"
    assert "effective_date" not in dict(bundles[0].fact.value)


def test_fact_and_evidence_are_bidirectionally_linked_and_tier1() -> None:
    observation = _observation(
        fact_id="fact.treasury.nprm",
        evidence_id="evidence.treasury.nprm",
        kind=OfficialPolicyFactKind.PROPOSAL,
        assertion="NPRM requests public comment",
        item=_item(
            source_id="official-us-treasury-press",
            url="https://home.treasury.gov/news/press-releases/jy2421",
        ),
        actor_id="actor-gov-us-treasury",
    )
    bundle = build_official_policy_fact(observation)
    assert bundle.fact.evidence_record_ids == ("evidence.treasury.nprm",)
    assert bundle.evidence.target_record_ids == ("fact.treasury.nprm",)
    assert bundle.evidence.quality_class.value == "tier_1_official"
    assert bundle.fact.provenance.published_at is None


def test_duplicate_fact_or_evidence_ids_are_rejected() -> None:
    one = _observation(
        fact_id="fact.same",
        evidence_id="evidence.one",
        kind=OfficialPolicyFactKind.STATEMENT,
        assertion="one",
    )
    duplicate_fact = _observation(
        fact_id="fact.same",
        evidence_id="evidence.two",
        kind=OfficialPolicyFactKind.STATEMENT,
        assertion="two",
    )
    with pytest.raises(ContractViolation):
        build_official_policy_facts((one, duplicate_fact))

    duplicate_evidence = _observation(
        fact_id="fact.two",
        evidence_id="evidence.one",
        kind=OfficialPolicyFactKind.STATEMENT,
        assertion="two",
    )
    with pytest.raises(ContractViolation):
        build_official_policy_facts((one, duplicate_evidence))
