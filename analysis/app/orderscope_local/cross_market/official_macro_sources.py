"""Official-direct macro source adapters beyond the A0-002 validation collector.

Source parsers emit raw normalized points only. They intentionally do not invent
provider availability, retrieval, or Fact Store acceptance timestamps.
"""

from __future__ import annotations

from csv import DictReader
from dataclasses import dataclass
from datetime import date, datetime
import io
from math import isfinite

from orderscope_local.contracts import (
    ContractViolation,
    MacroMarketRegion,
    MacroMarketSeriesKind,
    SourceTimestamp,
)


TREASURY_PAR_YIELD_SOURCE = "us-treasury:daily-par-yield-curve"
_TREASURY_REQUIRED_COLUMNS = {
    "2Y": ("2 YR", "2 Yr", "2 Yr."),
    "5Y": ("5 YR", "5 Yr", "5 Yr."),
    "10Y": ("10 YR", "10 Yr", "10 Yr."),
    "30Y": ("30 YR", "30 Yr", "30 Yr."),
}


@dataclass(frozen=True, kw_only=True, slots=True)
class OfficialMacroRawPoint:
    series_id: str
    series_kind: MacroMarketSeriesKind
    region: MacroMarketRegion
    value: float
    unit: str
    observed_at: SourceTimestamp
    source_ref: str
    tenor: str | None = None

    def __post_init__(self) -> None:
        for value, field in (
            (self.series_id, "series_id"),
            (self.unit, "unit"),
            (self.source_ref, "source_ref"),
        ):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ContractViolation(f"{field} must be canonical non-empty text")
        if not isinstance(self.series_kind, MacroMarketSeriesKind):
            raise ContractViolation("series_kind must be MacroMarketSeriesKind")
        if not isinstance(self.region, MacroMarketRegion):
            raise ContractViolation("region must be MacroMarketRegion")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not isfinite(float(self.value)):
            raise ContractViolation("value must be finite numeric data")
        if not isinstance(self.observed_at, SourceTimestamp):
            raise ContractViolation("observed_at must be SourceTimestamp")
        if self.tenor is not None and (not self.tenor.strip() or self.tenor != self.tenor.strip()):
            raise ContractViolation("tenor must be canonical non-empty text")


def parse_treasury_par_yield_csv(
    text: str,
    *,
    start: date | None = None,
    end_exclusive: date | None = None,
) -> tuple[OfficialMacroRawPoint, ...]:
    """Parse official Daily Treasury Par Yield Curve CSV into 2/5/10/30Y points."""
    if (start is None) != (end_exclusive is None):
        raise ContractViolation("Treasury window requires both start and end_exclusive")
    if start is not None and start >= end_exclusive:
        raise ContractViolation("Treasury window must be non-empty")
    if not isinstance(text, str) or not text.strip():
        raise ContractViolation("Treasury CSV cannot be empty")

    reader = DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ContractViolation("Treasury CSV header is missing")

    date_column = _resolve_column(reader.fieldnames, ("Date", "DATE"), "Date")
    tenor_columns = {
        tenor: _resolve_column(reader.fieldnames, aliases, tenor)
        for tenor, aliases in _TREASURY_REQUIRED_COLUMNS.items()
    }

    points: list[OfficialMacroRawPoint] = []
    for row in reader:
        raw_date = (row.get(date_column) or "").strip()
        if not raw_date:
            continue
        day = _parse_treasury_date(raw_date)
        if start is not None and not start <= day < end_exclusive:
            continue
        for tenor, column in tenor_columns.items():
            raw_value = (row.get(column) or "").strip()
            if raw_value.upper() in {"", "N/A", "NA"}:
                continue
            try:
                value = float(raw_value)
            except ValueError as exc:
                raise ContractViolation(f"Treasury {tenor} yield must be numeric") from exc
            if not isfinite(value):
                raise ContractViolation(f"Treasury {tenor} yield must be finite")
            points.append(
                OfficialMacroRawPoint(
                    series_id=f"US_TREASURY_{tenor}",
                    series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
                    region=MacroMarketRegion.US,
                    value=value,
                    unit="percent",
                    observed_at=SourceTimestamp.date_only(day),
                    source_ref=TREASURY_PAR_YIELD_SOURCE,
                    tenor=tenor,
                )
            )
    return tuple(points)


def _resolve_column(fieldnames: list[str], aliases: tuple[str, ...], label: str) -> str:
    normalized = {name.strip().casefold(): name for name in fieldnames if isinstance(name, str)}
    for alias in aliases:
        actual = normalized.get(alias.casefold())
        if actual is not None:
            return actual
    raise ContractViolation(f"Treasury CSV missing required {label} column")


def _parse_treasury_date(value: str) -> date:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ContractViolation("Treasury Date is not recognized")
