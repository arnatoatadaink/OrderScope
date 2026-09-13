import type { Cadence } from "./universe.ts";
import type { PredictionInputRegistry } from "./prediction.ts";

export type JapanSessionSegment = "MORNING" | "AFTERNOON";
export type SnapshotCoverageState = "COMPLETE" | "PARTIAL" | "UNKNOWN" | "BLOCKED";
export type SnapshotReasonCode =
  | "MISSING_INPUT"
  | "PARTIAL_COVERAGE"
  | "DUPLICATE_OBSERVATION"
  | "UNKNOWN_INSTRUMENT"
  | "DISABLED_INSTRUMENT"
  | "REGISTRY_REVISION_MISMATCH"
  | "MALFORMED_OBSERVATION"
  | "FUTURE_EVENT_TIME"
  | "RETRIEVED_AFTER_CUTOFF"
  | "AVAILABLE_AFTER_CUTOFF"
  | "OUTSIDE_SESSION_SEGMENT";

export type JapanSessionWindow = Readonly<{
  segment: JapanSessionSegment;
  opensAt: string;
  closesAt: string;
}>;

export type PredictionSnapshotObservation = Readonly<{
  instrumentId: string;
  cadence: Cadence;
  market: "JAPAN_EQUITIES";
  sessionSegment: JapanSessionSegment;
  eventTime: string;
  retrievedAt: string;
  availableAt: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  tradeCount?: number;
  vwap?: number;
  provider: string;
  sourceReference: string;
  logicalDataVariant: string;
}>;

export type RejectedSnapshotObservation = Readonly<{
  instrumentId?: string;
  eventTime?: string;
  code: Exclude<SnapshotReasonCode, "MISSING_INPUT" | "PARTIAL_COVERAGE" | "REGISTRY_REVISION_MISMATCH">;
}>;

export type ImmutablePredictionSnapshot = Readonly<{
  snapshotId: string;
  contentHash: string;
  schemaRevision: string;
  inputRegistryRevision: string;
  japanMarketDate: string;
  featureCutoff: string;
  generatedAt: string;
  calendarRevision: string;
  observations: readonly PredictionSnapshotObservation[];
  rejectedObservations: readonly RejectedSnapshotObservation[];
  missingInputs: readonly string[];
  reasonCodes: readonly SnapshotReasonCode[];
  coverageState: SnapshotCoverageState;
}>;

export type PredictionSnapshotBuildRequest = Readonly<{
  schemaRevision: string;
  inputRegistry: PredictionInputRegistry;
  inputRegistryRevision: string;
  japanMarketDate: string;
  featureCutoff: string;
  generatedAt: string;
  calendarRevision: string;
  sessions: readonly JapanSessionWindow[];
  observations: readonly PredictionSnapshotObservation[];
}>;

export interface PredictionSnapshotHandoffPort {
  write(snapshot: ImmutablePredictionSnapshot): Promise<void>;
  read(snapshotId: string): Promise<ImmutablePredictionSnapshot | undefined>;
}

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const CADENCE_MS: Record<Cadence, number> = { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 };

function parseInstant(value: string, name: string): number {
  const result = Date.parse(value);
  if (!Number.isFinite(result)) throw new Error(`${name} must be a valid instant`);
  return result;
}

function assertDate(value: string, name: string): void {
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (!DATE_PATTERN.test(value) || Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    throw new Error(`${name} must be a valid YYYY-MM-DD date`);
  }
}

function stableHash(value: string): string {
  let hash = 0xcbf29ce484222325n;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= BigInt(value.charCodeAt(index));
    hash = BigInt.asUintN(64, hash * 0x100000001b3n);
  }
  return hash.toString(16).padStart(16, "0");
}

function freeze<T>(value: T): T {
  if (value && typeof value === "object") {
    for (const child of Object.values(value as Record<string, unknown>)) freeze(child);
    Object.freeze(value);
  }
  return value;
}

function canonicalObservation(value: PredictionSnapshotObservation): readonly unknown[] {
  return [value.instrumentId, value.cadence, value.market, value.sessionSegment, value.eventTime,
    value.retrievedAt, value.availableAt, value.open, value.high, value.low, value.close, value.volume,
    value.tradeCount ?? null, value.vwap ?? null, value.provider, value.sourceReference, value.logicalDataVariant];
}

function observationIdentity(value: PredictionSnapshotObservation): string {
  return [value.instrumentId, value.cadence, value.sessionSegment, value.eventTime, value.logicalDataVariant].join("|");
}

function invalidObservation(value: PredictionSnapshotObservation, cutoff: number, sessions: readonly JapanSessionWindow[]): RejectedSnapshotObservation | undefined {
  const eventTime = parseInstant(value.eventTime, "observation eventTime");
  const retrievedAt = parseInstant(value.retrievedAt, "observation retrievedAt");
  const availableAt = parseInstant(value.availableAt, "observation availableAt");
  if (eventTime > cutoff) return { instrumentId: value.instrumentId, eventTime: value.eventTime, code: "FUTURE_EVENT_TIME" };
  if (retrievedAt > cutoff) return { instrumentId: value.instrumentId, eventTime: value.eventTime, code: "RETRIEVED_AFTER_CUTOFF" };
  if (availableAt > cutoff) return { instrumentId: value.instrumentId, eventTime: value.eventTime, code: "AVAILABLE_AFTER_CUTOFF" };
  if (![value.open, value.high, value.low, value.close, value.volume].every(Number.isFinite)
    || value.open < 0 || value.high < Math.max(value.open, value.open, value.low, value.close)
    || value.low > Math.min(value.open, value.high, value.close) || value.volume < 0
    || (value.tradeCount !== undefined && (!Number.isSafeInteger(value.tradeCount) || value.tradeCount < 0))
    || (value.vwap !== undefined && (!Number.isFinite(value.vwap) || value.vwap < 0))) {
    return { instrumentId: value.instrumentId, eventTime: value.eventTime, code: "MALFORMED_OBSERVATION" };
  }
  const segment = sessions.find((item) => item.segment === value.sessionSegment);
  if (!segment || eventTime < parseInstant(segment.opensAt, "session opensAt")
    || eventTime >= parseInstant(segment.closesAt, "session closesAt")
    || (eventTime - parseInstant(segment.opensAt, "session opensAt")) % CADENCE_MS[value.cadence] !== 0) {
    return { instrumentId: value.instrumentId, eventTime: value.eventTime, code: "OUTSIDE_SESSION_SEGMENT" };
  }
}

