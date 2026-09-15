from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

from orderscope_local.contracts import (
    ContentHash,
    Evidence,
    EvidenceKind,
    EvidenceQuality,
    Fact,
    FactAssertionKind,
    Provenance,
    RetentionClass,
    SourceReference,
    SourceTimestamp,
)
from orderscope_local.integration import (
    MarketTimelineBar,
    TimelineSourceKind,
    query_unified_timeline,
    read_market_timeline_bars,
)
from orderscope_local.market_import import D1ExportManifest, generate_fixture_canonical_bars


UTC = timezone.utc
BASE = datetime(2026, 9, 9, 13, 30, tzinfo=UTC)


def _fact(*, record_id: str, fact_type: str, available_at: datetime, accepted_at: datetime, event_time=None):
    evidence_id = f"evidence-{record_id}"
    provenance = Provenance(
        source_ref=SourceReference(f"https://example.test/{record_id}"),
        content_hash=ContentHash("1" * 64),
        available_at=available_at,
        retrieved_at=available_at,
        accepted_at=accepted_at,
        event_time=event_time,
    )
    fact = Fact(
        record_id=record_id,
        schema_version="fixture-v1",
        subject_ref="AMD",
        accepted_at=accepted_at,
        created_at=accepted_at,
        provenance=provenance,
        fact_type=fact_type,
        value="fixture",
        assertion_kind=FactAssertionKind.OBSERVATION,
        evidence_record_ids=(evidence_id,),
    )
    evidence = Evidence(
        record_id=evidence_id,
        schema_version="fixture-v1",
        subject_ref="AMD",
        accepted_at=accepted_at,
        created_at=accepted_at,
        provenance=provenance,
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(record_id,),
        locator=f"https://example.test/{record_id}",
        quality_class=EvidenceQuality.TIER_1_OFFICIAL,
        retention_class=RetentionClass.DURABLE_METADATA,
    )
    return fact, evidence


def _artifact() -> bytes:
    return (
        "CREATE TABLE bars (\n"
        "symbol TEXT NOT NULL,\n"
        "bar_time TEXT NOT NULL,\n"
        "open TEXT NOT NULL,\n"
        "high TEXT NOT NULL,\n"
        "low TEXT NOT NULL,\n"
        "close TEXT NOT NULL,\n"
        "volume INTEGER NOT NULL,\n"
        "receipt_time TEXT NOT NULL\n"
        ");\n"
        "INSERT INTO bars VALUES\n"
        f"('AMD','{BASE.isoformat()}','10','11','9','10.5',100,'{(BASE + timedelta(seconds=2)).isoformat()}'),\n"
        f"('AMD','{(BASE + timedelta(minutes=1)).isoformat()}','10.5','11.5','10','11',120,'{(BASE + timedelta(minutes=1, seconds=2)).isoformat()}');\n"
    ).encode()


def _market_bars(tmp_path: Path):
    artifact = _artifact()
    manifest = D1ExportManifest(
        source_environment="fixture",
        source_revision="fixture-v1",
        window_start=BASE,
        window_end=BASE + timedelta(minutes=5),
        table_name="bars",
        row_count=2,
        byte_size=len(artifact),
        sha256=sha256(artifact).hexdigest(),
    )
    dataset = generate_fixture_canonical_bars(manifest=manifest, artifact=artifact, dataset_root=tmp_path)
    return read_market_timeline_bars(dataset=dataset, dataset_root=tmp_path)


def test_timeline_orders_by_information_availability_not_event_time(tmp_path: Path) -> None:
    filing, _ = _fact(
        record_id="fact-filing",
        fact_type="filing.detected",
        available_at=BASE + timedelta(minutes=3),
        accepted_at=BASE + timedelta(minutes=4),
        event_time=SourceTimestamp.at(BASE - timedelta(days=1)),
    )
    news, _ = _fact(
        record_id="fact-news",
        fact_type="news.event.contract",
        available_at=BASE + timedelta(minutes=2),
        accepted_at=BASE + timedelta(minutes=2, seconds=30),
        event_time=SourceTimestamp.at(BASE + timedelta(minutes=10)),
    )

    items = query_unified_timeline(
        facts=(filing, news),
        market_bars=_market_bars(tmp_path),
        as_of=BASE + timedelta(minutes=5),
    )

    assert [item.source_kind for item in items] == [
        TimelineSourceKind.MARKET,
        TimelineSourceKind.MARKET,
        TimelineSourceKind.NEWS,
        TimelineSourceKind.FILING,
    ]
    assert items[2].event_time == BASE + timedelta(minutes=10)


