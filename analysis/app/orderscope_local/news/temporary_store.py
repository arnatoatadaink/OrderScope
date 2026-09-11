"""Concrete local temporary News body storage for operator retention work.

Bodies are stored only beneath ORDERSCOPE_DATA_ROOT/temporary/news.  Durable
callers receive opaque content refs; filesystem paths never cross the boundary.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import secrets

from orderscope_local.contracts import ContractViolation


TEMPORARY_STORE_VERSION = "local-temporary-news-store-v0.1"
_REF_PREFIX = "temporary:v1:"


class LocalTemporaryNewsStore:
    def __init__(self, *, data_root: Path) -> None:
        if not isinstance(data_root, Path) or not str(data_root).strip():
            raise ContractViolation("data_root must be a non-empty pathlib.Path")
        self._root = data_root / "temporary" / "news"

    def stage(self, *, provider_key: str, article_id: str, body: str, expires_at: datetime) -> str:
        _identity(provider_key, "provider_key")
        _identity(article_id, "article_id")
        if not isinstance(body, str) or not body.strip():
            raise ContractViolation("temporary body must be non-blank text")
        _utc(expires_at, "expires_at")
        self._root.mkdir(parents=True, exist_ok=True)
        token = secrets.token_hex(16)
        identity = hashlib.sha256(f"{provider_key}\0{article_id}\0{token}".encode("utf-8")).hexdigest()
        path = self._path(identity)
        path.write_text(body, encoding="utf-8")
        return f"{_REF_PREFIX}{identity}"

    def delete(self, *, content_ref: str) -> str:
        identity = _parse_ref(content_ref)
        path = self._path(identity)
        try:
            path.unlink()
        except FileNotFoundError:
            # Idempotent deletion proof: absence is sufficient and does not reveal a path.
            return f"delete-proof:{identity}:absent"
        except OSError as exc:
            raise ContractViolation("temporary content deletion failed") from exc
        return f"delete-proof:{identity}:deleted"

    def exists(self, *, content_ref: str) -> bool:
        return self._path(_parse_ref(content_ref)).is_file()

    def _path(self, identity: str) -> Path:
        return self._root / f"{identity}.txt"


def _parse_ref(content_ref: str) -> str:
    if not isinstance(content_ref, str) or not content_ref.startswith(_REF_PREFIX):
        raise ContractViolation("unsupported temporary content_ref")
    identity = content_ref.removeprefix(_REF_PREFIX)
    if len(identity) != 64 or any(character not in "0123456789abcdef" for character in identity):
        raise ContractViolation("invalid temporary content_ref")
    return identity


def _identity(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 512:
        raise ContractViolation(f"{field} must be bounded non-blank canonical text")


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")
