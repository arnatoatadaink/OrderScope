import type { StoredCoverageCheckpoint } from "./checkpoint";

export type Pb08ReproducibleAbsenceSpec = {
  coverageKey: string;
  symbol: "AMD" | "QQQ";
  expectedVersion: number;
  expectedCompleteThrough: string;
  expectedSourceObservedThrough: string;
  missingStart: string;
  missingEnd: string;
};

export const PB08_REPRODUCIBLE_ABSENCES: readonly Pb08ReproducibleAbsenceSpec[] = [
  {
    coverageKey: "AMD|1Min|REGULAR|stock:iex:raw",
    symbol: "AMD",
    expectedVersion: 42,
    expectedCompleteThrough: "2026-09-24T14:49:00.000Z",
    expectedSourceObservedThrough: "2026-09-24T14:50:00.000Z",
    missingStart: "2026-09-24T14:49:00.000Z",
    missingEnd: "2026-09-24T14:50:00.000Z",
  },
  {
    coverageKey: "QQQ|1Min|REGULAR|stock:iex:raw",
    symbol: "QQQ",
    expectedVersion: 11,
    expectedCompleteThrough: "2026-09-24T14:32:00.000Z",
    expectedSourceObservedThrough: "2026-09-24T14:33:00.000Z",
    missingStart: "2026-09-24T14:32:00.000Z",
    missingEnd: "2026-09-24T14:33:00.000Z",
  },
] as const;

export function matchesPb08ReproducibleAbsence(
  checkpoint: StoredCoverageCheckpoint,
  spec: Pb08ReproducibleAbsenceSpec,
): boolean {
  return checkpoint.coverageKey === spec.coverageKey
    && checkpoint.symbol === spec.symbol
    && checkpoint.interval === "1Min"
    && checkpoint.sessionScope === "REGULAR"
    && checkpoint.logicalDataVariant === "stock:iex:raw"
    && checkpoint.version === spec.expectedVersion
    && checkpoint.completeThrough === spec.expectedCompleteThrough
    && checkpoint.sourceObservedThrough === spec.expectedSourceObservedThrough
    && checkpoint.state === "PARTIAL"
    && checkpoint.blocker === undefined
    && checkpoint.missingRanges.length === 1
    && checkpoint.missingRanges[0]?.startInclusive === spec.missingStart
    && checkpoint.missingRanges[0]?.endExclusive === spec.missingEnd;
}

export function acknowledgedPb08Checkpoint(
  checkpoint: StoredCoverageCheckpoint,
  spec: Pb08ReproducibleAbsenceSpec,
  acknowledgedAt: string,
): StoredCoverageCheckpoint {
  if (!matchesPb08ReproducibleAbsence(checkpoint, spec)) {
    throw new Error(`PB-08 reproducible absence checkpoint mismatch: ${spec.symbol}`);
  }
  const at = Date.parse(acknowledgedAt);
  if (!Number.isFinite(at) || new Date(at).toISOString() !== acknowledgedAt) {
    throw new Error("acknowledgedAt must be a canonical UTC instant");
  }
  return {
    ...checkpoint,
    completeThrough: spec.expectedSourceObservedThrough,
    state: "COMPLETE",
    missingRanges: [],
    lastSuccessAt: acknowledgedAt,
    retryNotBefore: undefined,
    blocker: undefined,
  };
}
