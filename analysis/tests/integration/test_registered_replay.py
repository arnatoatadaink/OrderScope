from datetime import datetime, timedelta, timezone
import json

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.integration.replay import (
    ALPACA_NEWS_REPLAY_SOURCE,
    REPLAY_REGISTRY_VERSION,
    AlpacaNewsMetadataReplay,
    RegisteredReplayExecutor,
)

UTC = timezone.utc
START = datetime(2026, 9, 11, 22, 0, tzinfo=UTC)
END = datetime(2026, 9, 11, 23, 0, tzinfo=UTC)


class Transport:
    def __init__(self):
        self.calls = []

    def get_news(self, **kwargs):
        self.calls.append(kwargs)
        symbol = kwargs["symbol"]
        return {
            "news": [{
                "id": 100 if symbol == "AMD" else 200,
                "headline": f"{symbol} fixture",
                "author": "fixture",
                "created_at": "2026-09-11T22:30:00Z",
                "updated_at": "2026-09-11T22:31:00Z",
                "summary": "fixture summary",
                "url": f"https://example.test/{symbol.lower()}",
                "symbols": [symbol],
                "source": "fixture",
            }],
            "next_page_token": None,
        }


class Handler:
    def __init__(self):
        self.calls = []

    def replay(self, **kwargs):
        self.calls.append(kwargs)
        return len(kwargs["work_ids"])


def test_registry_rejects_unregistered_source():
    executor = RegisteredReplayExecutor({"registered": Handler()})
    with pytest.raises(ContractViolation, match="not registered"):
        executor.replay(source="unknown", start=START, end=END, work_ids=("w1",))


def test_registry_dispatches_only_bounded_unique_work_ids():
    handler = Handler()
    executor = RegisteredReplayExecutor({"registered": handler})
    assert executor.replay(source="registered", start=START, end=END, work_ids=("w1", "w2")) == 2
    assert handler.calls[0]["work_ids"] == ("w1", "w2")
    with pytest.raises(ContractViolation, match="unique"):
        executor.replay(source="registered", start=START, end=END, work_ids=("w1", "w1"))
    with pytest.raises(ContractViolation, match="31 days"):
        executor.replay(source="registered", start=START - timedelta(days=32), end=END, work_ids=("w1",))


def test_alpaca_news_replay_is_metadata_only_and_writes_bounded_receipt(tmp_path):
    transport = Transport()
    handler = AlpacaNewsMetadataReplay(
        transport=transport,
        data_root=tmp_path,
        clock=lambda: datetime(2026, 9, 12, 0, 0, tzinfo=UTC),
    )
    executor = RegisteredReplayExecutor({ALPACA_NEWS_REPLAY_SOURCE: handler})

    assert executor.replay(
        source=ALPACA_NEWS_REPLAY_SOURCE,
        start=START,
        end=END,
        work_ids=("retry-1",),
    ) == 1
    assert [call["symbol"] for call in transport.calls] == ["AMD", "NVDA"]
    assert all(call["include_content"] is False for call in transport.calls)

    receipts = list((tmp_path / "operator" / "replays").glob("*.json"))
    assert len(receipts) == 1
    payload = json.loads(receipts[0].read_text(encoding="utf-8"))
    assert payload["registry_version"] == REPLAY_REGISTRY_VERSION
    assert payload["source"] == ALPACA_NEWS_REPLAY_SOURCE
    assert payload["work_ids"] == ["retry-1"]
    assert payload["item_count"] == 2
    serialized = json.dumps(payload)
    assert "body" not in serialized
    assert "api_key" not in serialized
