from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    ContentHash,
    ContractViolation,
    Provenance,
    ProviderRevision,
    SourceReference,
    SourceTimestamp,
    TimestampPrecision,
    assert_secret_free,
)


UTC = timezone.utc
AVAILABLE = datetime(2026, 8, 4, 20, 16, 24, tzinfo=UTC)
RETRIEVED = AVAILABLE + timedelta(seconds=2)
ACCEPTED = RETRIEVED + timedelta(seconds=1)


def provenance(**overrides):
    values = {
        "source_ref": SourceReference("https://www.sec.gov/Archives/example.txt"),
        "content_hash": ContentHash("a" * 64),
        "provider_revision": ProviderRevision("0000002488-26-000121"),
        "event_time": SourceTimestamp.date_only(date(2026, 6, 27)),
        "published_at": SourceTimestamp.at(AVAILABLE, source_timezone="America/New_York"),
        "filed_at": SourceTimestamp.date_only(date(2026, 8, 4)),
        "source_accepted_at": SourceTimestamp.at(AVAILABLE),
        "available_at": AVAILABLE,
        "retrieved_at": RETRIEVED,
        "accepted_at": ACCEPTED,
    }
    values.update(overrides)
    return Provenance(**values)


def test_provenance_fixes_distinct_source_and_operational_timestamps():
    value = provenance()

    assert value.event_time.precision is TimestampPrecision.DATE_ONLY
    assert value.event_time.calendar_date == date(2026, 6, 27)
    assert value.event_time.instant is None
    assert value.published_at.source_timezone == "America/New_York"
    assert value.filed_at != value.published_at
    assert value.source_accepted_at.instant == AVAILABLE
    assert value.accepted_at == ACCEPTED


def test_unknown_external_timestamps_remain_none_and_are_not_backfilled():
    value = provenance(event_time=None, published_at=None, filed_at=None, source_accepted_at=None)

    assert value.event_time is None
    assert value.published_at is None
    assert value.filed_at is None
    assert value.source_accepted_at is None
    assert value.retrieved_at == RETRIEVED


def test_date_only_timestamp_cannot_be_fabricated_as_an_instant():
    value = SourceTimestamp.date_only(date(2026, 8, 4), source_timezone="America/New_York")

    assert value.calendar_date == date(2026, 8, 4)
    assert value.instant is None
    with pytest.raises(ContractViolation, match="date, not a datetime"):
        SourceTimestamp.date_only(AVAILABLE)


@pytest.mark.parametrize("field", ["available_at", "retrieved_at", "accepted_at"])
def test_operational_timestamps_require_utc(field):
    with pytest.raises(ContractViolation, match="UTC"):
        provenance(**{field: datetime(2026, 8, 4, 16, tzinfo=timezone(timedelta(hours=-4)))})


def test_provenance_rejects_invalid_operational_order():
    with pytest.raises(ContractViolation, match="available_at"):
        provenance(available_at=RETRIEVED + timedelta(seconds=1))
    with pytest.raises(ContractViolation, match="retrieved_at"):
        provenance(accepted_at=RETRIEVED - timedelta(seconds=1))


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SourceReference(" "),
        lambda: ProviderRevision(""),
        lambda: ContentHash("A" * 64),
        lambda: ContentHash("a" * 63),
        lambda: ContentHash("a" * 64, algorithm="md5"),
    ],
)
def test_provenance_value_objects_reject_ambiguous_values(factory):
    with pytest.raises(ContractViolation):
        factory()


def test_provenance_is_immutable_and_contains_no_raw_body_or_secret_field():
    value = provenance()
    with pytest.raises(FrozenInstanceError):
        value.accepted_at = RETRIEVED

    assert_secret_free(value.__dict__)
    assert set(value.__dict__) == {
        "source_ref",
        "content_hash",
        "retrieved_at",
        "available_at",
        "accepted_at",
        "provider_revision",
        "event_time",
        "published_at",
        "filed_at",
        "source_accepted_at",
    }
