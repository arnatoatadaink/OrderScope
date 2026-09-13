"""Bounded Alpaca daily-bar collector for A0-002 stock/ETF/BTC inputs.

The transport reuses the accepted Alpaca credential boundary. It emits
SeriesObservation values only; it does not evaluate hypotheses.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from orderscope_local.config import ALPACA_API_KEY_ENV, ALPACA_API_SECRET_ENV, read_required_secret
from orderscope_local.contracts import ContractViolation
from .validation import SeriesMeasure, SeriesObservation, SeriesRole


STOCK_BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
CRYPTO_BARS_URL = "https://data.alpaca.markets/v1beta3/crypto/us/bars"
_ET = ZoneInfo("America/New_York")
_UTC = timezone.utc


class AlpacaDailyRequestFailure(RuntimeError):
    def __init__(self, category: str, retryable: bool) -> None:
        self.category = category
        self.retryable = retryable
        super().__init__(category)


@dataclass(frozen=True, slots=True)
class DailySeriesBinding:
    role: SeriesRole
    symbol: str
    source_ref: str
    is_crypto: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.role, SeriesRole):
            raise ContractViolation("role must be SeriesRole")
        if not isinstance(self.symbol, str) or not self.symbol.strip() or self.symbol != self.symbol.strip():
            raise ContractViolation("symbol must be canonical non-empty text")
        if not isinstance(self.source_ref, str) or not self.source_ref.strip():
            raise ContractViolation("source_ref must be non-empty text")


DEFAULT_A0_ALPACA_BINDINGS = (
    DailySeriesBinding(role=SeriesRole.CBRS, symbol="CBRS", source_ref="alpaca:stock:CBRS"),
    DailySeriesBinding(role=SeriesRole.NVDA, symbol="NVDA", source_ref="alpaca:stock:NVDA"),
    DailySeriesBinding(role=SeriesRole.US_MARKET, symbol="QQQ", source_ref="alpaca:stock:QQQ"),
    DailySeriesBinding(role=SeriesRole.AI_SEMICONDUCTOR_PROXY, symbol="SOXX", source_ref="alpaca:stock:SOXX"),
    DailySeriesBinding(role=SeriesRole.BTC, symbol="BTC/USD", source_ref="alpaca:crypto:BTC-USD", is_crypto=True),
)


class AlpacaDailyBarsTransport:
    def __init__(self, *, environ, timeout_seconds: float = 20.0) -> None:
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or not 0 < timeout_seconds <= 120:
            raise ContractViolation("Alpaca timeout must be between 0 and 120 seconds")
        self._api_key = read_required_secret(environ, ALPACA_API_KEY_ENV)
        self._api_secret = read_required_secret(environ, ALPACA_API_SECRET_ENV)
        self._timeout = float(timeout_seconds)

    def get_daily_bars(
        self,
        *,
        symbols: tuple[str, ...],
        start: date,
        end_exclusive: date,
        crypto: bool,
        page_token: str | None = None,
        limit: int = 1000,
    ) -> dict[str, object]:
        if not symbols or len(symbols) != len(set(symbols)):
            raise ContractViolation("symbols must be a non-empty unique tuple")
        if start >= end_exclusive:
            raise ContractViolation("daily bar window must be non-empty")
        if not 1 <= limit <= 10000:
            raise ContractViolation("limit must be between 1 and 10000")
        query = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "start": start.isoformat(),
            "end": (end_exclusive - timedelta(days=1)).isoformat(),
            "limit": str(limit),
        }
        if not crypto:
            query["adjustment"] = "raw"
            query["feed"] = "iex"
        if page_token is not None:
            query["page_token"] = page_token
        url = CRYPTO_BARS_URL if crypto else STOCK_BARS_URL
        request = Request(
            f"{url}?{urlencode(query)}",
            headers={
                "APCA-API-KEY-ID": self._api_key,
                "APCA-API-SECRET-KEY": self._api_secret,
                "Accept": "application/json",
                "User-Agent": "OrderScope-local/0.1",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            if exc.code == 429:
                raise AlpacaDailyRequestFailure("rate_limited", True) from None
            if exc.code in {401, 403}:
                raise AlpacaDailyRequestFailure("authentication_or_access", False) from None
            if 500 <= exc.code <= 599:
                raise AlpacaDailyRequestFailure("upstream_error", True) from None
            raise AlpacaDailyRequestFailure("provider_request_error", False) from None
        except (URLError, TimeoutError, OSError):
            raise AlpacaDailyRequestFailure("transport_error", True) from None
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise AlpacaDailyRequestFailure("invalid_response", False) from None
        if not isinstance(payload, dict):
            raise AlpacaDailyRequestFailure("invalid_response", False)
        return payload


def collect_a0_alpaca_daily(
    *,
    transport: AlpacaDailyBarsTransport,
    start: date,
    end_exclusive: date,
    bindings: tuple[DailySeriesBinding, ...] = DEFAULT_A0_ALPACA_BINDINGS,
) -> tuple[SeriesObservation, ...]:
    stock = tuple(binding for binding in bindings if not binding.is_crypto)
    crypto = tuple(binding for binding in bindings if binding.is_crypto)
    observations: list[SeriesObservation] = []
    if stock:
        observations.extend(_collect_group(transport=transport, bindings=stock, start=start, end_exclusive=end_exclusive, crypto=False))
    if crypto:
        observations.extend(_collect_group(transport=transport, bindings=crypto, start=start, end_exclusive=end_exclusive, crypto=True))
    return tuple(sorted(observations, key=lambda item: (item.analysis_date, item.role.value, item.measure.value)))


def _collect_group(*, transport, bindings, start: date, end_exclusive: date, crypto: bool) -> list[SeriesObservation]:
    by_symbol = {binding.symbol: binding for binding in bindings}
    page_token: str | None = None
    out: list[SeriesObservation] = []
    while True:
        payload = transport.get_daily_bars(
            symbols=tuple(by_symbol),
            start=start,
            end_exclusive=end_exclusive,
            crypto=crypto,
            page_token=page_token,
        )
        bars = payload.get("bars")
        if not isinstance(bars, dict):
            raise ContractViolation("Alpaca daily response must contain bars object")
        for symbol, rows in bars.items():
            binding = by_symbol.get(symbol)
            if binding is None:
                raise ContractViolation("Alpaca response returned an unrequested symbol")
            if not isinstance(rows, list):
                raise ContractViolation("Alpaca symbol bars must be a list")
            for row in rows:
                out.extend(_normalize_bar(binding=binding, row=row, crypto=crypto))
        token = payload.get("next_page_token")
        if token is None:
            break
        if not isinstance(token, str) or not token:
            raise ContractViolation("next_page_token must be null or non-empty text")
        page_token = token
    return out


def _normalize_bar(*, binding: DailySeriesBinding, row: object, crypto: bool) -> tuple[SeriesObservation, SeriesObservation]:
    if not isinstance(row, dict):
        raise ContractViolation("Alpaca bar must be an object")
    timestamp = row.get("t")
    close = row.get("c")
    volume = row.get("v")
    if not isinstance(timestamp, str):
        raise ContractViolation("Alpaca bar timestamp must be text")
    try:
        observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractViolation("Alpaca bar timestamp must be ISO-8601") from exc
    if observed_at.tzinfo is None or observed_at.utcoffset() != timedelta(0):
        raise ContractViolation("Alpaca bar timestamp must be UTC")
    if isinstance(close, bool) or not isinstance(close, (int, float)):
        raise ContractViolation("Alpaca close must be numeric")
    if isinstance(volume, bool) or not isinstance(volume, (int, float)):
        raise ContractViolation("Alpaca volume must be numeric")
    analysis_date = observed_at.date()
    available_at = _daily_available_at(analysis_date=analysis_date, crypto=crypto)
    return (
        SeriesObservation(
            role=binding.role,
            measure=SeriesMeasure.PRICE,
            analysis_date=analysis_date,
            observed_at=observed_at,
            available_at=available_at,
            value=float(close),
            source_ref=binding.source_ref,
        ),
        SeriesObservation(
            role=binding.role,
            measure=SeriesMeasure.VOLUME,
            analysis_date=analysis_date,
            observed_at=observed_at,
            available_at=available_at,
            value=float(volume),
            source_ref=binding.source_ref,
        ),
    )


def _daily_available_at(*, analysis_date: date, crypto: bool) -> datetime:
    if crypto:
        return datetime.combine(analysis_date + timedelta(days=1), time.min, tzinfo=_UTC)
    local_close = datetime.combine(analysis_date, time(16, 0), tzinfo=_ET)
    return local_close.astimezone(_UTC)
