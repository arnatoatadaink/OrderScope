"""Issuer-IR earnings fallback and SEC/IR evidence reconciliation for E0-003.

The module keeps IR discovery metadata, the canonical individual release URL,
content identity, and fiscal-period semantics distinct. SEC remains the first
reference source when present, while issuer IR is retained as independent Tier-1
evidence rather than replacing or duplicating the SEC event.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import IntEnum, StrEnum
from urllib.parse import urlparse

from orderscope_local.contracts import ContentHash, ContractViolation, SourceTimestamp
from orderscope_local.sec import SecEarningsCandidate


class IrReleaseSource(StrEnum):
    AMD_IR = "amd_ir"
    NVIDIA_IR = "nvidia_ir"


class EarningsSourcePriority(IntEnum):
    SEC = 0
    ISSUER_IR = 1


_ALLOWED_HOSTS = {
    IrReleaseSource.AMD_IR: {"ir.amd.com"},
    IrReleaseSource.NVIDIA_IR: {"investor.nvidia.com", "nvidianews.nvidia.com"},
}
_CANARY = {
    IrReleaseSource.AMD_IR: "AMD",
    IrReleaseSource.NVIDIA_IR: "NVDA",
}


@dataclass(frozen=True, slots=True)
class IrReleaseRecord:
    instrument_id: str
    source: IrReleaseSource
    discovery_url: str
    canonical_release_url: str
    content_hash: ContentHash
    fiscal_year_label: str
    fiscal_quarter: str
    period_end: date
    published_at: SourceTimestamp | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, IrReleaseSource):
            raise ContractViolation("IR release source is invalid")
        if self.instrument_id != _CANARY[self.source]:
            raise ContractViolation("IR release instrument is outside the configured canary source")
        _require_https_host(self.discovery_url, self.source, "discovery_url")
        _require_https_host(self.canonical_release_url, self.source, "canonical_release_url")
        if self.discovery_url == self.canonical_release_url:
            raise ContractViolation("IR discovery and canonical release URLs must remain distinct roles")
        if not isinstance(self.content_hash, ContentHash):
            raise ContractViolation("IR release requires a ContentHash")
        for field, value in (
            ("fiscal_year_label", self.fiscal_year_label),
            ("fiscal_quarter", self.fiscal_quarter),
        ):
            if not isinstance(value, str) or not value or value != value.strip() or len(value) > 64:
                raise ContractViolation(f"IR {field} must be bounded canonical text")
        if not isinstance(self.period_end, date):
            raise ContractViolation("IR period_end must be a date")
        if self.published_at is not None and not isinstance(self.published_at, SourceTimestamp):
            raise ContractViolation("IR published_at must be a SourceTimestamp")


@dataclass(frozen=True, slots=True)
class EarningsEvidenceBundle:
    instrument_id: str
    period_end: date
    sec_candidates: tuple[SecEarningsCandidate, ...]
    ir_releases: tuple[IrReleaseRecord, ...]
    source_priority: tuple[EarningsSourcePriority, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.instrument_id, str) or not self.instrument_id:
            raise ContractViolation("earnings evidence bundle requires instrument_id")
        if not isinstance(self.period_end, date):
            raise ContractViolation("earnings evidence bundle requires period_end")
        if not isinstance(self.sec_candidates, tuple) or any(
            not isinstance(item, SecEarningsCandidate) for item in self.sec_candidates
        ):
            raise ContractViolation("earnings evidence bundle has invalid SEC candidates")
        if not isinstance(self.ir_releases, tuple) or any(
            not isinstance(item, IrReleaseRecord) for item in self.ir_releases
        ):
            raise ContractViolation("earnings evidence bundle has invalid IR releases")
        expected = (
            (EarningsSourcePriority.SEC, EarningsSourcePriority.ISSUER_IR)
            if self.sec_candidates and self.ir_releases
            else (EarningsSourcePriority.SEC,)
            if self.sec_candidates
            else (EarningsSourcePriority.ISSUER_IR,)
        )
        if self.source_priority != expected:
            raise ContractViolation("earnings source priority does not match retained evidence")
        for candidate in self.sec_candidates:
            if candidate.filing.ticker != self.instrument_id:
                raise ContractViolation("SEC earnings candidate instrument does not match bundle")
            if candidate.filing.period_end != self.period_end:
                raise ContractViolation("SEC earnings candidate period does not match bundle")
        for release in self.ir_releases:
            if release.instrument_id != self.instrument_id or release.period_end != self.period_end:
                raise ContractViolation("IR release event identity does not match bundle")


def reconcile_sec_ir_evidence(
    *,
    sec_candidates: tuple[SecEarningsCandidate, ...] = (),
    ir_releases: tuple[IrReleaseRecord, ...] = (),
) -> EarningsEvidenceBundle:
    """Deduplicate discoveries while retaining SEC and IR as independent evidence.

    Reconciliation is deliberately event-scoped by canary instrument and period_end.
    Repeated IR discovery through multiple listing/archive paths collapses only when
    the canonical release URL and content hash are identical. SEC candidates are
    deduplicated by accession. A hash change at the same canonical IR URL is not
    silently treated as a duplicate because it may represent a corrected release.
    """

    if not isinstance(sec_candidates, tuple) or not isinstance(ir_releases, tuple):
        raise ContractViolation("SEC/IR reconciliation inputs must be tuples")
    if not sec_candidates and not ir_releases:
        raise ContractViolation("SEC/IR reconciliation requires at least one evidence source")

    sec_unique: dict[str, SecEarningsCandidate] = {}
    for candidate in sec_candidates:
        if not isinstance(candidate, SecEarningsCandidate):
            raise ContractViolation("SEC/IR reconciliation contains an invalid SEC candidate")
        accession = candidate.filing.accession
        existing = sec_unique.get(accession)
        if existing is not None and existing != candidate:
            raise ContractViolation("same SEC accession has conflicting earnings candidate evidence")
        sec_unique[accession] = candidate

    ir_unique: dict[tuple[str, str], IrReleaseRecord] = {}
    url_hashes: dict[str, str] = {}
    for release in ir_releases:
        if not isinstance(release, IrReleaseRecord):
            raise ContractViolation("SEC/IR reconciliation contains an invalid IR release")
        digest = release.content_hash.digest
        previous = url_hashes.get(release.canonical_release_url)
        if previous is not None and previous != digest:
            raise ContractViolation("canonical IR release URL changed content hash; preserve as update/conflict")
        url_hashes[release.canonical_release_url] = digest
        ir_unique[(release.canonical_release_url, digest)] = release

    retained_sec = tuple(sec_unique[key] for key in sorted(sec_unique))
    retained_ir = tuple(
        ir_unique[key]
        for key in sorted(ir_unique, key=lambda item: (item[0], item[1]))
    )

    identities = {
        (candidate.filing.ticker, candidate.filing.period_end) for candidate in retained_sec
    } | {(release.instrument_id, release.period_end) for release in retained_ir}
    if None in {period for _, period in identities}:
        raise ContractViolation("SEC/IR reconciliation requires an established period_end")
    if len(identities) != 1:
        raise ContractViolation("SEC/IR evidence does not identify one earnings event")

    instrument_id, period_end = next(iter(identities))
    priority = (
        (EarningsSourcePriority.SEC, EarningsSourcePriority.ISSUER_IR)
        if retained_sec and retained_ir
        else (EarningsSourcePriority.SEC,)
        if retained_sec
        else (EarningsSourcePriority.ISSUER_IR,)
    )
    return EarningsEvidenceBundle(
        instrument_id=instrument_id,
        period_end=period_end,
        sec_candidates=retained_sec,
        ir_releases=retained_ir,
        source_priority=priority,
    )


def _require_https_host(url: object, source: IrReleaseSource, field: str) -> None:
    if not isinstance(url, str) or not url or url != url.strip() or len(url) > 2048:
        raise ContractViolation(f"IR {field} must be a bounded canonical URL")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname not in _ALLOWED_HOSTS[source]:
        raise ContractViolation(f"IR {field} must use the configured official issuer host")
    if parsed.username or parsed.password or parsed.fragment:
        raise ContractViolation(f"IR {field} cannot contain credentials or fragments")
