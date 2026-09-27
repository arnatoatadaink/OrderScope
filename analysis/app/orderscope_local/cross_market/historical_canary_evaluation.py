"""UWBS-086 historical replay aggregation and final Canary bridge.

Historical classification quality is summarized independently from capacity.
Capacity is injected only in the second-stage assessment so a clean historical
replay cannot hide insufficient Worker/D1 headroom, and vice versa.
"""

from __future__ import annotations

from dataclasses import dataclass

from orderscope_local.contracts.cross_asset_canary import (
    CrossAssetCanaryAssessment,
    CrossAssetCanaryResult,
)
from orderscope_local.contracts.errors import ContractViolation
from .cross_asset_canary_replay import CapacityEnvelope, ProjectedCapacityUsage, assess_replay
from .historical_replay_manifest import HistoricalReplayManifest
from .historical_replay_runner import (
    HistoricalReplayClassification,
    build_canary_result,
    classify_historical_manifest,
)


@dataclass(frozen=True, slots=True)
class HistoricalCanaryEvaluation:
    classifications: tuple[HistoricalReplayClassification, ...]
    results: tuple[CrossAssetCanaryResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.classifications, tuple) or not self.classifications:
            raise ContractViolation("historical Canary evaluation requires classifications")
        if not isinstance(self.results, tuple) or not self.results:
            raise ContractViolation("historical Canary evaluation requires results")
        if len(self.classifications) != len(self.results):
            raise ContractViolation("historical classifications and results must be aligned")
        if len({item.scenario_id for item in self.results}) != len(self.results):
            raise ContractViolation("historical scenario ids must be unique")

    @property
    def false_positive_count(self) -> int:
        return sum(not item.expected_alert and item.observed_alert for item in self.results)

    @property
    def false_negative_count(self) -> int:
        return sum(item.expected_alert and not item.observed_alert for item in self.results)

    @property
    def regime_mismatch_count(self) -> int:
        return sum(item.expected_regime != item.observed_regime for item in self.results)

    @property
    def historical_clean(self) -> bool:
        return not (
            self.false_positive_count
            or self.false_negative_count
            or self.regime_mismatch_count
        )


def evaluate_historical_manifests(
    manifests: tuple[HistoricalReplayManifest, ...],
) -> HistoricalCanaryEvaluation:
    if not isinstance(manifests, tuple) or not manifests:
        raise ContractViolation("historical Canary evaluation requires at least one manifest")

    classifications: list[HistoricalReplayClassification] = []
    results: list[CrossAssetCanaryResult] = []
    for manifest in manifests:
        if not isinstance(manifest, HistoricalReplayManifest):
            raise ContractViolation("historical Canary evaluation requires HistoricalReplayManifest values")
        classification = classify_historical_manifest(manifest)
        classifications.append(classification)
        results.append(build_canary_result(manifest, classification))

    return HistoricalCanaryEvaluation(
        classifications=tuple(classifications),
        results=tuple(results),
    )


def assess_historical_evaluation(
    *,
    evaluation: HistoricalCanaryEvaluation,
    projected: ProjectedCapacityUsage,
    envelope: CapacityEnvelope,
    minimum_headroom_ratio: float = 0.20,
) -> CrossAssetCanaryAssessment:
    if not isinstance(evaluation, HistoricalCanaryEvaluation):
        raise ContractViolation("evaluation must be HistoricalCanaryEvaluation")
    return assess_replay(
        results=evaluation.results,
        projected=projected,
        envelope=envelope,
        minimum_headroom_ratio=minimum_headroom_ratio,
    )
