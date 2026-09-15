from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import (
    ContractViolation,
    RetentionClass,
    TemporaryContent,
    TemporaryContentState,
    validate_temporary_content,
)


UTC = timezone.utc
T0 = datetime(2026, 9, 6, 0, 0, tzinfo=UTC)


def test_successful_temporary_content_keeps_only_reference_and_expiry_audit():
    record = TemporaryContent(
        content_ref="tmp:sha256:article-1",
        retention_class=RetentionClass.TEMPORARY_SUCCESS,
        captured_at=T0,
        expires_at=T0 + timedelta(hours=1),
        state=TemporaryContentState.EXTRACTION_SUCCEEDED,
        extraction_completed_at=T0 + timedelta(minutes=5),
    )

    validate_temporary_content(record)
    assert record.content_ref == "tmp:sha256:article-1"
    assert not hasattr(record, "body")


def test_deleted_content_requires_proof_and_preserves_exception_reason():
    record = TemporaryContent(
        content_ref="tmp:sha256:failed-1",
        retention_class=RetentionClass.TEMPORARY_EXCEPTION,
        captured_at=T0,
        expires_at=T0 + timedelta(days=30),
        state=TemporaryContentState.DELETED,
        exception_reason="extractor_timeout",
        deleted_at=T0 + timedelta(days=1),
        deletion_proof="delete-log:2026-09-07:failed-1",
    )

    validate_temporary_content(record)
    assert record.exception_reason == "extractor_timeout"
    assert record.deletion_proof.startswith("delete-log:")


def test_exception_content_requires_reason_and_stays_bounded_to_thirty_days():
    with pytest.raises(ContractViolation, match="exception_reason"):
        TemporaryContent(
            content_ref="tmp:sha256:failed-2",
            retention_class=RetentionClass.TEMPORARY_EXCEPTION,
            captured_at=T0,
            expires_at=T0 + timedelta(days=30),
            state=TemporaryContentState.EXCEPTION,
        )

    record = TemporaryContent(
        content_ref="tmp:sha256:failed-3",
        retention_class=RetentionClass.TEMPORARY_EXCEPTION,
        captured_at=T0,
        expires_at=T0 + timedelta(days=30),
        state=TemporaryContentState.EXCEPTION,
        exception_reason="provider_partial",
    )
    assert record.expires_at <= record.captured_at + timedelta(days=30)

    with pytest.raises(ContractViolation, match="within 30 days"):
        TemporaryContent(
            content_ref="tmp:sha256:failed-4",
            retention_class=RetentionClass.TEMPORARY_EXCEPTION,
            captured_at=T0,
            expires_at=T0 + timedelta(days=31),
            state=TemporaryContentState.EXCEPTION,
            exception_reason="provider_partial",
        )


def test_secret_like_lifecycle_metadata_and_durable_metadata_are_rejected():
    with pytest.raises(ContractViolation, match="temporary retention class"):
        TemporaryContent(
            content_ref="tmp:sha256:durable",
            retention_class=RetentionClass.DURABLE_METADATA,
            captured_at=T0,
            expires_at=T0,
        )

    with pytest.raises(ContractViolation, match="secret-like"):
        TemporaryContent(
            content_ref="tmp:sha256:secret",
            retention_class=RetentionClass.TEMPORARY_SUCCESS,
            captured_at=T0,
            expires_at=T0,
            state=TemporaryContentState.EXCEPTION,
            exception_reason="api_key=fixture-secret",
        )


def test_deleted_successful_content_requires_deletion_proof():
    with pytest.raises(ContractViolation, match="deletion_proof"):
        TemporaryContent(
            content_ref="tmp:sha256:deleted",
            retention_class=RetentionClass.TEMPORARY_SUCCESS,
            captured_at=T0,
            expires_at=T0,
            state=TemporaryContentState.DELETED,
            deleted_at=T0 + timedelta(seconds=1),
        )


def test_state_and_retention_class_must_agree():
    with pytest.raises(ContractViolation, match="temporary_success retention"):
        TemporaryContent(
            content_ref="tmp:sha256:wrong-class",
            retention_class=RetentionClass.TEMPORARY_EXCEPTION,
            captured_at=T0,
            expires_at=T0,
            state=TemporaryContentState.EXTRACTION_SUCCEEDED,
            extraction_completed_at=T0,
        )