export function buildPredictionSnapshot(request: PredictionSnapshotBuildRequest): ImmutablePredictionSnapshot {
  if (request.inputRegistry.revision !== request.inputRegistryRevision) {
    throw new Error("input registry revision mismatch");
  }
  if (!request.schemaRevision.trim() || !request.calendarRevision.trim()) throw new Error("snapshot revisions must be non-empty");
  assertDate(request.japanMarketDate, "japanMarketDate");
  const cutoff = parseInstant(request.featureCutoff, "featureCutoff");
  if (parseInstant(request.generatedAt, "generatedAt") < cutoff) throw new Error("generatedAt must not precede featureCutoff");
  const enabled = new Map(request.inputRegistry.instruments.filter((item) => item.enabled).map((item) => [item.instrumentId, item]));
  const known = new Map(request.inputRegistry.instruments.map((item) => [item.instrumentId, item]));
  const rejected: RejectedSnapshotObservation[] = [];
  const accepted: PredictionSnapshotObservation[] = [];
  const seen = new Set<string>();
  for (const observation of request.observations) {
    if (!known.has(observation.instrumentId)) { rejected.push({ instrumentId: observation.instrumentId, eventTime: observation.eventTime, code: "UNKNOWN_INSTRUMENT" }); continue; }
    if (!enabled.has(observation.instrumentId)) { rejected.push({ instrumentId: observation.instrumentId, eventTime: observation.eventTime, code: "DISABLED_INSTRUMENT" }); continue; }
    if (enabled.get(observation.instrumentId)!.baseCadence !== observation.cadence || observation.market !== "JAPAN_EQUITIES"
      || !observation.provider.trim() || !observation.sourceReference.trim() || !observation.logicalDataVariant.trim()) {
      rejected.push({ instrumentId: observation.instrumentId, eventTime: observation.eventTime, code: "MALFORMED_OBSERVATION" }); continue;
    }
    const identity = observationIdentity(observation);
    if (seen.has(identity)) { rejected.push({ instrumentId: observation.instrumentId, eventTime: observation.eventTime, code: "DUPLICATE_OBSERVATION" }); continue; }
    seen.add(identity);
    const invalid = invalidObservation(observation, cutoff, request.sessions);
    if (invalid) rejected.push(invalid); else accepted.push({ ...observation });
  }
  accepted.sort((left, right) => observationIdentity(left).localeCompare(observationIdentity(right)));
  rejected.sort((left, right) => `${left.code}|${left.instrumentId ?? ""}|${left.eventTime ?? ""}`.localeCompare(`${right.code}|${right.instrumentId ?? ""}|${right.eventTime ?? ""}`));
  const observed = new Set(accepted.map((item) => item.instrumentId));
  const missingInputs = [...enabled.keys()].filter((id) => !observed.has(id)).sort();
  const rejectedCodes = rejected.map((item) => item.code);
  const reasonCodes: SnapshotReasonCode[] = [...new Set([
    ...(missingInputs.length ? ["MISSING_INPUT", "PARTIAL_COVERAGE"] as SnapshotReasonCode[] : []),
    ...rejectedCodes,
  ])].sort() as SnapshotReasonCode[];
  const coverageState: SnapshotCoverageState = accepted.length === 0 && (missingInputs.length > 0 || rejected.length > 0)
    ? "BLOCKED" : reasonCodes.length > 0 ? "PARTIAL" : "COMPLETE";
  const canonical = JSON.stringify([request.schemaRevision, request.inputRegistryRevision, request.japanMarketDate,
    request.featureCutoff, request.generatedAt, request.calendarRevision, accepted.map(canonicalObservation), rejected,
    missingInputs, reasonCodes, coverageState]);
  const contentHash = stableHash(canonical);
  return freeze({ snapshotId: `jp-input:${request.schemaRevision}:${contentHash}`, contentHash,
    schemaRevision: request.schemaRevision, inputRegistryRevision: request.inputRegistryRevision,
    japanMarketDate: request.japanMarketDate, featureCutoff: request.featureCutoff, generatedAt: request.generatedAt,
    calendarRevision: request.calendarRevision, observations: accepted, rejectedObservations: rejected, missingInputs,
    reasonCodes, coverageState });
}

export class InMemoryPredictionSnapshotHandoffPort implements PredictionSnapshotHandoffPort {
  private readonly snapshots = new Map<string, ImmutablePredictionSnapshot>();
  async write(snapshot: ImmutablePredictionSnapshot): Promise<void> {
    const existing = this.snapshots.get(snapshot.snapshotId);
    if (existing && existing.contentHash !== snapshot.contentHash) throw new Error("snapshot identity conflicts with different content");
    this.snapshots.set(snapshot.snapshotId, snapshot);
  }
  async read(snapshotId: string): Promise<ImmutablePredictionSnapshot | undefined> { return this.snapshots.get(snapshotId); }
}
