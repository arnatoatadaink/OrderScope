from datetime import datetime, timedelta, timezone

import pytest

from orderscope_local.contracts import ContractViolation, RetentionClass, TemporaryContent, TemporaryContentState
from orderscope_local.news import (
    NEWS_RETENTION_CONTROLLER_VERSION,
    assert_exception_retention_compliant,
    delete_due_content,
    retention_decision,
)

UTC = timezone.utc
CAPTURED = datetime(2026, 9, 9, 0, 0, tzinfo=UTC)
EXTRACTED = CAPTURED + timedelta(minutes=5)


class Deleter:
    def __init__(self, proof="delete-proof:fixture-123", error=None):
        self.proof = proof
        self.error = error
        self.calls = []

    def delete(self, *, content_ref):
        self.calls.append(content_ref)
        if self.error is not None:
            raise self.error
        return self.proof


def _success():
    return TemporaryContent(
        content_ref="temp://news/success-1",
        retention_class=RetentionClass.TEMPORARY_SUCCESS,
        captured_at=CAPTURED,
        expires_at=CAPTURED + timedelta(hours=6),
        state=TemporaryContentState.EXTRACTION_SUCCEEDED,
        extraction_completed_at=EXTRACTED,
    )


def _exception(*, expires_at=None):
    return TemporaryContent(
        content_ref="temp://news/exception-1",
        retention_class=RetentionClass.TEMPORARY_EXCEPTION,
        captured_at=CAPTURED,
        expires_at=expires_at or CAPTURED + timedelta(days=30),
        state=TemporaryContentState.EXCEPTION,
        exception_reason="Extraction failed after temporary body acquisition.",
    )


def test_controller_version_is_frozen():
    assert NEWS_RETENTION_CONTROLLER_VERSION == "news-retention-controller-v0.1"


def test_success_body_is_due_immediately_after_extraction():
    content = _success()
    before = retention_decision(content=content, now=EXTRACTED - timedelta(microseconds=1))
    due = retention_decision(content=content, now=EXTRACTED)

    assert before.delete_now is False
    assert due.delete_now is True
    assert due.due_at == EXTRACTED
    assert due.reason == "success_delete_after_extraction"


def test_success_delete_returns_audit_record_without_body():
    content = _success()
    deleter = Deleter()

    deleted = delete_due_content(content=content, deleter=deleter, now=EXTRACTED)

    assert deleter.calls == [content.content_ref]
    assert deleted.state is TemporaryContentState.DELETED
    assert deleted.retention_class is RetentionClass.TEMPORARY_SUCCESS
    assert deleted.extraction_completed_at == EXTRACTED
    assert deleted.deleted_at == EXTRACTED
    assert deleted.deletion_proof == "delete-proof:fixture-123"
    assert not hasattr(deleted, "body")


def test_exception_body_is_retained_before_expiry_and_due_at_expiry():
    content = _exception()
    deleter = Deleter()

    before = delete_due_content(content=content, deleter=deleter, now=content.expires_at - timedelta(seconds=1))
    assert before is content
    assert deleter.calls == []

    deleted = delete_due_content(content=content, deleter=deleter, now=content.expires_at)
    assert deleted.state is TemporaryContentState.DELETED
    assert deleted.exception_reason == content.exception_reason
    assert deleted.deleted_at == content.expires_at
    assert deleter.calls == [content.content_ref]


def test_i0_contract_rejects_exception_expiry_beyond_30_days():
    with pytest.raises(ContractViolation, match="within 30 days"):
        _exception(expires_at=CAPTURED + timedelta(days=30, microseconds=1))


def test_retention_compliance_flags_exception_left_at_or_past_expiry():
    content = _exception()
    assert_exception_retention_compliant(content=content, now=content.expires_at - timedelta(microseconds=1))

    with pytest.raises(ContractViolation, match="beyond mandatory expiry"):
        assert_exception_retention_compliant(content=content, now=content.expires_at)


def test_success_body_cannot_be_deleted_before_extraction_succeeds():
    staged = TemporaryContent(
        content_ref="temp://news/staged",
        retention_class=RetentionClass.TEMPORARY_SUCCESS,
        captured_at=CAPTURED,
        expires_at=CAPTURED + timedelta(hours=6),
        state=TemporaryContentState.STAGED,
    )
    with pytest.raises(ContractViolation, match="requires extraction_succeeded"):
        retention_decision(content=staged, now=EXTRACTED)


def test_already_deleted_content_is_idempotent_and_does_not_hit_store():
    deleted = delete_due_content(content=_success(), deleter=Deleter(), now=EXTRACTED)
    deleter = Deleter(proof="different-proof")

    same = delete_due_content(content=deleted, deleter=deleter, now=EXTRACTED + timedelta(minutes=1))

    assert same is deleted
    assert deleter.calls == []
    assert same.deletion_proof == "delete-proof:fixture-123"


def test_deletion_failure_does_not_fabricate_deleted_state():
    content = _success()
    deleter = Deleter(error=OSError("local path must not leak"))

    with pytest.raises(ContractViolation, match="temporary content deletion failed") as excinfo:
        delete_due_content(content=content, deleter=deleter, now=EXTRACTED)

    assert "local path" not in str(excinfo.value)
    assert content.state is TemporaryContentState.EXTRACTION_SUCCEEDED


def test_invalid_or_secret_like_deletion_proof_is_rejected():
    for proof in ("", "api_key=do-not-store"):
        with pytest.raises(ContractViolation, match="deletion proof"):
            delete_due_content(content=_success(), deleter=Deleter(proof=proof), now=EXTRACTED)


def test_retention_time_requires_utc():
    naive = datetime(2026, 9, 9, 0, 5)
    with pytest.raises(ContractViolation, match="normalized to UTC"):
        retention_decision(content=_success(), now=naive)
