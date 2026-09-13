"""Deterministic earnings Canary quality reporting for E0-007.

The report reconciles source-grounded earnings Facts and segment extraction
resolutions without choosing a winning source when values disagree.  It reports
coverage, agreement, conflicts, fallback methods, and unresolved extraction
failures for AMD/NVDA over multiple fiscal periods.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from orderscope_local.contracts import ContractViolation, Fact

from .segment_revenue import SegmentRevenueResolution, SegmentRevenueStatus


class EarningsQualitySource(StrEnum):
    SEC = "sec"
    ISSUER_IR = "issuer_ir"


class MetricReconciliationStatus(StrEnum):
    AGREEMENT = "agreement"
    SINGLE_SOURCE = "single_source"
    CONFLICT = "conflict"


class SegmentExtractionStatus(StrEnum):
    EXTRACTED = "extracted"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class EarningsFactEvidence:
    source: EarningsQualitySource
    fact: Fact

    def __post_init__(self) -> None:
        if not isinstance(self.source, EarningsQualitySource):
            raise ContractViolation("earnings quality source is invalid")
        if not isinstance(self.fact, Fact) or not self.fact.fact_type.startswith("earnings."):
            raise ContractViolation("earnings quality evidence requires an earnings Fact")
        source_ref = self.fact.provenance.source_ref.value
        if self.source is EarningsQualitySource.SEC and "sec.gov" not in source_ref:
            raise ContractViolation("SEC quality evidence must use SEC provenance")
        if self.source is EarningsQualitySource.ISSUER_IR and not any(
            host in source_ref for host in ("ir.amd.com", "investor.nvidia.com", "nvidianews.nvidia.com")
        ):
            raise ContractViolation("issuer IR quality evidence must use configured issuer provenance")


@dataclass(frozen=True, slots=True)
class EarningsMetricQuality:
    instrument_id: str
    fiscal_year_label: str
    fiscal_quarter: str
    period_end: date
    fact_type: str
    accounting_basis: str
    status: MetricReconciliationStatus
    values_by_source: Mapping[str, str]
    fact_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.instrument_id not in {"AMD", "NVDA"}:
            raise ContractViolation("metric quality row is outside the corporate canary")
        if not isinstance(self.status, MetricReconciliationStatus):
            raise ContractViolation("metric quality status is invalid")
        if not isinstance(self.values_by_source, Mapping) or not self.values_by_source:
            raise ContractViolation("metric quality row requires source values")
        object.__setattr__(self, "values_by_source", MappingProxyType(dict(self.values_by_source)))
        if len(self.fact_record_ids) != len(set(self.fact_record_ids)) or not self.fact_record_ids:
            raise ContractViolation("metric quality Fact references must be unique and non-empty")


@dataclass(frozen=True, slots=True)
class SegmentQualityCheck:
    instrument_id: str
    fiscal_year_label: str
    fiscal_quarter: str
    period_end: date
    segment_id: str
    raw_label: str
    resolution: SegmentRevenueResolution

    def __post_init__(self) -> None:
        if self.instrument_id not in {"AMD", "NVDA"}:
            raise ContractViolation("segment quality check is outside the corporate canary")
        for field, value in (("segment_id", self.segment_id), ("raw_label", self.raw_label)):
            if not isinstance(value, str) or not value.strip():
                raise ContractViolation(f"segment quality {field} must be explicit")
        if not isinstance(self.resolution, SegmentRevenueResolution):
            raise ContractViolation("segment quality check requires a resolution")
        if self.resolution.observation is not None:
            observation = self.resolution.observation
            if observation.instrument_id != self.instrument_id or observation.period_end != self.period_end:
                raise ContractViolation("segment quality resolution does not match event identity")


@dataclass(frozen=True, slots=True)
class SegmentExtractionQuality:
    instrument_id: str
    fiscal_year_label: str
    fiscal_quarter: str
    period_end: date
    segment_id: str
    raw_label: str
    status: SegmentExtractionStatus
    successful_method: str | None
    failure_path: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EarningsCanaryQualityReport:
    metric_rows: tuple[EarningsMetricQuality, ...]
    segment_rows: tuple[SegmentExtractionQuality, ...]
    metric_checks: int
    metric_agreements: int
    metric_single_source: int
    metric_conflicts: int
    segment_checks: int
    segment_extracted: int
    segment_unresolved: int

    @property
    def metric_agreement_rate(self) -> float:
        comparable = self.metric_agreements + self.metric_conflicts
        return 1.0 if comparable == 0 else self.metric_agreements / comparable

    @property
    def segment_extraction_rate(self) -> float:
        return 1.0 if self.segment_checks == 0 else self.segment_extracted / self.segment_checks


def build_earnings_canary_quality_report(
    *,
    earnings_facts: tuple[EarningsFactEvidence, ...],
    segment_checks: tuple[SegmentQualityCheck, ...],
) -> EarningsCanaryQualityReport:
    """Build a deterministic quality report without resolving source conflicts.

    Basic Facts are grouped by event/metric/accounting basis.  Equal values from
    SEC and issuer IR are agreement; differing values are conflict.  A conflict
    remains visible and no source is selected as authoritative by this report.
    Segment checks report the successful fallback method or the complete failure
    path recorded by E0-005.
    """

    if not isinstance(earnings_facts, tuple) or any(
        not isinstance(item, EarningsFactEvidence) for item in earnings_facts
    ):
        raise ContractViolation("earnings quality facts must be an immutable evidence tuple")
    if not isinstance(segment_checks, tuple) or any(
        not isinstance(item, SegmentQualityCheck) for item in segment_checks
    ):
        raise ContractViolation("segment quality checks must be an immutable tuple")

    grouped: dict[tuple[str, str, str, date, str, str], list[EarningsFactEvidence]] = {}
    for evidence in earnings_facts:
        fact = evidence.fact
        value = fact.value
        if not isinstance(value, Mapping):
            raise ContractViolation("E0-007 requires E0-004 structured earnings Fact values")
        required = ("amount", "accounting_basis", "fiscal_year_label", "fiscal_quarter")
        if any(key not in value for key in required):
            raise ContractViolation("earnings Fact lacks E0-004 reconciliation fields")
        if fact.period_end is None or fact.period_end.calendar_date is None:
            raise ContractViolation("earnings quality reconciliation requires date-precision period_end")
        instrument_id = fact.subject_ref.removeprefix("instrument:")
        key = (
            instrument_id,
            str(value["fiscal_year_label"]),
            str(value["fiscal_quarter"]),
            fact.period_end.calendar_date,
            fact.fact_type,
            str(value["accounting_basis"]),
        )
        grouped.setdefault(key, []).append(evidence)

    metric_rows: list[EarningsMetricQuality] = []
    for key in sorted(grouped, key=lambda item: (item[0], item[3], item[4], item[5], item[1], item[2])):
        items = grouped[key]
        by_source: dict[str, str] = {}
        record_ids: list[str] = []
        for evidence in sorted(items, key=lambda item: (item.source.value, item.fact.record_id)):
            amount = str(evidence.fact.value["amount"])
            previous = by_source.get(evidence.source.value)
            if previous is not None and previous != amount:
                raise ContractViolation("same source has conflicting basic earnings Facts for one quality key")
            by_source[evidence.source.value] = amount
            record_ids.append(evidence.fact.record_id)
        if len(by_source) == 1:
            status = MetricReconciliationStatus.SINGLE_SOURCE
        elif len(set(by_source.values())) == 1:
            status = MetricReconciliationStatus.AGREEMENT
        else:
            status = MetricReconciliationStatus.CONFLICT
        metric_rows.append(
            EarningsMetricQuality(
                instrument_id=key[0],
                fiscal_year_label=key[1],
                fiscal_quarter=key[2],
                period_end=key[3],
                fact_type=key[4],
                accounting_basis=key[5],
                status=status,
                values_by_source=by_source,
                fact_record_ids=tuple(record_ids),
            )
        )

    segment_rows: list[SegmentExtractionQuality] = []
    for check in sorted(
        segment_checks,
        key=lambda item: (item.instrument_id, item.period_end, item.segment_id, item.raw_label),
    ):
        resolution = check.resolution
        if resolution.observation is not None:
            status = SegmentExtractionStatus.EXTRACTED
            successful_method = resolution.observation.method.value
        else:
            status = SegmentExtractionStatus.UNRESOLVED
            successful_method = None
        failure_path = tuple(
            f"{attempt.method.value}:{attempt.failure_reason.value}"
            for attempt in resolution.attempts
            if attempt.status is not SegmentRevenueStatus.SUCCESS and attempt.failure_reason is not None
        )
        segment_rows.append(
            SegmentExtractionQuality(
                instrument_id=check.instrument_id,
                fiscal_year_label=check.fiscal_year_label,
                fiscal_quarter=check.fiscal_quarter,
                period_end=check.period_end,
                segment_id=check.segment_id,
                raw_label=check.raw_label,
                status=status,
                successful_method=successful_method,
                failure_path=failure_path,
            )
        )

    metric_tuple = tuple(metric_rows)
    segment_tuple = tuple(segment_rows)
    return EarningsCanaryQualityReport(
        metric_rows=metric_tuple,
        segment_rows=segment_tuple,
        metric_checks=len(metric_tuple),
        metric_agreements=sum(row.status is MetricReconciliationStatus.AGREEMENT for row in metric_tuple),
        metric_single_source=sum(row.status is MetricReconciliationStatus.SINGLE_SOURCE for row in metric_tuple),
        metric_conflicts=sum(row.status is MetricReconciliationStatus.CONFLICT for row in metric_tuple),
        segment_checks=len(segment_tuple),
        segment_extracted=sum(row.status is SegmentExtractionStatus.EXTRACTED for row in segment_tuple),
        segment_unresolved=sum(row.status is SegmentExtractionStatus.UNRESOLVED for row in segment_tuple),
    )


def render_earnings_canary_quality_markdown(report: EarningsCanaryQualityReport) -> str:
    """Render stable human-reviewable Markdown from a quality report."""

    if not isinstance(report, EarningsCanaryQualityReport):
        raise ContractViolation("quality markdown requires an EarningsCanaryQualityReport")
    lines = [
        "# Earnings Canary Quality Report",
        "",
        f"- Metric checks: {report.metric_checks}",
        f"- Agreements: {report.metric_agreements}",
        f"- Single-source: {report.metric_single_source}",
        f"- Conflicts: {report.metric_conflicts}",
        f"- Segment checks: {report.segment_checks}",
        f"- Segment extracted: {report.segment_extracted}",
        f"- Segment unresolved: {report.segment_unresolved}",
        "",
        "## Basic earnings reconciliation",
        "",
        "| Instrument | Period | Metric | Basis | Status | Sources |",
        "|---|---|---|---|---|---|",
    ]
    for row in report.metric_rows:
        sources = "; ".join(f"{key}={value}" for key, value in sorted(row.values_by_source.items()))
        lines.append(
            f"| {row.instrument_id} | {row.fiscal_year_label} {row.fiscal_quarter} ({row.period_end}) | "
            f"{row.fact_type} | {row.accounting_basis} | {row.status.value} | {sources} |"
        )
    lines.extend(
        [
            "",
            "## Segment extraction",
            "",
            "| Instrument | Period | Segment | Status | Method / failure path |",
            "|---|---|---|---|---|",
        ]
    )
    for row in report.segment_rows:
        detail = row.successful_method or "; ".join(row.failure_path) or "unresolved"
        lines.append(
            f"| {row.instrument_id} | {row.fiscal_year_label} {row.fiscal_quarter} ({row.period_end}) | "
            f"{row.segment_id} ({row.raw_label}) | {row.status.value} | {detail} |"
        )
    return "\n".join(lines) + "\n"
