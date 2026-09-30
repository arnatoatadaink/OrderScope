from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts.errors import ContractViolation
from orderscope_local.theme import (
    CalibratedCriteria,
    CaseLabel,
    EventThemeHypotheses,
    EventThemeHypothesis,
    ExposureStrength,
    HistoricalThemeCase,
    MemberReaction,
    PARENT_THEME,
    ReactionDirection,
    RelationType,
    ThemeExposure,
    ThemeExposureSet,
    ThemeId,
    ThemeState,
    assess_activation,
    assess_repricing,
    assess_rotation,
    observe_theme_reaction,
    summarize_historical_cases,
)


START = datetime(2026, 9, 1, tzinfo=timezone.utc)
END = START + timedelta(hours=1)
ACCEPTED = END + timedelta(hours=1)


def exposure(theme: ThemeId, subject: str = "company:EXAMPLE") -> ThemeExposure:
    return ThemeExposure(
        subject_ref=subject, theme=theme, strength=ExposureStrength.MATERIAL,
        evidence_refs=(f"evidence:{theme.value.lower()}",),
        effective_from=START, accepted_at=ACCEPTED,
    )


def hypothesis(
    theme: ThemeId = ThemeId.AI_SECURITY,
    direction: ReactionDirection = ReactionDirection.POSITIVE,
    event: str = "event:cyber-1",
    event_class: str = "MAJOR_CYBERATTACK",
) -> EventThemeHypothesis:
    return EventThemeHypothesis(
        event_ref=event, event_class=event_class, theme=theme,
        relation=RelationType.THREAT_ACCELERATOR, expected_direction=direction,
        event_evidence_refs=("evidence:incident-report",),
        rationale_ref="analysis:threat-hypothesis", accepted_at=ACCEPTED,
    )


def member(
    name: str, theme: ThemeId = ThemeId.AI_SECURITY, relative: float = 2.0,
    start: datetime = START, persisted: bool | None = True,
) -> MemberReaction:
    return MemberReaction(
        subject_ref=f"instrument:{name}", theme=theme,
        window_start=start, window_end=start + timedelta(hours=1),
        return_pct=relative + 0.5, benchmark_return_pct=0.5,
        volume_ratio=1.4, metric_refs=(f"metric:{name}:{start.strftime('%Y%m%dT%H%M%S')}",),
        next_session_persisted=persisted,
    )


def observation(
    theme: ThemeId = ThemeId.AI_SECURITY, direction: ReactionDirection = ReactionDirection.POSITIVE,
    event: str = "event:cyber-1", start: datetime = START, relative: float = 2.0,
):
    h = hypothesis(theme=theme, direction=direction, event=event)
    names = ("AAA", "BBB", "CCC") if theme is ThemeId.AI_SECURITY else ("DDD", "EEE", "FFF")
    return observe_theme_reaction(
        h, tuple(member(name, theme=theme, relative=relative, start=start) for name in names),
    )


def criteria() -> CalibratedCriteria:
    return CalibratedCriteria(
        calibration_ref="calibration:historical-reviewed",
        min_members=3, min_directional_breadth=0.6,
        min_abs_median_relative_return_pct=1.0,
        min_median_volume_ratio=1.2, min_persistent_members=2,
    )


def test_multi_theme_exposure_does_not_infer_parent_or_permanent_opposition():
    exposures = ThemeExposureSet((exposure(ThemeId.AI_APPLICATION), exposure(ThemeId.DEFENSE_INDUSTRIAL)))
    assert exposures.has_explicit(ThemeId.AI_APPLICATION)
    assert exposures.has_explicit(ThemeId.DEFENSE_INDUSTRIAL)
    assert not exposures.has_explicit(ThemeId.AI)
    assert PARENT_THEME[ThemeId.PHYSICAL_AI] is ThemeId.AI_APPLICATION
    assert PARENT_THEME[ThemeId.DEFENSE_INDUSTRIAL] is None


def test_reject_duplicate_or_ungrounded_exposure():
    with pytest.raises(ContractViolation, match="duplicate"):
        ThemeExposureSet((exposure(ThemeId.AI_SECURITY), exposure(ThemeId.AI_SECURITY)))
    with pytest.raises(ContractViolation, match="evidence_refs"):
        replace(exposure(ThemeId.AI_SECURITY), evidence_refs=())


def test_event_may_support_security_and_foundation_together():
    hypotheses = EventThemeHypotheses((
        hypothesis(ThemeId.AI_FOUNDATION, event="event:ai-adoption"),
        hypothesis(ThemeId.AI_SECURITY, event="event:ai-adoption"),
        hypothesis(ThemeId.AI_GOVERNANCE, event="event:ai-adoption"),
    ))
    assert len(hypotheses.hypotheses) == 3
    assert all(item.expected_direction.sign == 1 for item in hypotheses.hypotheses)


def test_numeric_or_duplicate_event_coefficients_are_rejected():
    with pytest.raises(ContractViolation, match="categorical"):
        replace(hypothesis(), expected_direction=0.8)
    with pytest.raises(ContractViolation, match="duplicate"):
        EventThemeHypotheses((hypothesis(), hypothesis()))


