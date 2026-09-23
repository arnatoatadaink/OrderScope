import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

type DryRunPacket = {
  schemaVersion: "l1-003-pb04-local-evidence-dry-run-v1";
  remoteMutation: false;
  campaignId: string;
  recoveryId: string;
  localEvidence: {
    marketDate: string;
    contentSha256: string;
    providerRevision: string;
    bars: number;
    denseSession: boolean;
    reproducible?: boolean;
  };
  checkpointBefore: { completeThrough: string; version: number };
  session: { opensAt: string; closesAt: string; calendarRevision: string };
  chunks: readonly {
    ordinal: number;
    jobId: string;
    requestedRange: { startInclusive: string; endExclusive: string };
    expectedGridBars: number;
    localProviderBars: number;
    acknowledgedAbsent: number;
    checkpointBefore: { completeThrough: string; version: number };
    checkpointAfter: { completeThrough: string; version: number };
  }[];
};

function argValue(argv: readonly string[], name: string): string | undefined {
  const index = argv.indexOf(name);
  return index >= 0 ? argv[index + 1] : undefined;
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  const dryRunPath = argValue(argv, "--dry-run");
  const output = argValue(argv, "--output");
  const remoteVersionRaw = argValue(argv, "--remote-checkpoint-version");
  const remoteThrough = argValue(argv, "--remote-checkpoint-through");

  if (!dryRunPath || !output || !remoteVersionRaw || !remoteThrough) {
    throw new Error("required: --dry-run <json> --remote-checkpoint-version <n> --remote-checkpoint-through <iso> --output <json>");
  }

  const remoteVersion = Number(remoteVersionRaw);
  if (!Number.isSafeInteger(remoteVersion) || remoteVersion < 0) {
    throw new Error("--remote-checkpoint-version must be a non-negative integer");
  }
  if (new Date(remoteThrough).toISOString() !== remoteThrough) {
    throw new Error("--remote-checkpoint-through must be canonical UTC");
  }

  const packet = JSON.parse(await readFile(resolve(dryRunPath), "utf8")) as DryRunPacket;
  if (packet.schemaVersion !== "l1-003-pb04-local-evidence-dry-run-v1" || packet.remoteMutation !== false) {
    throw new Error("unsupported PB-04 dry-run packet");
  }
  if (packet.checkpointBefore.version !== remoteVersion
    || packet.checkpointBefore.completeThrough !== remoteThrough) {
    throw new Error("remote checkpoint does not match the accepted dry-run packet; regenerate before mutation");
  }
  if (packet.chunks.length !== 4
    || packet.chunks.reduce((sum, chunk) => sum + chunk.expectedGridBars, 0) !== 390) {
    throw new Error("PB-04 execution packet requires one four-chunk / 390-grid-bar session");
  }

  const executionPacket = {
    schemaVersion: "l1-003-pb04-remote-execution-packet-v1",
    generatedAt: new Date().toISOString(),
    authorized: false,
    remoteMutationPerformed: false,
    environment: "live-canary",
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    source: {
      kind: "local-provider-evidence",
      marketDate: packet.localEvidence.marketDate,
      contentSha256: packet.localEvidence.contentSha256,
      providerRevision: packet.localEvidence.providerRevision,
      bars: packet.localEvidence.bars,
      denseSession: packet.localEvidence.denseSession,
      ...(packet.localEvidence.reproducible === undefined ? {} : { reproducible: packet.localEvidence.reproducible }),
    },
    frozenRemoteCheckpoint: {
      version: remoteVersion,
      completeThrough: remoteThrough,
      requiredState: "COMPLETE",
      requiredMissingRanges: [],
      requiredBlocker: null,
    },
    campaignId: packet.campaignId.replace("-LOCAL-DRYRUN", "-REMOTE"),
    recoveryId: packet.recoveryId,
    session: packet.session,
    chunks: packet.chunks,
    mandatoryEntryChecks: [
      "D1 control read PASS",
      "checkpoint identity exactly matches frozenRemoteCheckpoint",
      "checkpoint state COMPLETE",
      "missing_ranges_json = []",
      "blocker_json IS NULL",
      "Worker mode shadow",
      "News disabled",
      "historical recovery gate disabled before opening the change window",
      "temporary historical control secret absent before opening the change window",
      "local evidence SHA-256 matches source.contentSha256",
    ],
    stopAfterEachChunkUnless: [
      "response accepted=true and SUCCEEDED",
      "inserted + matched equals localProviderBars",
      "acknowledgedAbsent equals chunk acknowledgedAbsent when non-zero",
      "conflicts=0, rejected=0, missing=0",
      "checkpoint advances exactly to checkpointAfter",
      "checkpoint remains COMPLETE with no missing ranges or blocker",
      "exactly one successful attempt for the frozen job",
      "persisted canonical bars equal localProviderBars",
      "no unexpected checkpoint movement",
    ],
    closeout: [
      "disable historical recovery gate",
      "delete temporary control secret",
      "verify endpoint returns 404",
      "verify Worker remains shadow",
      "verify News remains disabled",
      "perform final read-only checkpoint and accepted-record inspection",
    ],
  };

  await writeFile(resolve(output), JSON.stringify(executionPacket, null, 2) + "\n", "utf8");
  console.log("packet: " + resolve(output));
  console.log("PB-04 remote execution packet: FROZEN / NOT AUTHORIZED / remoteMutationPerformed=false");
}

await main();
