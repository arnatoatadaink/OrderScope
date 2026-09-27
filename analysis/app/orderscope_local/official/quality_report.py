"""Integrated Official Signal quality matrix for O0-005.

This module combines O0-002 acquisition/change observations, O0-003 semantic Fact
classification, and O0-004 relevance outcomes into one deterministic quality
summary. It does not reinterpret source semantics or infer deletion/relevance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from orderscope_local.contracts import ContractViolation, TimestampPrecision

from .feed_adapter import OfficialDiscoveredItem, OfficialItemAvailability
from .official_statement import OfficialPolicyFactKind, OfficialPolicyObservation
from .relevance import OfficialRelevanceClass, OfficialRelevanceObservation


class OfficialQualitySeverity(StrEnum):
    PASS = "pass"
    REVIEW = "review"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class OfficialSignalQualityCase:
    case_id: str
    item: OfficialDiscoveredItem
    policy_observations: tuple[OfficialPolicyObservation, ...]
    relevance_observations: tuple[OfficialRelevanceObservation, ...]
    previous_item: OfficialDiscoveredItem | None = None

    def __post_init__(self) -> None:
        if not self.case_id or self.case_id != self.case_id.strip() or len(self.case_id) > 160:
            raise ContractViolation("official quality case_id must be bounded canonical text")
        if not isinstance(self.item, OfficialDiscoveredItem):
            raise ContractViolation("official quality case requires OfficialDiscoveredItem")
        if not isinstance(self.policy_observations, tuple) or not self.policy_observations:
            raise ContractViolation("official quality case requires semantic policy observations")
        if not isinstance(self.relevance_observations, tuple) or not self.relevance_observations:
            raise ContractViolation("official quality case requires relevance observations")
        if any(obs.item.canonical_item_url != self.item.canonical_item_url for obs in self.policy_observations):
            raise ContractViolation("official quality policy observations must use the case item")
        policy_ids = {obs.fact_id for obs in self.policy_observations}
        if any(obs.subject_fact_id not in policy_ids for obs in self.relevance_observations):
            raise ContractViolation("official quality relevance must target a policy Fact in the same case")
        if self.previous_item is not None:
            if self.previous_item.source_id != self.item.source_id or self.previous_item.canonical_item_url != self.item.canonical_item_url:
                raise ContractViolation("official quality previous_item must match source/canonical URL")


@dataclass(frozen=True, slots=True)
class OfficialSignalQualityFinding:
    case_id: str
    check: str
    severity: OfficialQualitySeverity
    detail: str


@dataclass(frozen=True, slots=True)
class OfficialSignalQualityReport:
    cases: int
    pass_count: int
    review_count: int
    error_count: int
    findings: tuple[OfficialSignalQualityFinding, ...]

    @property
    def accepted(self) -> bool:
        return self.error_count == 0


def assess_official_signal_quality(
    cases: tuple[OfficialSignalQualityCase, ...],
) -> OfficialSignalQualityReport:
    if not isinstance(cases, tuple) or not cases:
        raise ContractViolation("official quality assessment requires immutable non-empty cases")
    if len({case.case_id for case in cases}) != len(cases):
        raise ContractViolation("official quality case IDs must be unique")

    findings: list[OfficialSignalQualityFinding] = []
    for case in cases:
        findings.extend(_assess_case(case))

    return OfficialSignalQualityReport(
        cases=len(cases),
        pass_count=sum(item.severity is OfficialQualitySeverity.PASS for item in findings),
        review_count=sum(item.severity is OfficialQualitySeverity.REVIEW for item in findings),
        error_count=sum(item.severity is OfficialQualitySeverity.ERROR for item in findings),
        findings=tuple(findings),
    )


def render_official_signal_quality_markdown(report: OfficialSignalQualityReport) -> str:
    lines = [
        "# Official Signal Canary Quality",
        "",
        f"- cases: {report.cases}",
        f"- pass: {report.pass_count}",
        f"- review: {report.review_count}",
        f"- error: {report.error_count}",
        f"- accepted: {'yes' if report.accepted else 'no'}",
        "",
        "| Case | Check | Severity | Detail |",
        "|---|---|---|---|",
    ]
    for finding in report.findings:
        detail = finding.detail.replace("|", "\\|")
        lines.append(f"| {finding.case_id} | {finding.check} | {finding.severity.value} | {detail} |")
    return "\n".join(lines) + "\n"


def _assess_case(case: OfficialSignalQualityCase) -> list[OfficialSignalQualityFinding]:
    out: list[OfficialSignalQualityFinding] = []

    # Availability/update boundary.
    if case.item.availability is OfficialItemAvailability.LISTING_MISSING:
        out.append(_finding(case, "availability", OfficialQualitySeverity.REVIEW, "listing_missing is not deletion"))
    elif case.item.availability is OfficialItemAvailability.CANONICAL_UNAVAILABLE:
        out.append(_finding(case, "availability", OfficialQualitySeverity.REVIEW, "canonical unavailable retained as history, not hard delete"))
    else:
        out.append(_finding(case, "availability", OfficialQualitySeverity.PASS, "canonical item is present"))

    if case.previous_item is None:
        out.append(_finding(case, "revision", OfficialQualitySeverity.PASS, "new canonical observation"))
    elif case.previous_item.content_hash.digest == case.item.content_hash.digest:
        out.append(_finding(case, "revision", OfficialQualitySeverity.PASS, "same URL/hash is unchanged"))
    else:
        out.append(_finding(case, "revision", OfficialQualitySeverity.REVIEW, "same canonical URL with changed hash is a revision candidate"))

    # Timestamp precision boundary.
    published = case.item.published_at
    if published is not None and published.precision is TimestampPrecision.DATE_ONLY:
        out.append(_finding(case, "timestamp_precision", OfficialQualitySeverity.PASS, "date-only publication remains date-only"))
    else:
        out.append(_finding(case, "timestamp_precision", OfficialQualitySeverity.PASS, "no fabricated publication precision detected"))

    # Semantic separation boundary.
    kinds = {obs.fact_kind for obs in case.policy_observations}
    semantic_error = False
    for obs in case.policy_observations:
        if obs.fact_kind in {OfficialPolicyFactKind.STATEMENT, OfficialPolicyFactKind.PROPOSAL}:
            semantic_error |= obs.decision_at is not None or obs.effective_at is not None or obs.effective_expression is not None
        elif obs.fact_kind is OfficialPolicyFactKind.DECISION:
            semantic_error |= obs.decision_at is None or obs.effective_at is not None or obs.effective_expression is not None
        elif obs.fact_kind is OfficialPolicyFactKind.IMPLEMENTATION:
            semantic_error |= obs.decision_at is not None or ((obs.effective_at is None) == (obs.effective_expression is None))
    if semantic_error:
        out.append(_finding(case, "semantic_separation", OfficialQualitySeverity.ERROR, "policy semantic promotion boundary violated"))
    elif len(kinds) > 1:
        out.append(_finding(case, "semantic_separation", OfficialQualitySeverity.PASS, "multiple semantic Facts preserved from the source item"))
    else:
        out.append(_finding(case, "semantic_separation", OfficialQualitySeverity.PASS, "semantic Fact kind remains explicit"))

    # Relevance false-positive boundary.
    classes = {obs.classification for obs in case.relevance_observations}
    direct = [obs for obs in case.relevance_observations if obs.classification is OfficialRelevanceClass.DIRECT_INSTRUMENT]
    if OfficialRelevanceClass.THEME_EXPOSURE in classes and direct:
        # Direct + theme is valid only when direct observation independently passed its O0-004 constructor.
        out.append(_finding(case, "relevance", OfficialQualitySeverity.PASS, "direct instrument and theme exposure are retained as separate Evidence-grounded links"))
    elif OfficialRelevanceClass.THEME_EXPOSURE in classes:
        out.append(_finding(case, "relevance", OfficialQualitySeverity.PASS, "theme exposure does not fan out to AMD/NVDA"))
    elif OfficialRelevanceClass.MENTION_ONLY in classes:
        out.append(_finding(case, "relevance", OfficialQualitySeverity.PASS, "mention-only evidence is not promoted to instrument relevance"))
    elif OfficialRelevanceClass.UNRESOLVED in classes:
        out.append(_finding(case, "relevance", OfficialQualitySeverity.REVIEW, "unresolved relevance remains pending review"))
    elif OfficialRelevanceClass.NO_LINK in classes:
        out.append(_finding(case, "relevance", OfficialQualitySeverity.PASS, "no-link emits no inferred relation"))
    else:
        out.append(_finding(case, "relevance", OfficialQualitySeverity.PASS, "direct relevance uses explicit O0-004 thresholds"))

    return out


def _finding(case: OfficialSignalQualityCase, check: str, severity: OfficialQualitySeverity, detail: str) -> OfficialSignalQualityFinding:
    return OfficialSignalQualityFinding(case.case_id, check, severity, detail)
