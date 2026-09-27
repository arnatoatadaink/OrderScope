"""Official macro inputs for the A0-002 validation case.

This is a validation-only collector for the reviewed 2026-08-26..2026-09-04
window. It keeps official source semantics and emits source-neutral
SeriesObservation values; it does not evaluate hypotheses.
"""

from __future__ import annotations

from csv import reader
from datetime import date, datetime, time, timedelta, timezone
from html import unescape
import io
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from orderscope_local.contracts import ContractViolation
from .validation import SeriesMeasure, SeriesObservation, SeriesRole


FRED_DGS10_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
MOF_JGB_URL = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv"
BOJ_USDJPY_URL = "https://www.stat-search.boj.or.jp/ssi/mtshtml/fm08_d_1.html"

_UTC = timezone.utc
_TOKYO = ZoneInfo("Asia/Tokyo")


class OfficialMacroRequestFailure(RuntimeError):
    def __init__(self, category: str, retryable: bool) -> None:
        self.category = category
        self.retryable = retryable
        super().__init__(category)


def collect_official_macro(*, start: date, end_exclusive: date, timeout_seconds: float = 20.0) -> tuple[SeriesObservation, ...]:
    if start >= end_exclusive:
        raise ContractViolation("official macro window must be non-empty")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or not 0 < timeout_seconds <= 120:
        raise ContractViolation("official macro timeout must be between 0 and 120 seconds")

    dgs10 = _get_text(
        FRED_DGS10_URL,
        query={"id": "DGS10", "cosd": start.isoformat(), "coed": (end_exclusive - timedelta(days=1)).isoformat()},
        timeout=float(timeout_seconds),
    )
    jgb = _get_text(MOF_JGB_URL, timeout=float(timeout_seconds), encoding="cp932")
    # BOJ's legacy time-series HTML may be served in a Shift_JIS/Windows-31J
    # encoding. Decode with cp932 first while retaining the generic UTF-8
    # fallback inside _get_text.
    boj = _get_text(BOJ_USDJPY_URL, timeout=float(timeout_seconds), encoding="cp932")

    observations = [
        *parse_fred_dgs10_csv(dgs10, start=start, end_exclusive=end_exclusive),
        *parse_mof_jgb_csv(jgb, start=start, end_exclusive=end_exclusive),
        *parse_boj_usdjpy_html(boj, start=start, end_exclusive=end_exclusive),
    ]
    return tuple(sorted(observations, key=lambda item: (item.analysis_date, item.role.value, item.measure.value)))


