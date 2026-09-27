"""New York Fed reference-rate source adapter for UWBS-033."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from math import isfinite

from orderscope_local.contracts import ContractViolation, MacroMarketRegion, MacroMarketSeriesKind, SourceTimestamp

NY_FED_REFERENCE_RATE_SOURCE = "ny-fed:reference-rates"
_ALLOWED_TYPES = frozenset({"EFFR", "SOFR", "OBFR"})


@dataclass(frozen=True, kw_only=True, slots=True)
class NyFedReferenceRatePoint:
    series_id: str
    series_kind: MacroMarketSeriesKind
    region: MacroMarketRegion
    value: float
    unit: str
    observed_at: SourceTimestamp
    source_ref: str
    revision_indicator: str | None = None
    footnote: str | None = None


def parse_ny_fed_reference_rates_json(
    text: str,
    *,
    start: date | None = None,
    end_exclusive: date | None = None,
    include_types: frozenset[str] = _ALLOWED_TYPES,
) -> tuple[NyFedReferenceRatePoint, ...]:
    if (start is None) != (end_exclusive is None):
        raise ContractViolation("NY Fed window requires both start and end_exclusive")
    if start is not None and start >= end_exclusive:
        raise ContractViolation("NY Fed window must be non-empty")
    if not isinstance(text, str) or not text.strip():
        raise ContractViolation("NY Fed JSON cannot be empty")
    if not isinstance(include_types, frozenset) or not include_types:
        raise ContractViolation("NY Fed include_types must be a non-empty frozenset")
    normalized_types = frozenset(str(value).upper() for value in include_types)
    if not normalized_types <= _ALLOWED_TYPES:
        raise ContractViolation("NY Fed include_types contains unsupported reference-rate type")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractViolation("NY Fed response must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ContractViolation("NY Fed response root must be an object")
    rows = payload.get("refRates", payload.get("rates"))
    if not isinstance(rows, list):
        raise ContractViolation("NY Fed response must contain refRates list")

    points: list[NyFedReferenceRatePoint] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ContractViolation("NY Fed reference-rate row must be an object")
        rate_type = str(row.get("type", "")).strip().upper()
        if rate_type not in normalized_types:
            continue
        raw_date = str(row.get("effectiveDate", row.get("date", ""))).strip()
        if not raw_date:
            raise ContractViolation("NY Fed reference-rate row missing effectiveDate")
        day = _parse_date(raw_date)
        if start is not None and not start <= day < end_exclusive:
            continue

        raw_rate = row.get("percentRate", row.get("rate"))
        if isinstance(raw_rate, bool) or raw_rate is None:
            raise ContractViolation(f"NY Fed {rate_type} row missing percentRate")
        try:
            value = float(raw_rate)
        except (TypeError, ValueError) as exc:
            raise ContractViolation(f"NY Fed {rate_type} percentRate must be numeric") from exc
        if not isfinite(value):
            raise ContractViolation(f"NY Fed {rate_type} percentRate must be finite")

        points.append(
            NyFedReferenceRatePoint(
                series_id=f"US_{rate_type}",
                series_kind=MacroMarketSeriesKind.SHORT_MARKET_RATE,
                region=MacroMarketRegion.US,
                value=value,
                unit="percent",
                observed_at=SourceTimestamp.date_only(day),
                source_ref=f"{NY_FED_REFERENCE_RATE_SOURCE}:{rate_type.lower()}",
                revision_indicator=_optional_text(row.get("revisionIndicator")),
                footnote=_optional_text(row.get("footnote", row.get("rateFootnote"))),
            )
        )
    return tuple(points)


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ContractViolation("NY Fed effectiveDate is not recognized") from exc


def _optional_text(value: object) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ContractViolation("NY Fed metadata must be canonical text when present")
    return value
