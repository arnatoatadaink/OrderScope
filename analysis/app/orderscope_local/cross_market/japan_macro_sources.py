"""Official Japanese macro source adapters for UWBS-034."""

from __future__ import annotations

from csv import DictReader
from dataclasses import dataclass
from datetime import date, datetime
import io
import json
from math import isfinite

from orderscope_local.contracts import (
    ContractViolation,
    MacroMarketRegion,
    MacroMarketSeriesKind,
    SourceTimestamp,
)

BOJ_USDJPY_SOURCE = "boj:fm08:fxerd04"
MOF_JGB_SOURCE = "mof:jgb:constant-maturity"


@dataclass(frozen=True, kw_only=True, slots=True)
class JapanMacroRawPoint:
    series_id: str
    series_kind: MacroMarketSeriesKind
    region: MacroMarketRegion
    value: float
    unit: str
    observed_at: SourceTimestamp
    source_ref: str
    tenor: str | None = None
    last_update: date | None = None


def parse_boj_usdjpy_json(text: str) -> tuple[JapanMacroRawPoint, ...]:
    """Parse BOJ getDataCode JSON for FM08 FXERD04 daily USD/JPY 17:00 series."""
    if not isinstance(text, str) or not text.strip():
        raise ContractViolation("BOJ JSON cannot be empty")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractViolation("BOJ response must be valid JSON") from exc
    if not isinstance(payload, dict) or payload.get("STATUS") != 200:
        raise ContractViolation("BOJ response must be a successful API result")
    resultset = payload.get("RESULTSET")
    if not isinstance(resultset, list):
        raise ContractViolation("BOJ response must contain RESULTSET list")

    matches = [row for row in resultset if isinstance(row, dict) and row.get("SERIES_CODE") == "FXERD04"]
    if len(matches) != 1:
        raise ContractViolation("BOJ response must contain exactly one FXERD04 series")
    row = matches[0]
    if row.get("FREQUENCY") != "DAILY":
        raise ContractViolation("BOJ FXERD04 must be DAILY")
    unit = row.get("UNIT")
    if not isinstance(unit, str) or not unit.strip():
        raise ContractViolation("BOJ FXERD04 unit is missing")
    values_block = row.get("VALUES")
    if not isinstance(values_block, dict):
        raise ContractViolation("BOJ FXERD04 VALUES block is missing")
    dates = values_block.get("SURVEY_DATES")
    values = values_block.get("VALUES")
    if not isinstance(dates, list) or not isinstance(values, list) or len(dates) != len(values):
        raise ContractViolation("BOJ FXERD04 dates/values are malformed")
    last_update = _parse_compact_date(row.get("LAST_UPDATE"), "BOJ LAST_UPDATE")

    points: list[JapanMacroRawPoint] = []
    for raw_date, raw_value in zip(dates, values, strict=True):
        if raw_value is None:
            continue
        day = _parse_compact_date(raw_date, "BOJ survey date")
        value = _finite_float(raw_value, "BOJ FXERD04 value")
        points.append(
            JapanMacroRawPoint(
                series_id="USDJPY_BOJ_17H",
                series_kind=MacroMarketSeriesKind.FX_RATE,
                region=MacroMarketRegion.CROSS_MARKET,
                value=value,
                unit=unit,
                observed_at=SourceTimestamp.date_only(day),
                source_ref=BOJ_USDJPY_SOURCE,
                last_update=last_update,
            )
        )
    return tuple(points)


def parse_mof_jgb_csv(text: str) -> tuple[JapanMacroRawPoint, ...]:
    """Parse MOF constant-maturity JGB CSV into 2Y/5Y/10Y/30Y points."""
    if not isinstance(text, str) or not text.strip():
        raise ContractViolation("MOF JGB CSV cannot be empty")
    reader = DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ContractViolation("MOF JGB CSV header is missing")
    date_col = _resolve_column(reader.fieldnames, ("Date", "DATE", "年月日"), "Date")
    columns = {
        "2Y": _resolve_column(reader.fieldnames, ("2Y", "2 Year", "2-Year", "2年"), "2Y"),
        "5Y": _resolve_column(reader.fieldnames, ("5Y", "5 Year", "5-Year", "5年"), "5Y"),
        "10Y": _resolve_column(reader.fieldnames, ("10Y", "10 Year", "10-Year", "10年"), "10Y"),
        "30Y": _resolve_column(reader.fieldnames, ("30Y", "30 Year", "30-Year", "30年"), "30Y"),
    }

    points: list[JapanMacroRawPoint] = []
    for row in reader:
        raw_date = (row.get(date_col) or "").strip()
        if not raw_date:
            continue
        day = _parse_mof_date(raw_date)
        for tenor, column in columns.items():
            raw = (row.get(column) or "").strip()
            if raw.upper() in {"", "NA", "N/A", "-"}:
                continue
            value = _finite_float(raw, f"MOF {tenor} value")
            points.append(
                JapanMacroRawPoint(
                    series_id=f"JP_JGB_{tenor}",
                    series_kind=MacroMarketSeriesKind.SOVEREIGN_YIELD,
                    region=MacroMarketRegion.JP,
                    value=value,
                    unit="percent",
                    observed_at=SourceTimestamp.date_only(day),
                    source_ref=f"{MOF_JGB_SOURCE}:{tenor.lower()}",
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
    raise ContractViolation(f"MOF JGB CSV missing required {label} column")


def _parse_compact_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise ContractViolation(f"{field} is missing")
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError as exc:
        raise ContractViolation(f"{field} is invalid") from exc


def _parse_mof_date(value: str) -> date:
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ContractViolation("MOF JGB date is not recognized")


def _finite_float(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ContractViolation(f"{field} must be numeric")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractViolation(f"{field} must be numeric") from exc
    if not isfinite(parsed):
        raise ContractViolation(f"{field} must be finite")
    return parsed
