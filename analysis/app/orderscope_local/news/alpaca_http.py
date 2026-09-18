"""Concrete bounded HTTP transport for the accepted Alpaca News metadata adapter."""

from __future__ import annotations

from datetime import timedelta
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from orderscope_local.contracts import ContractViolation
from orderscope_local.config import (
    ALPACA_API_KEY_ENV,
    ALPACA_API_SECRET_ENV,
    read_required_secret,
)
from .alpaca import AlpacaNewsRequestFailure


ALPACA_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"


class AlpacaNewsHttpTransport:
    """Small stdlib HTTP boundary that never requests article body content."""

    def __init__(self, *, environ, timeout_seconds: float = 20.0) -> None:
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0 or timeout_seconds > 120:
            raise ContractViolation("Alpaca News timeout must be between 0 and 120 seconds")
        self._api_key = read_required_secret(environ, ALPACA_API_KEY_ENV)
        self._api_secret = read_required_secret(environ, ALPACA_API_SECRET_ENV)
        self._timeout_seconds = float(timeout_seconds)

    def get_news(
        self,
        *,
        symbol: str,
        start: str,
        end: str,
        limit: int,
        page_token: str | None,
        include_content: bool,
        sort: str,
    ):
        if include_content:
            raise ContractViolation("N1-006 News candidate acquisition must not request article content")
        query = {
            "symbols": symbol,
            "start": start,
            "end": end,
            "limit": str(limit),
            "include_content": "false",
            "sort": sort,
        }
        if page_token is not None:
            query["page_token"] = page_token
        request = Request(
            f"{ALPACA_NEWS_URL}?{urlencode(query)}",
            headers={
                "APCA-API-KEY-ID": self._api_key,
                "APCA-API-SECRET-KEY": self._api_secret,
                "Accept": "application/json",
                "User-Agent": "OrderScope-local/0.1",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            raise _http_failure(exc) from None
        except (URLError, TimeoutError, OSError):
            raise AlpacaNewsRequestFailure("transport_error", True) from None

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise AlpacaNewsRequestFailure("invalid_response", False) from None
        if not isinstance(payload, dict):
            raise AlpacaNewsRequestFailure("invalid_response", False)
        return payload


def _http_failure(exc: HTTPError) -> AlpacaNewsRequestFailure:
    if exc.code == 429:
        return AlpacaNewsRequestFailure("rate_limited", True, _retry_after(exc))
    if exc.code in {401, 403}:
        return AlpacaNewsRequestFailure("authentication_or_access", False)
    if 500 <= exc.code <= 599:
        return AlpacaNewsRequestFailure("upstream_error", True)
    return AlpacaNewsRequestFailure("provider_request_error", False)


def _retry_after(exc: HTTPError) -> timedelta | None:
    value = exc.headers.get("Retry-After") if exc.headers is not None else None
    if value is None:
        return None
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return None
    if seconds < 0:
        return None
    return timedelta(seconds=min(seconds, 24 * 60 * 60))
