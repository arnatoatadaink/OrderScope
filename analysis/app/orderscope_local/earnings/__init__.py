"""Provider-neutral earnings integration helpers."""

from .basic_facts import (
    BasicEarningsMetricType,
    ObservedEarningsMetric,
    extract_basic_earnings_records,
)
from .ir_fallback import (
    EarningsEvidenceBundle,
    EarningsSourcePriority,
    IrReleaseRecord,
    IrReleaseSource,
    reconcile_sec_ir_evidence,
)
from .segment_identity import (
    SegmentClassificationRole,
    SegmentHistoryChange,
    SegmentHistoryEdge,
    SegmentIdentityHistory,
    SegmentIdentityVersion,
    resolve_segment_version,
)
from .segment_revenue import (
    SegmentRevenueAttempt,
    SegmentRevenueFailureReason,
    SegmentRevenueMethod,
    SegmentRevenueObservation,
    SegmentRevenueResolution,
    SegmentRevenueStatus,
    resolve_segment_revenue,
)

__all__ = [
    "BasicEarningsMetricType",
    "ObservedEarningsMetric",
    "extract_basic_earnings_records",
    "EarningsEvidenceBundle",
    "EarningsSourcePriority",
    "IrReleaseRecord",
    "IrReleaseSource",
    "reconcile_sec_ir_evidence",
    "SegmentClassificationRole",
    "SegmentHistoryChange",
    "SegmentHistoryEdge",
    "SegmentIdentityHistory",
    "SegmentIdentityVersion",
    "resolve_segment_version",
    "SegmentRevenueAttempt",
    "SegmentRevenueFailureReason",
    "SegmentRevenueMethod",
    "SegmentRevenueObservation",
    "SegmentRevenueResolution",
    "SegmentRevenueStatus",
    "resolve_segment_revenue",
]
