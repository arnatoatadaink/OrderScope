from datetime import date, datetime, timezone

import pytest

from orderscope_local.contracts import ContentHash, ContractViolation, Provenance, SourceReference
from orderscope_local.earnings.segment_identity import (
    SegmentClassificationRole,
    SegmentHistoryChange,
    SegmentHistoryEdge,
    SegmentIdentityHistory,
    SegmentIdentityVersion,
    resolve_segment_version,
)


def _provenance(url: str, digest: str) -> Provenance:
    return Provenance(
        source_ref=SourceReference(url),
        content_hash=ContentHash(digest),
        retrieved_at=datetime(2026, 8, 10, 20, 0, 1, tzinfo=timezone.utc),
        available_at=datetime(2026, 8, 10, 20, 0, 1, tzinfo=timezone.utc),
        accepted_at=datetime(2026, 8, 10, 20, 0, 2, tzinfo=timezone.utc),
    )


def test_amd_client_and_gaming_merge_into_distinct_client_gaming_identity() -> None:
    provenance = _provenance("https://www.sec.gov/amd/2025-10-k", "a" * 64)
    versions = (
        SegmentIdentityVersion(
            segment_id="amd:segment:client",
            instrument_id="AMD",
            classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
            issuer_label="Client",
            valid_from=date(2023, 1, 1),
            valid_to=date(2024, 12, 31),
            as_reported_at=date(2024, 2, 1),
            filing_accession="0000002488-24-000001",
            provenance=provenance,
        ),
        SegmentIdentityVersion(
            segment_id="amd:segment:gaming",
            instrument_id="AMD",
            classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
            issuer_label="Gaming",
            valid_from=date(2023, 1, 1),
            valid_to=date(2024, 12, 31),
            as_reported_at=date(2024, 2, 1),
            filing_accession="0000002488-24-000001",
            provenance=provenance,
        ),
        SegmentIdentityVersion(
            segment_id="amd:segment:client-gaming",
            instrument_id="AMD",
            classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
            issuer_label="Client and Gaming",
            valid_from=date(2025, 1, 1),
            valid_to=None,
            as_reported_at=date(2026, 2, 1),
            filing_accession="0000002488-26-000010",
            provenance=provenance,
            recast=True,
        ),
    )
    edge = SegmentHistoryEdge(
        change=SegmentHistoryChange.MERGED,
        from_segment_ids=("amd:segment:client", "amd:segment:gaming"),
        to_segment_ids=("amd:segment:client-gaming",),
        effective_on=date(2025, 1, 1),
        as_reported_at=date(2026, 2, 1),
        filing_accession="0000002488-26-000010",
        provenance=provenance,
    )
    history = SegmentIdentityHistory(versions=versions, edges=(edge,))

    resolved = resolve_segment_version(history, segment_id="amd:segment:client-gaming", on_date=date(2025, 6, 30))
    assert resolved.issuer_label == "Client and Gaming"
    assert resolved.recast is True


def test_same_label_different_role_is_not_same_identity() -> None:
    provenance = _provenance("https://www.sec.gov/nvda/example", "b" * 64)
    versions = (
        SegmentIdentityVersion(
            segment_id="nvda:segment:compute-networking",
            instrument_id="NVDA",
            classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
            issuer_label="Compute & Networking",
            valid_from=date(2024, 1, 1),
            valid_to=None,
            as_reported_at=date(2026, 8, 1),
            filing_accession="0001045810-26-000100",
            provenance=provenance,
        ),
        SegmentIdentityVersion(
            segment_id="nvda:platform:compute-networking",
            instrument_id="NVDA",
            classification_role=SegmentClassificationRole.MARKET_PLATFORM,
            issuer_label="Compute & Networking",
            valid_from=date(2024, 1, 1),
            valid_to=None,
            as_reported_at=date(2026, 8, 1),
            filing_accession="0001045810-26-000100",
            provenance=provenance,
        ),
    )
    history = SegmentIdentityHistory(versions=versions, edges=())

    reportable = resolve_segment_version(
        history,
        segment_id="nvda:segment:compute-networking",
        on_date=date(2026, 7, 26),
        classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
    )
    assert reportable.segment_id != "nvda:platform:compute-networking"


