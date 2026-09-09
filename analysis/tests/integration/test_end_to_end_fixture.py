from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
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
    TemporaryContent,
    TemporaryContentState,
    validate_fact_store,
)
from orderscope_local.integration import (
    SchedulerJob,
    TimelineSourceKind,
    query_unified_timeline,
    run_scheduler,
)
from orderscope_local.news import delete_due_content

UTC = timezone.utc
BASE = datetime(2026, 9, 10, 0, 0, tzinfo=UTC)
SUBJECT = "us-sec-0000002488-common"

FIXTURE_INPUTS = (
    {
        "kind": "filing",
        "source": "https://www.sec.gov/Archives/edgar/data/2488/fixture-10q.htm",
        "fact_type": "filing.detected",
        "value": {"form": "10-Q", "accession": "fixture-10q"},
        "available_offset": 1,
    },
    {
        "kind": "ir",
        "source": "https://ir.amd.com/fixture-earnings",
        "fact_type": "earnings.revenue",
        "value": {"currency": "USD", "revenue": "fixture-value"},
        "available_offset": 2,
    },
    {
        "kind": "news",
        "source": "https://example.test/news/fixture-contract",
        "fact_type": "news.event.contract",
        "value": {"headline": "AMD wins government contract for accelerator systems"},
        "available_offset": 3,
    },
    {
        "kind": "official",
        "source": "https://www.commerce.gov/fixture-semiconductor-update",
        "fact_type": "official.statement",
        "value": {"statement": "fixture semiconductor policy update"},
        "available_offset": 4,
    },
)


@dataclass
class ReplayState:
    facts: list[Fact]
    evidence: list[Evidence]
    deleted_content: TemporaryContent | None = None
    timeline_ids: tuple[str, ...] = ()
    timeline_kinds: tuple[TimelineSourceKind, ...] = ()


class FixtureDeleter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def delete(self, *, content_ref: str) -> str:
        self.calls.append(content_ref)
        return "delete-proof:x0-005-fixture"


def _stable_ids(source_input: dict[str, object]) -> tuple[str, str, str]:
    canonical = json.dumps(source_input, sort_keys=True, separators=(",", ":")).encode()
    digest = sha256(canonical).hexdigest()
    return f"fact-{digest[:24]}", f"evidence-{digest[24:48]}", digest


def _fact_from_input(source_input: dict[str, object]) -> tuple[Fact, Evidence]:
    record_id, evidence_id, digest = _stable_ids(source_input)
    available_at = BASE + timedelta(minutes=int(source_input["available_offset"]))
    accepted_at = available_at + timedelta(seconds=10)
    provenance = Provenance(
        source_ref=SourceReference(str(source_input["source"])),
        content_hash=ContentHash(digest),
        available_at=available_at,
        retrieved_at=available_at,
        accepted_at=accepted_at,
    )
    fact = Fact(
        record_id=record_id,
        schema_version="x0-005-fixture-v0.1",
        subject_ref=SUBJECT,
        accepted_at=accepted_at,
        created_at=accepted_at,
        provenance=provenance,
        fact_type=str(source_input["fact_type"]),
        value=source_input["value"],
        assertion_kind=FactAssertionKind.OBSERVATION,
        evidence_record_ids=(evidence_id,),
    )
    evidence = Evidence(
        record_id=evidence_id,
        schema_version="x0-005-fixture-v0.1",
        subject_ref=SUBJECT,
        accepted_at=accepted_at,
        created_at=accepted_at,
        provenance=provenance,
        evidence_kind=EvidenceKind.SUPPORTING,
        target_record_ids=(record_id,),
        locator=str(source_input["source"]),
        quality_class=EvidenceQuality.TIER_1_OFFICIAL if source_input["kind"] != "news" else EvidenceQuality.TIER_2_REPUTABLE,
        retention_class=RetentionClass.DURABLE_METADATA,
    )
    return fact, evidence


