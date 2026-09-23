import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fetchHistoricalBars, type ProviderNeutralBar } from "../src/alpaca.ts";
import {
  L1_003_NVDA_DEFAULT_SESSIONS,
  planRegularSession,
  validateRegularSession,
} from "../src/local-history-collector.ts";
import type { UniverseInstrument } from "../src/universe.ts";

type Args = {
  sessions: string[];
  outputDir: string;
  dryPlan: boolean;
};

function parseArgs(argv: readonly string[]): Args {
  const sessions: string[] = [];
  let outputDir = "var/l1-003/local-market-recovery/nvda";
  let dryPlan = false;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--session") {
      const value = argv[index + 1];
      if (!value) throw new Error("--session requires YYYY-MM-DD");
      sessions.push(value);
      index += 1;
    } else if (arg === "--output-dir") {
      const value = argv[index + 1];
      if (!value) throw new Error("--output-dir requires a path");
      outputDir = value;
      index += 1;
    } else if (arg === "--dry-plan") {
      dryPlan = true;
    } else {
      throw new Error(`unsupported argument: ${arg}`);
    }
  }
  return {
    sessions: sessions.length > 0 ? sessions : [...L1_003_NVDA_DEFAULT_SESSIONS],
    outputDir,
    dryPlan,
  };
}

function credentialsFromEnv(): { keyId: string; secretKey: string } {
  const keyId = process.env.ALPACA_API_KEY?.trim();
  const secretKey = process.env.ALPACA_API_SECRET?.trim();
  if (!keyId || !secretKey) {
    throw new Error("ALPACA_API_KEY and ALPACA_API_SECRET are required");
  }
  return { keyId, secretKey };
}

async function fetchSession(
  instrument: UniverseInstrument,
  marketDate: string,
): Promise<{ plan: ReturnType<typeof planRegularSession>; bars: ProviderNeutralBar[]; pages: number }> {
  const plan = planRegularSession(marketDate);
  const credentials = credentialsFromEnv();
  const bars: ProviderNeutralBar[] = [];
  let pageToken: string | undefined;
  let pages = 0;

  do {
    const page = await fetchHistoricalBars(credentials, {
      instrument,
      startInclusive: plan.startInclusive,
      endExclusive: plan.endExclusive,
      feed: "iex",
      limit: 10_000,
      ...(pageToken ? { pageToken } : {}),
    }, {
      retry: {
        maxAttempts: 4,
        baseBackoffMs: 500,
        maxBackoffMs: 4_000,
        maxRetryAfterMs: 10_000,
      },
    });
    pages += 1;
    bars.push(...page.bars);
    pageToken = page.nextPageToken;
  } while (pageToken);

  bars.sort((left, right) => left.timestamp.localeCompare(right.timestamp));
  return { plan, bars, pages };
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const plans = args.sessions.map(planRegularSession);
  if (args.dryPlan) {
    process.stdout.write(JSON.stringify({
      symbol: "NVDA",
      cadence: "1Min",
      dataVariant: "stock:iex:raw",
      sessions: plans,
      expectedBars: plans.reduce((sum, plan) => sum + plan.expectedBars, 0),
      remoteMutation: false,
    }, null, 2) + "\n");
    return;
  }

  const instrument: UniverseInstrument = {
    symbol: "NVDA",
    cadence: "1Min",
    providerRoute: "alpaca_stock_bars",
  };
  const outputDir = resolve(args.outputDir);
  await mkdir(outputDir, { recursive: true });

  const sessionResults = [];
  let totalBars = 0;
  let totalPages = 0;
  let allComplete = true;

  for (const marketDate of args.sessions) {
    const { plan, bars, pages } = await fetchSession(instrument, marketDate);
    const validation = validateRegularSession(plan, bars);
    const sessionPath = resolve(outputDir, `NVDA_1Min_REGULAR_${marketDate}.json`);
    await writeFile(sessionPath, JSON.stringify({
      schemaVersion: "l1-003-local-history-session-v1",
      coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
      providerRevision: "alpaca-stock-bars-v1",
      feed: "iex",
      adjustment: "raw",
      plan,
      validation,
      pages,
      bars,
    }, null, 2) + "\n", "utf8");

    totalBars += bars.length;
    totalPages += pages;
    allComplete &&= validation.complete;
    sessionResults.push({
      marketDate,
      pages,
      bars: bars.length,
      complete: validation.complete,
      output: sessionPath,
    });
    console.log(`${marketDate}: bars=${bars.length} pages=${pages} complete=${validation.complete}`);
  }

  const manifest = {
    schemaVersion: "l1-003-local-history-manifest-v1",
    generatedAt: new Date().toISOString(),
    coverageKey: "NVDA|1Min|REGULAR|stock:iex:raw",
    remoteMutation: false,
    sessionCount: sessionResults.length,
    totalPages,
    totalBars,
    expectedBars: plans.reduce((sum, plan) => sum + plan.expectedBars, 0),
    complete: allComplete,
    sessions: sessionResults,
  };
  const manifestPath = resolve(outputDir, "manifest.json");
  await writeFile(manifestPath, JSON.stringify(manifest, null, 2) + "\n", "utf8");
  console.log(`manifest: ${manifestPath}`);
  console.log(`L1-003 local collection: ${allComplete ? "PASS" : "INCOMPLETE"}`);
  if (!allComplete) process.exitCode = 2;
}

await main();
