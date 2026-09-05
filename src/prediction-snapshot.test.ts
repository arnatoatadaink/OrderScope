import assert from "node:assert/strict";
import test from "node:test";
import {
  buildPredictionSnapshot,
  InMemoryPredictionSnapshotHandoffPort,
  type PredictionSnapshotBuildRequest,
} from "./prediction-snapshot.ts";
import type { PredictionInputRegistry } from "./prediction.ts";

const registry: PredictionInputRegistry = {
  revision: "prediction-input:snapshot-test-v1", market: "JAPAN_EQUITIES", generatedAt: "2026-08-31T00:00:00.000Z",
  instruments: [{ instrumentId: "tse:fixture-1", displaySymbol: "0001", providerSymbolMappings: { fixture: "0001" },
    exchange: "TSE", themes: ["Fixture"], baseCadence: "1Min", enabled: true, validFrom: "2026-08-01" },
  { instrumentId: "tse:disabled", displaySymbol: "0002", providerSymbolMappings: { fixture: "0002" },
    exchange: "TSE", themes: ["Fixture"], baseCadence: "1Min", enabled: false, validFrom: "2026-08-01" }],
};

const base: PredictionSnapshotBuildRequest = {
  schemaRevision: "jp-input-snapshot-v1", inputRegistry: registry, inputRegistryRevision: registry.revision,
  japanMarketDate: "2026-09-01", featureCutoff: "2026-09-01T06:30:00.000Z",
  generatedAt: "2026-09-01T06:31:00.000Z", calendarRevision: "jpx:fixture-v1",
  sessions: [{ segment: "MORNING", opensAt: "2026-09-01T00:00:00.000Z", closesAt: "2026-09-01T02:30:00.000Z" },
    { segment: "AFTERNOON", opensAt: "2026-09-01T03:30:00.000Z", closesAt: "2026-09-01T06:30:00.000Z" }],
  observations: [{ instrumentId: "tse:fixture-1", cadence: "1Min", market: "JAPAN_EQUITIES", sessionSegment: "AFTERNOON",
    eventTime: "2026-09-01T06:29:00.000Z", retrievedAt: "2026-09-01T06:29:10.000Z", availableAt: "2026-09-01T06:29:10.000Z",
    open: 100, high: 103, low: 99, close: 102, volume: 50, provider: "fixture", sourceReference: "opaque-ref", logicalDataVariant: "fixture:raw" }],
};

test("builds a valid immutable snapshot with stable canonical identity", () => {
  const first = buildPredictionSnapshot(base);
  const second = buildPredictionSnapshot({ ...base, observations: [...base.observations].reverse() });
  assert.equal(first.coverageState, "COMPLETE");
  assert.equal(first.snapshotId, second.snapshotId);
  assert.equal(first.contentHash, second.contentHash);
  assert.throws(() => { (first.observations as Array<unknown>).push({}); }, /not extensible/);
  assert.equal("providerPayload" in first.observations[0]!, false);
  assert.notEqual(first.contentHash, buildPredictionSnapshot({ ...base, observations: [{ ...base.observations[0]!, close: 101 }] }).contentHash);
});

test("fails closed for registry mismatch and records unknown, disabled, duplicate, and malformed observations", () => {
  assert.throws(() => buildPredictionSnapshot({ ...base, inputRegistryRevision: "wrong" }), /registry revision mismatch/);
  const snapshot = buildPredictionSnapshot({ ...base, observations: [...base.observations,
    { ...base.observations[0]!, instrumentId: "tse:unknown" },
    { ...base.observations[0]!, instrumentId: "tse:disabled" },
    { ...base.observations[0]! },
    { ...base.observations[0]!, eventTime: "2026-09-01T06:31:00.000Z" },
  ] });
  assert.deepEqual(snapshot.rejectedObservations.map((item) => item.code), ["DISABLED_INSTRUMENT", "DUPLICATE_OBSERVATION", "FUTURE_EVENT_TIME", "UNKNOWN_INSTRUMENT"]);
  assert.equal(snapshot.coverageState, "PARTIAL");
});

test("excludes late retrieval and availability, missing coverage, and the lunch break", () => {
  const lateRetrieved = buildPredictionSnapshot({ ...base, observations: [{ ...base.observations[0]!, retrievedAt: "2026-09-01T06:30:01.000Z" }] });
  assert.equal(lateRetrieved.coverageState, "BLOCKED");
  assert.deepEqual(lateRetrieved.reasonCodes, ["MISSING_INPUT", "PARTIAL_COVERAGE", "RETRIEVED_AFTER_CUTOFF"]);
  const lateAvailable = buildPredictionSnapshot({ ...base, observations: [{ ...base.observations[0]!, availableAt: "2026-09-01T06:30:01.000Z" }] });
  assert.equal(lateAvailable.rejectedObservations[0]?.code, "AVAILABLE_AFTER_CUTOFF");
  const lunch = buildPredictionSnapshot({ ...base, observations: [{ ...base.observations[0]!, sessionSegment: "MORNING", eventTime: "2026-09-01T02:30:00.000Z" }] });
  assert.equal(lunch.rejectedObservations[0]?.code, "OUTSIDE_SESSION_SEGMENT");
});

test("uses an injectable in-memory handoff port without changing snapshots", async () => {
  const snapshot = buildPredictionSnapshot(base);
  const port = new InMemoryPredictionSnapshotHandoffPort();
  await port.write(snapshot);
  assert.equal(await port.read(snapshot.snapshotId), snapshot);
});