def _fixture_jobs(state: ReplayState) -> tuple[SchedulerJob, ...]:
    jobs: list[SchedulerJob] = []

    for source_input in FIXTURE_INPUTS:
        def execute(item=source_input) -> None:
            fact, evidence = _fact_from_input(item)
            state.facts.append(fact)
            state.evidence.append(evidence)

        jobs.append(SchedulerJob(name=f"ingest-{source_input['kind']}", execute=execute))

    def retention() -> None:
        content = TemporaryContent(
            content_ref="temp://news/x0-005-fixture",
            retention_class=RetentionClass.TEMPORARY_SUCCESS,
            captured_at=BASE,
            expires_at=BASE + timedelta(hours=6),
            state=TemporaryContentState.EXTRACTION_SUCCEEDED,
            extraction_completed_at=BASE + timedelta(minutes=5),
        )
        state.deleted_content = delete_due_content(
            content=content,
            deleter=FixtureDeleter(),
            now=BASE + timedelta(minutes=5),
        )

    def timeline() -> None:
        validate_fact_store(tuple(state.facts) + tuple(state.evidence))
        items = query_unified_timeline(
            facts=tuple(state.facts),
            market_bars=(),
            as_of=BASE + timedelta(minutes=10),
        )
        state.timeline_ids = tuple(item.item_id for item in items)
        state.timeline_kinds = tuple(item.source_kind for item in items)

    jobs.append(SchedulerJob(name="retention", execute=retention))
    jobs.append(SchedulerJob(name="timeline", execute=timeline))
    return tuple(jobs)


def _replay(tmp_path: Path) -> tuple[ReplayState, tuple[str, ...]]:
    state = ReplayState(facts=[], evidence=[])
    result = run_scheduler(
        jobs=_fixture_jobs(state),
        lock_path=tmp_path / "scheduler.lock",
        max_jobs=100,
    )
    return state, result.completed


def test_end_to_end_fixture_regenerates_fact_retention_and_timeline(tmp_path: Path) -> None:
    state, completed = _replay(tmp_path)

    assert completed == (
        "ingest-filing",
        "ingest-ir",
        "ingest-news",
        "ingest-official",
        "retention",
        "timeline",
    )
    assert len(state.facts) == 4
    assert state.deleted_content is not None
    assert state.deleted_content.state is TemporaryContentState.DELETED
    assert state.deleted_content.deletion_proof == "delete-proof:x0-005-fixture"
    assert state.timeline_kinds == (
        TimelineSourceKind.FILING,
        TimelineSourceKind.EARNINGS,
        TimelineSourceKind.NEWS,
        TimelineSourceKind.OFFICIAL,
    )


def test_identical_fixture_replay_is_deterministic(tmp_path: Path) -> None:
    first, _ = _replay(tmp_path / "first")
    second, _ = _replay(tmp_path / "second")

    assert tuple(fact.record_id for fact in first.facts) == tuple(fact.record_id for fact in second.facts)
    assert tuple(item.record_id for item in first.evidence) == tuple(item.record_id for item in second.evidence)
    assert first.timeline_ids == second.timeline_ids
    assert first.timeline_kinds == second.timeline_kinds
    assert first.deleted_content == second.deleted_content


def test_end_to_end_timeline_is_information_time_ordered(tmp_path: Path) -> None:
    state, _ = _replay(tmp_path)
    expected = tuple(_stable_ids(item)[0] for item in FIXTURE_INPUTS)
    assert state.timeline_ids == expected


def test_scheduler_resume_can_finish_fixture_from_job_boundary(tmp_path: Path) -> None:
    state = ReplayState(facts=[], evidence=[])
    jobs = _fixture_jobs(state)

    first = run_scheduler(jobs=jobs, lock_path=tmp_path / "scheduler.lock", max_jobs=3)
    second = run_scheduler(
        jobs=jobs,
        lock_path=tmp_path / "scheduler.lock",
        max_jobs=100,
        resume_after=first.completed[-1],
    )

    assert first.completed == ("ingest-filing", "ingest-ir", "ingest-news")
    assert second.completed == ("ingest-official", "retention", "timeline")
    assert len(state.facts) == 4
    assert state.timeline_kinds[-1] is TimelineSourceKind.OFFICIAL
