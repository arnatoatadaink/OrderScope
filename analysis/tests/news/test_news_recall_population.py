from __future__ import annotations

from datetime import datetime, timezone
import json
from urllib.parse import parse_qs, urlparse

import pytest

from orderscope_local.config import ALPACA_API_KEY_ENV, ALPACA_API_SECRET_ENV
from orderscope_local.contracts import ContractViolation
from orderscope_local.news import (
    AlpacaNewsHttpTransport,
    collect_news_recall_candidates,
    write_news_recall_candidates,
)


UTC = timezone.utc
START = datetime(2026, 8, 11, tzinfo=UTC)
END = datetime(2026, 9, 10, tzinfo=UTC)


class _Response:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._payload


def test_http_transport_uses_metadata_only_alpaca_news_request(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response({"news": [], "next_page_token": None})

    monkeypatch.setattr("orderscope_local.news.alpaca_http.urlopen", fake_urlopen)
    transport = AlpacaNewsHttpTransport(
        environ={ALPACA_API_KEY_ENV: "key", ALPACA_API_SECRET_ENV: "secret"},
    )
    result = transport.get_news(
        symbol="AMD",
        start=START.isoformat(),
        end=END.isoformat(),
        limit=50,
        page_token=None,
        include_content=False,
        sort="asc",
    )
    assert result["news"] == []
    request = captured["request"]
    query = parse_qs(urlparse(request.full_url).query)
    assert query["symbols"] == ["AMD"]
    assert query["include_content"] == ["false"]
    assert query["limit"] == ["50"]
    assert request.get_header("Apca-api-key-id") == "key"
    assert request.get_header("Apca-api-secret-key") == "secret"


def test_http_transport_rejects_body_request() -> None:
    transport = AlpacaNewsHttpTransport(
        environ={ALPACA_API_KEY_ENV: "key", ALPACA_API_SECRET_ENV: "secret"},
    )
    with pytest.raises(ContractViolation, match="must not request article content"):
        transport.get_news(
            symbol="AMD", start=START.isoformat(), end=END.isoformat(), limit=50,
            page_token=None, include_content=True, sort="asc",
        )


class _FakeTransport:
    def __init__(self):
        self.calls = []

    def get_news(self, **kwargs):
        self.calls.append(kwargs)
        symbol = kwargs["symbol"]
        common = {
            "id": 100,
            "headline": "Shared semiconductor story",
            "source": "fixture-wire",
            "url": "https://example.test/shared",
            "created_at": "2026-08-20T12:00:00Z",
            "updated_at": "2026-08-20T12:00:00Z",
            "author": "Fixture",
            "summary": "Metadata only",
            "symbols": ["AMD", "NVDA"],
        }
        unique = {
            "id": 101 if symbol == "AMD" else 102,
            "headline": f"{symbol} unique story",
            "source": "fixture-wire",
            "url": f"https://example.test/{symbol.lower()}",
            "created_at": "2026-08-21T12:00:00Z",
            "updated_at": "2026-08-21T12:00:00Z",
            "author": "Fixture",
            "summary": "Metadata only",
            "symbols": [symbol],
        }
        return {"news": [common, unique], "next_page_token": None}


def test_candidate_collection_deduplicates_provider_article_and_preserves_query_symbols() -> None:
    transport = _FakeTransport()
    candidates = collect_news_recall_candidates(
        transport=transport,
        window_start=START,
        window_end=END,
    )
    assert len(candidates) == 3
    shared = next(item for item in candidates if item.provider_article_id == "100")
    assert shared.query_symbols == ("AMD", "NVDA")
    assert shared.provider_symbols == ("AMD", "NVDA")
    assert all(call["include_content"] is False for call in transport.calls)


def test_candidate_file_is_forced_under_data_root_and_contains_no_credentials(tmp_path) -> None:
    candidates = collect_news_recall_candidates(
        transport=_FakeTransport(), window_start=START, window_end=END
    )
    path = write_news_recall_candidates(
        data_root=tmp_path,
        filename="candidates.json",
        window_start=START,
        window_end=END,
        candidates=candidates,
    )
    assert path == tmp_path / "benchmarks" / "n1-006" / "candidates.json"
    text = path.read_text()
    assert "Shared semiconductor story" in text
    assert "api_key" not in text.casefold()
    assert "secret" not in text.casefold()


def test_candidate_filename_cannot_escape_data_root(tmp_path) -> None:
    with pytest.raises(ContractViolation, match="simple .json filename"):
        write_news_recall_candidates(
            data_root=tmp_path,
            filename="../escape.json",
            window_start=START,
            window_end=END,
            candidates=(),
        )


def test_candidate_window_requires_30_to_93_days() -> None:
    with pytest.raises(ContractViolation, match="30 through 93"):
        collect_news_recall_candidates(
            transport=_FakeTransport(),
            window_start=datetime(2026, 9, 1, tzinfo=UTC),
            window_end=END,
        )
