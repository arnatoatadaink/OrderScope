import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { parseLocalHistoryEvidence } from "../src/local-history-evidence.ts";
import { buildLocalPb04DryRunPacket } from "../src/local-history-pb04.ts";

type Args = {
  session: string;
  inputDir: string;
  output?: string;
  checkpointVersion: number;
  checkpointThrough: string;
  calendarRevision: string;
  createdAt: string;
};

function parseArgs(argv: readonly string[]): Args {
  let session = "";
  let inputDir = "var/l1-003/local-market-recovery/nvda";
  let output: string | undefined;
  let checkpointVersion = 18;
  let checkpointThrough = "2026-09-08T20:00:00.000Z";
  let calendarRevision = "";
  let createdAt = new Date().toISOString();

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const value = argv[index + 1];
    if (arg === "--session") {
      if (!value) throw new Error("--session requires YYYY-MM-DD");
      session = value; index += 1;
    } else if (arg === "--input-dir") {
      if (!value) throw new Error("--input-dir requires a path");
      inputDir = value; index += 1;
    } else if (arg === "--output") {
      if (!value) throw new Error("--output requires a path");
      output = value; index += 1;
    } else if (arg === "--checkpoint-version") {
      if (!value) throw new Error("--checkpoint-version requires an integer");
      checkpointVersion = Number(value); index += 1;
    } else if (arg === "--checkpoint-through") {
      if (!value) throw new Error("--checkpoint-through requires an ISO timestamp");
      checkpointThrough = value; index += 1;
    } else if (arg === "--calendar-revision") {
      if (!value) throw new Error("--calendar-revision requires a value");
      calendarRevision = value; index += 1;
    } else if (arg === "--created-at") {
      if (!value) throw new Error("--created-at requires an ISO timestamp");
      createdAt = value; index += 1;
    } else {
      throw new Error("unsupported argument: " + arg);
    }
  }

  if (!session) throw new Error("--session is required");
  if (!Number.isSafeInteger(checkpointVersion) || checkpointVersion < 0) {
    throw new Error("--checkpoint-version must be a non-negative integer");
  }
  if (new Date(checkpointThrough).toISOString() !== checkpointThrough) {
    throw new Error("--checkpoint-through must be canonical UTC");
  }
  if (new Date(createdAt).toISOString() !== createdAt) {
    throw new Error("--created-at must be canonical UTC");
  }
  if (!calendarRevision) calendarRevision = "local-evidence:" + session;
  return { session, inputDir, output, checkpointVersion, checkpointThrough, calendarRevision, createdAt };
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const inputPath = resolve(args.inputDir, "NVDA_1Min_REGULAR_" + args.session + ".json");
  const loaded = await parseLocalHistoryEvidence(await readFile(inputPath, "utf8"));
  if (loaded.session.plan.marketDate !== args.session) {
    throw new Error("session argument does not match local evidence");
  }

  const checkpointBefore = {
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    symbol: "NVDA",
    interval: "1Min" as const,
    sessionScope: "REGULAR" as const,
    logicalDataVariant: "stock:iex:raw",
    state: "COMPLETE" as const,
    completeThrough: args.checkpointThrough,
    missingRanges: [],
    version: args.checkpointVersion,
    universeRevision: "stock-monitoring-canary-v0.1",
  };

  const packet = buildLocalPb04DryRunPacket({
    session: loaded.session,
    coverageAbsences: loaded.coverageAbsences,
    checkpointBefore,
    calendarRevision: args.calendarRevision,
    createdAt: args.createdAt,
  });

  const rendered = JSON.stringify(packet, null, 2) + "\n";
  if (args.output) {
    const outputPath = resolve(args.output);
    await writeFile(outputPath, rendered, "utf8");
    console.log("packet: " + outputPath);
  } else {
    process.stdout.write(rendered);
  }
  console.log("PB-04 local dry-run: PASS session=" + args.session + " chunks=" + packet.chunks.length + " remoteMutation=false");
}

await main();