def test_as_of_excludes_future_available_or_future_accepted_facts(tmp_path: Path) -> None:
    visible, _ = _fact(
        record_id="fact-visible",
        fact_type="earnings.revenue",
        available_at=BASE,
        accepted_at=BASE + timedelta(seconds=10),
    )
    future_available, _ = _fact(
        record_id="fact-future-available",
        fact_type="official.policy",
        available_at=BASE + timedelta(minutes=5),
        accepted_at=BASE + timedelta(minutes=5),
    )
    future_accepted, _ = _fact(
        record_id="fact-future-accepted",
        fact_type="news.event.contract",
        available_at=BASE,
        accepted_at=BASE + timedelta(minutes=5),
    )

    items = query_unified_timeline(
        facts=(visible, future_available, future_accepted),
        market_bars=(),
        as_of=BASE + timedelta(minutes=1),
    )
    assert [item.item_id for item in items] == ["fact-visible"]


def test_date_only_event_time_is_not_fabricated_into_instant() -> None:
    fact, _ = _fact(
        record_id="fact-date-only",
        fact_type="official.statement",
        available_at=BASE,
        accepted_at=BASE,
        event_time=SourceTimestamp.date_only(BASE.date()),
    )
    item = query_unified_timeline(facts=(fact,), market_bars=(), as_of=BASE)[0]
    assert item.event_time is None


def test_fact_source_kinds_are_classified_without_changing_fact() -> None:
    cases = (
        ("filing.detected", TimelineSourceKind.FILING),
        ("earnings.revenue", TimelineSourceKind.EARNINGS),
        ("news.event.contract", TimelineSourceKind.NEWS),
        ("official.statement", TimelineSourceKind.OFFICIAL),
        ("custom.other", TimelineSourceKind.OTHER_FACT),
    )
    facts = tuple(
        _fact(record_id=f"fact-{index}", fact_type=fact_type, available_at=BASE, accepted_at=BASE)[0]
        for index, (fact_type, _) in enumerate(cases)
    )
    items = query_unified_timeline(facts=facts, market_bars=(), as_of=BASE)
    by_id = {item.item_id: item for item in items}
    for index, (_, expected) in enumerate(cases):
        assert by_id[f"fact-{index}"].source_kind is expected


def test_market_bars_use_receipt_time_as_availability(tmp_path: Path) -> None:
    bars = _market_bars(tmp_path)
    items = query_unified_timeline(facts=(), market_bars=bars, as_of=BASE + timedelta(seconds=30))
    assert len(items) == 1
    assert items[0].available_at == BASE + timedelta(seconds=2)
    assert items[0].event_time == BASE


def test_tie_break_order_is_deterministic() -> None:
    first, _ = _fact(record_id="fact-a", fact_type="news.event.contract", available_at=BASE, accepted_at=BASE)
    second, _ = _fact(record_id="fact-b", fact_type="news.event.contract", available_at=BASE, accepted_at=BASE)
    assert query_unified_timeline(facts=(second, first), market_bars=(), as_of=BASE) == query_unified_timeline(
        facts=(first, second), market_bars=(), as_of=BASE
    )


def test_market_reader_preserves_dataset_lineage(tmp_path: Path) -> None:
    bars = _market_bars(tmp_path)
    assert len(bars) == 2
    assert all(bar.source_manifest_id.startswith("d1-export-") for bar in bars)
    assert all(len(bar.source_artifact_sha256) == 64 for bar in bars)
