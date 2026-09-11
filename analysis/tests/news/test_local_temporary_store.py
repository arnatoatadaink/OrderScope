from datetime import datetime, timezone

import pytest

from orderscope_local.contracts import ContractViolation
from orderscope_local.news.temporary_store import LocalTemporaryNewsStore, TEMPORARY_STORE_VERSION

UTC = timezone.utc


def test_version_is_frozen():
    assert TEMPORARY_STORE_VERSION == "local-temporary-news-store-v0.1"


def test_stage_returns_opaque_ref_and_keeps_body_under_data_root(tmp_path):
    store = LocalTemporaryNewsStore(data_root=tmp_path)
    ref = store.stage(
        provider_key="alpaca-news",
        article_id="article-1",
        body="temporary body text",
        expires_at=datetime(2026, 9, 12, 1, 0, tzinfo=UTC),
    )
    assert ref.startswith("temporary:v1:")
    assert str(tmp_path) not in ref
    assert store.exists(content_ref=ref) is True
    paths = list((tmp_path / "temporary" / "news").glob("*.txt"))
    assert len(paths) == 1
    assert paths[0].read_text(encoding="utf-8") == "temporary body text"


def test_delete_is_idempotent_and_proof_contains_no_path_or_body(tmp_path):
    store = LocalTemporaryNewsStore(data_root=tmp_path)
    ref = store.stage(
        provider_key="alpaca-news",
        article_id="article-2",
        body="sensitive temporary body",
        expires_at=datetime(2026, 9, 12, 1, 0, tzinfo=UTC),
    )
    proof = store.delete(content_ref=ref)
    assert proof.endswith(":deleted")
    assert str(tmp_path) not in proof
    assert "sensitive temporary body" not in proof
    assert store.exists(content_ref=ref) is False
    second = store.delete(content_ref=ref)
    assert second.endswith(":absent")


def test_invalid_ref_cannot_escape_store_root(tmp_path):
    store = LocalTemporaryNewsStore(data_root=tmp_path)
    for ref in ("../secret", "temporary:v1:../secret", "temporary:v1:not-a-hash"):
        with pytest.raises(ContractViolation, match="temporary content_ref"):
            store.delete(content_ref=ref)


def test_stage_requires_utc_expiry(tmp_path):
    store = LocalTemporaryNewsStore(data_root=tmp_path)
    with pytest.raises(ContractViolation, match="normalized to UTC"):
        store.stage(
            provider_key="alpaca-news",
            article_id="article-3",
            body="temporary body",
            expires_at=datetime(2026, 9, 12, 1, 0),
        )
