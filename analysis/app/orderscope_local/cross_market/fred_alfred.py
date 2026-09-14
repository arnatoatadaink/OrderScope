"""FRED/ALFRED revision-aware fallback parsing for UWBS-035.

This module is fallback-only. Callers must supply the underlying source and terms
references explicitly so a FRED series ID cannot silently replace an official
source with different semantics or licensing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from math import isfinite

from orderscope_local.contracts import (
    ContractViolation,
    MacroMarketRegion,
    MacroMarketSeriesKind,
    SourceTimestamp,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class FredSeriesDescriptor:
    series_id: str
    series_kind: MacroMarketSeriesKind
    region: MacroMarketRegion
    unit: str
    underlying_source_ref: str
    terms_ref: str
    tenor: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.series_id, "series_id"),
            (self.unit, "unit"),
            (self.underlying_source_ref, "underlying_source_ref"),
            (self.terms_ref, "terms_ref"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if not isinstance(self.series_kind, MacroMarketSeriesKind):
            raise ContractViolation("series_kind must be MacroMarketSeriesKind")
        if not isinstance(self.region, MacroMarketRegion):
            raise ContractViolation("region must be MacroMarketRegion")
        if self.tenor is not None and (not self.tenor.strip() or self.tenor != self.tenor.strip()):
            raise ContractViolation("tenor must be canonical non-empty text")


@dataclass(frozen=True, kw_only=True, slots=True)
class FredVintageObservation:
    descriptor: FredSeriesDescriptor
    value: float
    observed_at: SourceTimestamp
    realtime_start: SourceTimestamp
    realtime_end: SourceTimestamp

    @property
    def source_ref(self) -> str:
        return f"fred:{self.descriptor.series_id}"


@dataclass(frozen=True, kw_only=True, slots=True)
class FredVintageDate:
    series_id: str
    vintage_date: SourceTimestamp


def parse_fred_observations_json(
    text: str,
    *,
    descriptor: FredSeriesDescriptor,
) -> tuple[FredVintageObservation, ...]:
    payload = _json_object(text, "FRED observations")
    rows = payload.get("observations")
    if not isinstance(rows, list):
        raise ContractViolation("FRED observations response must contain observations list")

    output: list[FredVintageObservation] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ContractViolation("FRED observation row must be an object")
        raw_value = row.get("value")
        if raw_value in {None, ".", ""}:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ContractViolation("FRED observation value must be numeric") from exc
        if not isfinite(value):
            raise ContractViolation("FRED observation value must be finite")

        output.append(
            FredVintageObservation(
                descriptor=descriptor,
                value=value,
                observed_at=SourceTimestamp.date_only(_date(row.get("date"), "FRED observation date")),
                realtime_start=SourceTimestamp.date_only(
                    _date(row.get("realtime_start", payload.get("realtime_start")), "FRED realtime_start")
                ),
                realtime_end=SourceTimestamp.date_only(
                    _date(row.get("realtime_end", payload.get("realtime_end")), "FRED realtime_end")
                ),
            )
        )
    return tuple(output)


def parse_fred_vintage_dates_json(text: str, *, series_id: str) -> tuple[FredVintageDate, ...]:
    if not isinstance(series_id, str) or not series_id.strip() or series_id != series_id.strip():
        raise ContractViolation("series_id must be canonical non-empty text")
    payload = _json_object(text, "FRED vintage dates")
    values = payload.get("vintage_dates")
    if not isinstance(values, list):
        raise ContractViolation("FRED vintage dates response must contain vintage_dates list")
    return tuple(
        FredVintageDate(series_id=series_id, vintage_date=SourceTimestamp.date_only(_date(value, "FRED vintage date")))
        for value in values
    )


def _json_object(text: str, label: str) -> dict[str, object]:
    if not isinstance(text, str) or not text.strip():
        raise ContractViolation(f"{label} JSON cannot be empty")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractViolation(f"{label} response must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ContractViolation(f"{label} response root must be an object")
    return payload


def _date(value: object, field: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{field} is required")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ContractViolation(f"{field} is not recognized") from exc