def test_observation_is_descriptive_and_single_name_never_confirms():
    h = hypothesis()
    single = observe_theme_reaction(h, (member("AAA"),))
    assert single.median_relative_return_pct == 2.0
    assert assess_activation(single, criteria=criteria()).state is ThemeState.UNKNOWN
    three = observation()
    assert three.directional_breadth == 1.0
    assert three.median_volume_ratio == 1.4
    assert three.volume_assessed_members == 3
    assert assess_activation(three).state is ThemeState.ACTIVATION_CANDIDATE
    assert assess_activation(three, criteria=criteria()).state is ThemeState.ACTIVATION_CONFIRMED


def test_missing_or_contradictory_market_evidence_stays_conservative():
    h = hypothesis()
    wrong = observe_theme_reaction(h, tuple(member(x, relative=-2.0) for x in ("AAA", "BBB", "CCC")))
    assert assess_activation(wrong).state is ThemeState.REJECTED
    incomplete = observe_theme_reaction(
        h, tuple(member(x, persisted=None) for x in ("AAA", "BBB", "CCC")),
    )
    assert assess_activation(incomplete, criteria=criteria()).state is ThemeState.ACTIVATION_CANDIDATE
    with pytest.raises(ContractViolation, match="one member"):
        observe_theme_reaction(h, (member("AAA"), member("AAA")))


def test_rotation_is_event_local_not_structural_antagonism():
    source = observation(ThemeId.AI_FOUNDATION, ReactionDirection.NEGATIVE, relative=-2.0)
    target = observation(ThemeId.AI_SECURITY, ReactionDirection.POSITIVE, relative=2.0)
    candidate = assess_rotation(source, target)
    assert candidate.state is ThemeState.ROTATION_CANDIDATE
    assert "no permanent" in candidate.reason
    assert assess_rotation(source, target, source_criteria=criteria(), destination_criteria=criteria()).state is ThemeState.ROTATION_CONFIRMED
    with pytest.raises(ContractViolation, match="same window"):
        assess_rotation(source, observation(start=END))


def test_repricing_requires_distinct_ordered_events_and_calibration():
    first = observation()
    second = observation(event="event:cyber-2", start=START + timedelta(days=1))
    assert assess_repricing(first, second).state is ThemeState.REPRICING_CANDIDATE
    assert assess_repricing(first, second, criteria=criteria()).state is ThemeState.REPRICING_CONFIRMED
    with pytest.raises(ContractViolation, match="distinct"):
        assess_repricing(first, first)


def test_calibration_summarizes_cases_without_making_up_thresholds():
    positive = observation()
    negative = observation(event="event:cyber-neg", relative=-2.0)
    control = observation(event="event:cyber-control", relative=0.0)
    cases = tuple(
        HistoricalThemeCase(
            case_ref=f"case:{i}", event_class="MAJOR_CYBERATTACK",
            observation=obs, label=label,
            source_refs=(f"source:{i}",), review_ref=f"review:{i}",
        )
        for i, (obs, label) in enumerate((
            (positive, CaseLabel.POSITIVE),
            (negative, CaseLabel.NEGATIVE),
            (control, CaseLabel.CONTROL),
        ))
    )
    summary = summarize_historical_cases(cases)
    assert summary.ready_for_threshold_review
    assert summary.case_count == 3
    assert not hasattr(summary, "confirmation_threshold")
    assert not summarize_historical_cases(cases[:1]).ready_for_threshold_review


def test_fact_store_materialization_keeps_hypothesis_and_observation_separate():
    h = hypothesis()
    interpretation = h.to_interpretation(record_id="interp:theme:cyber", accepted_at=ACCEPTED)
    assert interpretation.interpretation_type == "event_theme_hypothesis"
    assert interpretation.statement["expected_direction"] == "POSITIVE"
    assert interpretation.basis_record_ids == ("evidence:incident-report",)
    metric = observation().to_derived_metric(record_id="metric:theme:cyber", accepted_at=ACCEPTED)
    assert metric.metric_name == "theme_reaction_observation"
    assert metric.value["member_count"] == 3
    assert len(metric.input_record_ids) == 3
    assert "buyer" not in metric.value
    with pytest.raises(ContractViolation, match="cannot precede"):
        observation().to_derived_metric(record_id="metric:early", accepted_at=START)


def test_partial_volume_coverage_cannot_confirm_theme():
    h = hypothesis()
    basket = (
        member("AAA"),
        replace(member("BBB"), volume_ratio=None),
        replace(member("CCC"), volume_ratio=None),
    )
    observed = observe_theme_reaction(h, basket)
    assert observed.volume_assessed_members == 1
    assert assess_activation(observed, criteria=criteria()).state is ThemeState.ACTIVATION_CANDIDATE


def test_theme_state_materializes_as_interpretation_with_metric_basis():
    candidate = assess_activation(observation())
    record = candidate.to_interpretation(
        record_id="interp:theme:activation",
        generated_at=END,
        accepted_at=ACCEPTED,
        event_evidence_refs=("evidence:incident-report",),
    )
    assert record.interpretation_type == "theme_state"
    assert record.statement["state"] == ThemeState.ACTIVATION_CANDIDATE.value
    assert record.statement["calibration_ref"] is None
    assert len(record.basis_record_ids) == 4
    assert "evidence:incident-report" in record.basis_record_ids
