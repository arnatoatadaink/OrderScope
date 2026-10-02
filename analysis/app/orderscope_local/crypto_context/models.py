"""Source-neutral contracts for BTC-relative crypto market context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from orderscope_local.contracts.errors import ContractViolation


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None or value.utcoffset() != timedelta(0):
        raise ContractViolation(f"{field} must be normalized to UTC")


def _nonblank(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractViolation(f"{field} must be non-blank")


@dataclass(frozen=True, kw_only=True)
class CryptoReturnObservation:
    """Aligned return observation used for BTC-relative analysis.

    The record is analytical input only. It does not assert causality or leader status.
    """

    instrument_ref: str
    window_start: datetime
    window_end: datetime
    return_decimal: float
    source_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _nonblank(self.instrument_ref, "instrument_ref")
        _utc(self.window_start, "window_start")
        _utc(self.window_end, "window_end")
        if self.window_end <= self.window_start:
            raise ContractViolation("window_end must be later than window_start")
        if not isinstance(self.return_decimal, (int, float)):
            raise ContractViolation("return_decimal must be numeric")
        if not isinstance(self.source_record_ids, tuple) or not self.source_record_ids:
            raise ContractViolation("source_record_ids must be a non-empty immutable tuple")
        if len(self.source_record_ids) != len(set(self.source_record_ids)):
            raise ContractViolation("source_record_ids cannot contain duplicates")
        for value in self.source_record_ids:
            _nonblank(value, "source_record_ids")


@dataclass(frozen=True, kw_only=True)
class BtcRelativePair:
    btc: CryptoReturnObservation
    target: CryptoReturnObservation

    def __post_init__(self) -> None:
        if self.btc.instrument_ref == self.target.instrument_ref:
            raise ContractViolation("BTC and target instruments must differ")
        if self.btc.window_start != self.target.window_start or self.btc.window_end != self.target.window_end:
            raise ContractViolation("BTC and target observations must use the same analysis window")


@dataclass(frozen=True, kw_only=True)
class CryptoBreadthObservation:
    """Cross-sectional direction snapshot relative to the BTC move."""

    as_of: datetime
    btc_return_decimal: float
    member_returns: tuple[float, ...]
    input_record_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _utc(self.as_of, "as_of")
        if not isinstance(self.member_returns, tuple) or not self.member_returns:
            raise ContractViolation("member_returns must be a non-empty immutable tuple")
        if any(not isinstance(value, (int, float)) for value in self.member_returns):
            raise ContractViolation("member_returns must be numeric")
        if not isinstance(self.input_record_ids, tuple) or not self.input_record_ids:
            raise ContractViolation("input_record_ids must be a non-empty immutable tuple")
        if len(self.input_record_ids) != len(set(self.input_record_ids)):
            raise ContractViolation("input_record_ids cannot contain duplicates")
