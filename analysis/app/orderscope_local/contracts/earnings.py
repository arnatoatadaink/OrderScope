"""Provider-neutral earnings event and result contracts.

The contracts deliberately keep issuer schedule, release, call, fiscal-period,
accounting-basis, and evidence semantics distinct.  Source publication/filing
metadata remains in the shared provenance boundary; callers must not infer a
missing release instant from a call time or SEC acceptance timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
import re

from .errors import ContractViolation
from .provenance import SourceTimestamp, TimestampPrecision


_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._/-]{0,63}")
_CURRENCY = re.compile(r"[A-Z]{3}")


class EarningsEventKind(StrEnum):
    RELEASE = "earnings_release"
    CALL = "earnings_call"


class ScheduledReleaseWindow(StrEnum):
    BEFORE_MARKET_OPEN = "before_market_open"
    DURING_MARKET = "during_market"
    AFTER_MARKET_CLOSE = "after_market_close"
    UNSPECIFIED = "unspecified"


class AccountingBasis(StrEnum):
    GAAP = "gaap"
    NON_GAAP = "non_gaap"


class EarningsEvidenceRole(StrEnum):
    ISSUER_SCHEDULE_ANNOUNCEMENT = "issuer_schedule_announcement"
    ISSUER_RESULT_RELEASE = "issuer_result_release"
    SEC_8K = "sec_8k"
    SEC_EXHIBIT_99_1 = "sec_exhibit_99_1"
    ISSUER_EVENT_PAGE = "issuer_event_page"


@dataclass(frozen=True, slots=True)
class EarningsEvidenceRef:
    evidence_id: str
    role: EarningsEvidenceRole

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise ContractViolation("earnings evidence_id cannot be blank")
        if len(self.evidence_id) > 512:
            raise ContractViolation("earnings evidence_id exceeds 512 characters")
        if not isinstance(self.role, EarningsEvidenceRole):
            raise ContractViolation("earnings evidence role is invalid")


@dataclass(frozen=True, slots=True)
class EarningsEvent:
    """One issuer earnings release or call for a fiscal period.

    ``scheduled_at`` records only the precision established by the source.  A
    release announced merely as a calendar date plus a market window therefore
    stays date-only; the window is not converted to an invented clock time.
    ``actual_release_at`` is nullable and is valid only for release events.
    """

    instrument_id: str
    event_kind: EarningsEventKind
    fiscal_year_label: str
    fiscal_quarter: str
    period_end: date
    evidence: tuple[EarningsEvidenceRef, ...]
    scheduled_at: SourceTimestamp | None = None
    scheduled_release_window: ScheduledReleaseWindow | None = None
    actual_release_at: SourceTimestamp | None = None

    def __post_init__(self) -> None:
        _require_label(self.instrument_id, "instrument_id")
        _require_label(self.fiscal_year_label, "fiscal_year_label")
        _require_label(self.fiscal_quarter, "fiscal_quarter")
        if not isinstance(self.event_kind, EarningsEventKind):
            raise ContractViolation("earnings event_kind is invalid")
        if not isinstance(self.period_end, date):
            raise ContractViolation("earnings period_end must be a date")
        _validate_evidence(self.evidence)
        if self.scheduled_at is not None and not isinstance(self.scheduled_at, SourceTimestamp):
            raise ContractViolation("earnings scheduled_at must be a SourceTimestamp")
        if self.actual_release_at is not None and not isinstance(
            self.actual_release_at, SourceTimestamp
        ):
            raise ContractViolation("actual_release_at must be a SourceTimestamp")

        if self.event_kind is EarningsEventKind.CALL:
            if self.scheduled_release_window is not None:
                raise ContractViolation("earnings call cannot have a release window")
            if self.actual_release_at is not None:
                raise ContractViolation("earnings call cannot carry actual_release_at")
            if (
                self.scheduled_at is not None
                and self.scheduled_at.precision is TimestampPrecision.DATE_ONLY
            ):
                raise ContractViolation("earnings call scheduled_at requires an established instant")
        else:
            if self.scheduled_release_window is not None and not isinstance(
                self.scheduled_release_window, ScheduledReleaseWindow
            ):
                raise ContractViolation("scheduled release window is invalid")
            if (
                self.actual_release_at is not None
                and self.actual_release_at.precision is TimestampPrecision.DATE_ONLY
            ):
                raise ContractViolation(
                    "actual_release_at requires an established instant; keep unknown exact time null"
                )


@dataclass(frozen=True, slots=True)
class EarningsResultMetric:
    """One observed earnings metric, preserving basis, period, unit, and evidence."""

    instrument_id: str
    fiscal_year_label: str
    fiscal_quarter: str
    period_end: date
    metric_type: str
    value: Decimal
    unit: str
    accounting_basis: AccountingBasis
    evidence: tuple[EarningsEvidenceRef, ...]
    currency: str | None = None

    def __post_init__(self) -> None:
        _require_label(self.instrument_id, "instrument_id")
        _require_label(self.fiscal_year_label, "fiscal_year_label")
        _require_label(self.fiscal_quarter, "fiscal_quarter")
        _require_label(self.metric_type, "metric_type")
        _require_label(self.unit, "unit")
        if not isinstance(self.period_end, date):
            raise ContractViolation("earnings metric period_end must be a date")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ContractViolation("earnings metric value must be a finite Decimal")
        if not isinstance(self.accounting_basis, AccountingBasis):
            raise ContractViolation("earnings accounting_basis is invalid")
        if self.currency is not None and (
            not isinstance(self.currency, str) or _CURRENCY.fullmatch(self.currency) is None
        ):
            raise ContractViolation("earnings currency must be an explicit ISO-style code")
        _validate_evidence(self.evidence)


def _require_label(value: object, field: str) -> None:
    if not isinstance(value, str) or _LABEL.fullmatch(value) is None:
        raise ContractViolation(f"earnings {field} must be bounded canonical text")


def _validate_evidence(value: object) -> None:
    if not isinstance(value, tuple) or not value:
        raise ContractViolation("earnings evidence must be a non-empty tuple")
    if any(not isinstance(item, EarningsEvidenceRef) for item in value):
        raise ContractViolation("earnings evidence contains an invalid reference")
    keys = {(item.evidence_id, item.role) for item in value}
    if len(keys) != len(value):
        raise ContractViolation("earnings evidence cannot contain duplicate references")
