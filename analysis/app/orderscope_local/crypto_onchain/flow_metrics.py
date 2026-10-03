"""Deterministic abnormal-flow metrics for REL-11B / C0-002.

The module consumes accepted C0-001 confirmed-transfer Facts and produces
bounded Derived Metrics / candidate interpretations.  It never promotes an
abnormal transfer pattern to an exploit, theft, malicious action or confirmed
security incident.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Iterable, Mapping

from .models import ConfirmedTransferFact, CryptoOnchainContractError


WINDOW_MINUTES = (5, 15, 60)
ZERO = Decimal("0")


class AbnormalFlowState(StrEnum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    ELEVATED = "elevated"
    ABNORMAL_FLOW_CANDIDATE = "abnormal_flow_candidate"


class AlternativeExplanation(StrEnum):
    TREASURY_MOVEMENT = "treasury_movement"
    BRIDGE_REBALANCE = "bridge_rebalance"
    UNKNOWN = "unknown"


class DestinationClass(StrEnum):
    EXCHANGE = "exchange"
    BRIDGE = "bridge"
    TREASURY = "treasury"
    CUSTODY = "custody"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass(frozen=True, kw_only=True)
class BaselineStats:
    mean_usd: Decimal
    stddev_usd: Decimal | None = None

    def __post_init__(self) -> None:
        _require_decimal(self.mean_usd, "mean_usd", nonnegative=True)
        if self.stddev_usd is not None:
            _require_decimal(self.stddev_usd, "stddev_usd", nonnegative=True)


@dataclass(frozen=True, kw_only=True)
class FlowThresholds:
    elevated_baseline_ratio: Decimal = Decimal("2.0")
    abnormal_baseline_ratio: Decimal = Decimal("3.0")
    elevated_zscore: Decimal = Decimal("2.0")
    abnormal_zscore: Decimal = Decimal("3.0")
    elevated_balance_ratio: Decimal = Decimal("0.10")
    abnormal_balance_ratio: Decimal = Decimal("0.25")
    burst_transfer_count: int = 3

    def __post_init__(self) -> None:
        for value, field in (
            (self.elevated_baseline_ratio, "elevated_baseline_ratio"),
            (self.abnormal_baseline_ratio, "abnormal_baseline_ratio"),
            (self.elevated_zscore, "elevated_zscore"),
            (self.abnormal_zscore, "abnormal_zscore"),
            (self.elevated_balance_ratio, "elevated_balance_ratio"),
            (self.abnormal_balance_ratio, "abnormal_balance_ratio"),
        ):
            _require_decimal(value, field, nonnegative=True)
        if self.elevated_baseline_ratio > self.abnormal_baseline_ratio:
            raise CryptoOnchainContractError("elevated baseline ratio cannot exceed abnormal threshold")
        if self.elevated_zscore > self.abnormal_zscore:
            raise CryptoOnchainContractError("elevated z-score cannot exceed abnormal threshold")
        if self.elevated_balance_ratio > self.abnormal_balance_ratio:
            raise CryptoOnchainContractError("elevated balance ratio cannot exceed abnormal threshold")
        if isinstance(self.burst_transfer_count, bool) or not isinstance(self.burst_transfer_count, int) or self.burst_transfer_count <= 0:
            raise CryptoOnchainContractError("burst_transfer_count must be a positive integer")


@dataclass(frozen=True, kw_only=True)
class WindowFlowMetrics:
    window_minutes: int
    transfer_count: int
    usd_transfer_count: int
    outflow_usd: Decimal | None
    usd_notional_complete: bool
    distinct_destination_count: int
    destination_counts: tuple[tuple[DestinationClass, int], ...]
    balance_ratio: Decimal | None
    baseline_ratio: Decimal | None
    zscore: Decimal | None
    burst: bool


@dataclass(frozen=True, kw_only=True)
class AbnormalFlowAssessment:
    monitored_address: str
    as_of: datetime
    windows: tuple[WindowFlowMetrics, ...]
    state: AbnormalFlowState
    alternatives: tuple[AlternativeExplanation, ...]

    def window(self, minutes: int) -> WindowFlowMetrics:
        for metric in self.windows:
            if metric.window_minutes == minutes:
                return metric
        raise KeyError(minutes)


def _require_decimal(value: Decimal, field: str, *, nonnegative: bool) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise CryptoOnchainContractError(f"{field} must be a finite Decimal")
    if nonnegative and value < 0:
        raise CryptoOnchainContractError(f"{field} must be non-negative")


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise CryptoOnchainContractError(f"{field} must be normalized to UTC")


def _ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _zscore(value: Decimal | None, baseline: BaselineStats | None) -> Decimal | None:
    if value is None or baseline is None or baseline.stddev_usd is None or baseline.stddev_usd <= 0:
        return None
    return (value - baseline.mean_usd) / baseline.stddev_usd


def _destination_counts(
    transfers: list[ConfirmedTransferFact],
    destination_classes: Mapping[str, DestinationClass],
) -> tuple[tuple[DestinationClass, int], ...]:
    counts: dict[DestinationClass, int] = {}
    for transfer in transfers:
        destination = transfer.to_address
        classification = destination_classes.get(destination, DestinationClass.UNKNOWN) if destination is not None else DestinationClass.UNKNOWN
        if not isinstance(classification, DestinationClass):
            raise CryptoOnchainContractError("destination classification must be DestinationClass")
        counts[classification] = counts.get(classification, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: item[0].value))


def _window_metrics(
    *,
    transfers: list[ConfirmedTransferFact],
    monitored_address: str,
    as_of: datetime,
    window_minutes: int,
    current_balance_usd: Decimal | None,
    baseline: BaselineStats | None,
    destination_classes: Mapping[str, DestinationClass],
    thresholds: FlowThresholds,
) -> WindowFlowMetrics:
    start = as_of - timedelta(minutes=window_minutes)
    selected = [
        transfer
        for transfer in transfers
        if transfer.from_address == monitored_address
        and start < transfer.confirmed_at <= as_of
        and transfer.available_at <= as_of
    ]
    usd_values = [transfer.usd_notional for transfer in selected if transfer.usd_notional is not None]
    complete = len(usd_values) == len(selected)
    if not selected:
        outflow_usd: Decimal | None = ZERO
        complete = True
    elif complete:
        outflow_usd = sum(usd_values, ZERO)
    else:
        outflow_usd = None

    baseline_ratio = _ratio(outflow_usd, baseline.mean_usd if baseline is not None else None)
    balance_ratio = _ratio(outflow_usd, current_balance_usd)
    zscore = _zscore(outflow_usd, baseline)
    destinations = {transfer.to_address for transfer in selected if transfer.to_address is not None}

    has_amount_signal = any(value is not None for value in (baseline_ratio, balance_ratio, zscore))
    burst = len(selected) >= thresholds.burst_transfer_count and has_amount_signal

    return WindowFlowMetrics(
        window_minutes=window_minutes,
        transfer_count=len(selected),
        usd_transfer_count=len(usd_values),
        outflow_usd=outflow_usd,
        usd_notional_complete=complete,
        distinct_destination_count=len(destinations),
        destination_counts=_destination_counts(selected, destination_classes),
        balance_ratio=balance_ratio,
        baseline_ratio=baseline_ratio,
        zscore=zscore,
        burst=burst,
    )


def _state(windows: tuple[WindowFlowMetrics, ...], thresholds: FlowThresholds) -> AbnormalFlowState:
    comparable = [metric for metric in windows if any(value is not None for value in (metric.balance_ratio, metric.baseline_ratio, metric.zscore))]
    if not comparable:
        return AbnormalFlowState.UNKNOWN

    for metric in comparable:
        if (
            (metric.baseline_ratio is not None and metric.baseline_ratio >= thresholds.abnormal_baseline_ratio)
            or (metric.zscore is not None and metric.zscore >= thresholds.abnormal_zscore)
            or (metric.balance_ratio is not None and metric.balance_ratio >= thresholds.abnormal_balance_ratio)
        ):
            return AbnormalFlowState.ABNORMAL_FLOW_CANDIDATE

    for metric in comparable:
        if (
            (metric.baseline_ratio is not None and metric.baseline_ratio >= thresholds.elevated_baseline_ratio)
            or (metric.zscore is not None and metric.zscore >= thresholds.elevated_zscore)
            or (metric.balance_ratio is not None and metric.balance_ratio >= thresholds.elevated_balance_ratio)
        ):
            return AbnormalFlowState.ELEVATED

    return AbnormalFlowState.NORMAL


def assess_abnormal_flow(
    transfers: Iterable[ConfirmedTransferFact],
    *,
    monitored_address: str,
    as_of: datetime,
    current_balance_usd: Decimal | None = None,
    baselines: Mapping[int, BaselineStats] | None = None,
    destination_classes: Mapping[str, DestinationClass] | None = None,
    alternatives: Iterable[AlternativeExplanation] | None = None,
    thresholds: FlowThresholds | None = None,
) -> AbnormalFlowAssessment:
    """Compute bounded REL-11B metrics without incident attribution."""

    if not isinstance(monitored_address, str) or not monitored_address.strip() or monitored_address != monitored_address.strip():
        raise CryptoOnchainContractError("monitored_address must be non-blank and trimmed")
    _require_utc(as_of, "as_of")
    if current_balance_usd is not None:
        _require_decimal(current_balance_usd, "current_balance_usd", nonnegative=True)

    thresholds = thresholds or FlowThresholds()
    baselines = baselines or {}
    destination_classes = destination_classes or {}
    facts = list(transfers)
    for fact in facts:
        if not isinstance(fact, ConfirmedTransferFact):
            raise CryptoOnchainContractError("transfers must contain ConfirmedTransferFact values")
    for minutes, baseline in baselines.items():
        if minutes not in WINDOW_MINUTES:
            raise CryptoOnchainContractError("baseline window must be one of 5, 15, 60 minutes")
        if not isinstance(baseline, BaselineStats):
            raise CryptoOnchainContractError("baseline values must be BaselineStats")

    metrics = tuple(
        _window_metrics(
            transfers=facts,
            monitored_address=monitored_address,
            as_of=as_of,
            window_minutes=minutes,
            current_balance_usd=current_balance_usd,
            baseline=baselines.get(minutes),
            destination_classes=destination_classes,
            thresholds=thresholds,
        )
        for minutes in WINDOW_MINUTES
    )

    supplied_alternatives = tuple(alternatives or (AlternativeExplanation.UNKNOWN,))
    if not supplied_alternatives:
        supplied_alternatives = (AlternativeExplanation.UNKNOWN,)
    if any(not isinstance(value, AlternativeExplanation) for value in supplied_alternatives):
        raise CryptoOnchainContractError("alternatives must contain AlternativeExplanation values")
    deterministic_alternatives = tuple(sorted(set(supplied_alternatives), key=lambda value: value.value))

    return AbnormalFlowAssessment(
        monitored_address=monitored_address,
        as_of=as_of,
        windows=metrics,
        state=_state(metrics, thresholds),
        alternatives=deterministic_alternatives,
    )