def test_recast_is_explicit_history_not_label_rewrite() -> None:
    provenance = _provenance("https://www.sec.gov/amd/recast", "c" * 64)
    original = SegmentIdentityVersion(
        segment_id="amd:segment:data-center",
        instrument_id="AMD",
        classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
        issuer_label="Data Center",
        valid_from=date(2024, 1, 1),
        valid_to=date(2024, 12, 31),
        as_reported_at=date(2025, 2, 1),
        filing_accession="0000002488-25-000010",
        provenance=provenance,
        recast=False,
    )
    recast = SegmentIdentityVersion(
        segment_id="amd:segment:data-center",
        instrument_id="AMD",
        classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
        issuer_label="Data Center",
        valid_from=date(2025, 1, 1),
        valid_to=None,
        as_reported_at=date(2026, 2, 1),
        filing_accession="0000002488-26-000010",
        provenance=provenance,
        recast=True,
    )
    edge = SegmentHistoryEdge(
        change=SegmentHistoryChange.RECAST,
        from_segment_ids=("amd:segment:data-center",),
        to_segment_ids=("amd:segment:data-center",),
        effective_on=date(2025, 1, 1),
        as_reported_at=date(2026, 2, 1),
        filing_accession="0000002488-26-000010",
        provenance=provenance,
        note="prior periods retrospectively adjusted",
    )
    history = SegmentIdentityHistory(versions=(original, recast), edges=(edge,))
    assert resolve_segment_version(history, segment_id="amd:segment:data-center", on_date=date(2025, 6, 30)).recast is True


def test_overlapping_versions_for_same_stable_id_are_rejected() -> None:
    provenance = _provenance("https://www.sec.gov/example", "d" * 64)
    with pytest.raises(ContractViolation, match="overlap"):
        SegmentIdentityHistory(
            versions=(
                SegmentIdentityVersion(
                    segment_id="amd:segment:x",
                    instrument_id="AMD",
                    classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
                    issuer_label="X",
                    valid_from=date(2025, 1, 1),
                    valid_to=None,
                    as_reported_at=date(2025, 2, 1),
                    filing_accession="0000002488-25-000001",
                    provenance=provenance,
                ),
                SegmentIdentityVersion(
                    segment_id="amd:segment:x",
                    instrument_id="AMD",
                    classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
                    issuer_label="X renamed",
                    valid_from=date(2026, 1, 1),
                    valid_to=None,
                    as_reported_at=date(2026, 2, 1),
                    filing_accession="0000002488-26-000001",
                    provenance=provenance,
                ),
            ),
            edges=(),
        )


def test_merge_shape_and_unknown_edge_refs_are_rejected() -> None:
    provenance = _provenance("https://www.sec.gov/example2", "e" * 64)
    version = SegmentIdentityVersion(
        segment_id="amd:segment:a",
        instrument_id="AMD",
        classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
        issuer_label="A",
        valid_from=date(2025, 1, 1),
        valid_to=None,
        as_reported_at=date(2025, 2, 1),
        filing_accession="0000002488-25-000001",
        provenance=provenance,
    )
    edge = SegmentHistoryEdge(
        change=SegmentHistoryChange.MERGED,
        from_segment_ids=("amd:segment:a", "amd:segment:missing"),
        to_segment_ids=("amd:segment:a",),
        effective_on=date(2025, 1, 1),
        as_reported_at=date(2025, 2, 1),
        filing_accession="0000002488-25-000001",
        provenance=provenance,
    )
    with pytest.raises(ContractViolation, match="unknown"):
        SegmentIdentityHistory(versions=(version,), edges=(edge,))


def test_resolution_never_uses_issuer_label_as_identity() -> None:
    provenance = _provenance("https://www.sec.gov/nvda/graphics", "f" * 64)
    history = SegmentIdentityHistory(
        versions=(
            SegmentIdentityVersion(
                segment_id="nvda:segment:graphics",
                instrument_id="NVDA",
                classification_role=SegmentClassificationRole.REPORTABLE_SEGMENT,
                issuer_label="Graphics",
                valid_from=date(2024, 1, 1),
                valid_to=None,
                as_reported_at=date(2026, 8, 1),
                filing_accession="0001045810-26-000100",
                provenance=provenance,
            ),
        ),
        edges=(),
    )
    with pytest.raises(ContractViolation, match="missing or ambiguous"):
        resolve_segment_version(history, segment_id="Graphics", on_date=date(2026, 7, 26))