def parse_fred_dgs10_csv(text: str, *, start: date, end_exclusive: date) -> tuple[SeriesObservation, ...]:
    rows = list(reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 2 or rows[0][0] not in {"DATE", "observation_date"}:
        raise ContractViolation("FRED DGS10 CSV header is not recognized")
    out: list[SeriesObservation] = []
    for row in rows[1:]:
        if len(row) < 2 or row[1] in {"", "."}:
            continue
        day = _date(row[0], "%Y-%m-%d", "FRED DGS10 date")
        if not start <= day < end_exclusive:
            continue
        value = _float(row[1], "FRED DGS10 value")
        observed_at = datetime.combine(day, time(23, 59), tzinfo=_UTC)
        available_at = datetime.combine(day + timedelta(days=1), time(23, 59), tzinfo=_UTC)
        out.append(
            SeriesObservation(
                role=SeriesRole.UST_10Y,
                measure=SeriesMeasure.YIELD,
                analysis_date=day,
                observed_at=observed_at,
                available_at=available_at,
                value=value,
                source_ref="fred:DGS10",
            )
        )
    return tuple(out)


def parse_mof_jgb_csv(text: str, *, start: date, end_exclusive: date) -> tuple[SeriesObservation, ...]:
    rows = list(reader(io.StringIO(text)))
    if not rows:
        raise ContractViolation("MOF JGB CSV is empty")
    header_index = None
    ten_year_index = None
    for index, row in enumerate(rows[:10]):
        normalized = [cell.strip().lower().replace(" ", "") for cell in row]
        if any(cell in {"date", "年月日"} for cell in normalized):
            header_index = index
            for column, cell in enumerate(normalized):
                if cell in {"10y", "10year", "10-year", "10年"} or "10-year" in cell or "10year" in cell:
                    ten_year_index = column
                    break
            break
    if header_index is None or ten_year_index is None:
        raise ContractViolation("MOF JGB CSV must expose Date and 10Y columns")

    out: list[SeriesObservation] = []
    for row in rows[header_index + 1 :]:
        if len(row) <= ten_year_index:
            continue
        raw_date = row[0].strip()
        raw_value = row[ten_year_index].strip()
        if not raw_date or not raw_value or raw_value in {"-", "NA", "N/A"}:
            continue
        day = _parse_mof_date(raw_date)
        if not start <= day < end_exclusive:
            continue
        value = _float(raw_value, "MOF JGB 10Y value")
        observed_at = datetime.combine(day, time(15, 0), tzinfo=_TOKYO).astimezone(_UTC)
        available_at = _next_business_day_0930_jst(day)
        out.append(
            SeriesObservation(
                role=SeriesRole.JGB_10Y,
                measure=SeriesMeasure.YIELD,
                analysis_date=day,
                observed_at=observed_at,
                available_at=available_at,
                value=value,
                source_ref="mof:jgb:constant-maturity:10y",
            )
        )
    return tuple(out)


def parse_boj_usdjpy_html(text: str, *, start: date, end_exclusive: date) -> tuple[SeriesObservation, ...]:
    plain = unescape(re.sub(r"<[^>]+>", " ", text))
    pattern = re.compile(r"(20\d{2}/\d{2}/\d{2})\s*[|\s]+(NA|[-+]?\d+(?:\.\d+)?)\s*[|\s]+(?:NA|ND|[-+]?\d+(?:\.\d+)?)")
    seen: set[date] = set()
    out: list[SeriesObservation] = []
    for match in pattern.finditer(plain):
        day = _date(match.group(1), "%Y/%m/%d", "BOJ USDJPY date")
        if day in seen or not start <= day < end_exclusive:
            continue
        seen.add(day)
        if match.group(2) == "NA":
            continue
        value = _float(match.group(2), "BOJ USDJPY value")
        observed_at = datetime.combine(day, time(17, 0), tzinfo=_TOKYO).astimezone(_UTC)
        available_at = datetime.combine(day, time(17, 50), tzinfo=_TOKYO).astimezone(_UTC)
        out.append(
            SeriesObservation(
                role=SeriesRole.USDJPY,
                measure=SeriesMeasure.FX_RATE,
                analysis_date=day,
                observed_at=observed_at,
                available_at=available_at,
                value=value,
                source_ref="boj:fxdaily:usdjpy:17h-mid",
            )
        )
    if not out:
        raise ContractViolation("BOJ USDJPY table contained no observations in requested window")
    return tuple(out)


def _get_text(url: str, *, timeout: float, query: dict[str, str] | None = None, encoding: str = "utf-8") -> str:
    if query:
        url = f"{url}?{urlencode(query)}"
    request = Request(url, headers={"Accept": "text/csv,text/html,*/*", "User-Agent": "OrderScope-local/0.1"}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        if exc.code == 429:
            raise OfficialMacroRequestFailure("rate_limited", True) from None
        if 500 <= exc.code <= 599:
            raise OfficialMacroRequestFailure("upstream_error", True) from None
        raise OfficialMacroRequestFailure("provider_request_error", False) from None
    except (URLError, TimeoutError, OSError):
        raise OfficialMacroRequestFailure("transport_error", True) from None

    candidates = [encoding]
    if encoding != "utf-8":
        candidates.append("utf-8")
    if "cp932" not in candidates:
        candidates.append("cp932")
    if "shift_jis" not in candidates:
        candidates.append("shift_jis")
    for candidate in candidates:
        try:
            return raw.decode(candidate)
        except UnicodeDecodeError:
            continue
    raise OfficialMacroRequestFailure("invalid_response", False) from None


def _next_business_day_0930_jst(day: date) -> datetime:
    candidate = day + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return datetime.combine(candidate, time(9, 30), tzinfo=_TOKYO).astimezone(_UTC)


def _parse_mof_date(value: str) -> date:
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ContractViolation("MOF JGB date is not recognized")


def _date(value: str, fmt: str, field: str) -> date:
    try:
        return datetime.strptime(value, fmt).date()
    except ValueError as exc:
        raise ContractViolation(f"{field} is invalid") from exc


def _float(value: str, field: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ContractViolation(f"{field} must be numeric") from exc
