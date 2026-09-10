import { fetchHistoricalBars, type AlpacaCredentials, type HistoricalBarFetchOptions, type HistoricalBarRequest } from "./alpaca.ts";
import { normalizeMarketBar } from "./bar.ts";
import type { NormalizedBarStore } from "./bar-store";
import type { InvocationBudget } from "./invocation-budget";
import type { MarketCalendarSnapshot } from "./calendar";
import type { CoverageCheckpointPort, StoredCoverageCheckpoint } from "./checkpoint";
import type { AcquisitionJob, TimeRange } from "./schedule";

export type AcquisitionExecutionSummary = {
  jobId: string;
  outcome: "SUCCEEDED" | "PARTIAL" | "FAILED";
  pages: number;
  inserted: number;
  matched: number;
  conflicts: number;
  rejected: number;
  missing: number;
};

export type AcquisitionExecutorOptions = {
  credentials: AlpacaCredentials;
  calendar: MarketCalendarSnapshot;
  checkpoints: CoverageCheckpointPort;
  bars: NormalizedBarStore;
  feed: "iex" | "sip" | "delayed_sip";
  maxPages: number;
  maxBars: number;
  gapRetryDelayMs?: number;
  providerFetchOptions?: HistoricalBarFetchOptions;
  budget?: InvocationBudget;
  now?: () => Date;
  fetchPage?: (credentials: AlpacaCredentials, request: HistoricalBarRequest, options?: HistoricalBarFetchOptions) => ReturnType<typeof fetchHistoricalBars>;
};

type ExpectedBar = { identityStart: string; completesAt: string; range: TimeRange };
const INTERVAL_MS = { "1Min": 60_000, "15Min": 900_000, "1Day": 86_400_000 } as const;

function expectedBars(job: AcquisitionJob, calendar: MarketCalendarSnapshot): ExpectedBar[] {
  const instrument = job.instruments[0];
  if (!instrument) return [];
  const from = Date.parse(job.requestedRange.startInclusive);
  const to = Date.parse(job.requestedRange.endExclusive);
  const interval = INTERVAL_MS[instrument.cadence];
  const result: ExpectedBar[] = [];
  if (instrument.providerRoute === "alpaca_crypto_bars") {
    let start = Math.ceil(from / interval) * interval;
    while (start + interval <= to) {
      result.push({ identityStart: new Date(start).toISOString(), completesAt: new Date(start + interval).toISOString(),
        range: { startInclusive: new Date(start).toISOString(), endExclusive: new Date(start + interval).toISOString() } });
      start += interval;
    }
    return result;
  }
  for (const session of calendar.sessions.filter((candidate) => candidate.sessionKind === job.sessionScope)) {
    const open = Date.parse(session.opensAt);
    const close = Date.parse(session.closesAt);
    if (instrument.cadence === "1Day") {
      if (close > from && close <= to) result.push({ identityStart: session.opensAt, completesAt: session.closesAt,
        range: { startInclusive: session.opensAt, endExclusive: session.closesAt } });
      continue;
    }
    let start = open;
    while (start + interval <= close) {
      if (start >= from && start + interval <= to) result.push({
        identityStart: new Date(start).toISOString(), completesAt: new Date(start + interval).toISOString(),
        range: { startInclusive: new Date(start).toISOString(), endExclusive: new Date(start + interval).toISOString() },
      });
      start += interval;
    }
  }
  return result.sort((left, right) => left.completesAt.localeCompare(right.completesAt));
}

function mergeMissing(ranges: readonly TimeRange[]): TimeRange[] {
  const sorted = [...ranges].sort((a, b) => a.startInclusive.localeCompare(b.startInclusive));
  const merged: TimeRange[] = [];
  for (const range of sorted) {
    const last = merged.at(-1);
    if (last && range.startInclusive <= last.endExclusive) {
      last.endExclusive = range.endExclusive > last.endExclusive ? range.endExclusive : last.endExclusive;
    } else merged.push({ ...range });
  }
  return merged;
}

export async function executeAcquisitionJob(
  job: AcquisitionJob,
  options: AcquisitionExecutorOptions,
): Promise<AcquisitionExecutionSummary> {
  const instrument = job.instruments[0];
  const expectation = job.checkpointExpectations[0];
  if (!instrument || job.instruments.length !== 1 || !expectation) throw new Error("v0.1 executor requires one instrument and checkpoint per job");
  const now = options.now ?? (() => new Date());
  const fetchPage = options.fetchPage ?? fetchHistoricalBars;
  const attemptId = `${job.jobId}:attempt:${job.attempt}:${job.createdAt}`;
  const startedAt = now().toISOString();
  await options.checkpoints.recordAttempt({ attemptId, coverageKey: expectation.coverageKey, jobId: job.jobId, startedAt });
  const counts = { pages: 0, inserted: 0, matched: 0, conflicts: 0, rejected: 0 };
  const acceptedStarts = new Set<string>();
  let pageToken: string | undefined;
  const seenTokens = new Set<string>();
  try {
    do {
      if (counts.pages >= options.maxPages) throw new Error(`acquisition page limit exceeded: ${options.maxPages}`);
      // An injected adapter is charged once before invocation; if it implements
      // retry-attempt callbacks, its first callback corresponds to that prepaid
      // attempt and subsequent callbacks charge retries.
      const prepaidInjectedAttempt = options.fetchPage !== undefined;
      if (prepaidInjectedAttempt) options.budget?.consume("external");
      let reportedAttempts = 0;
      const providerFetchOptions = { ...options.providerFetchOptions,
        onAttempt: () => {
          reportedAttempts += 1;
          if (!(prepaidInjectedAttempt && reportedAttempts === 1)) options.budget?.consume("external");
          options.providerFetchOptions?.onAttempt?.();
        } };
      const page = await fetchPage(options.credentials, {
        instrument, ...job.requestedRange, pageToken, feed: options.feed,
      }, providerFetchOptions);
      counts.pages += 1;
      const acceptedCount = counts.inserted + counts.matched + counts.conflicts + counts.rejected;
      if (acceptedCount + page.bars.length > options.maxBars) {
        throw new Error(`acquisition bar limit exceeded: ${options.maxBars}`);
      }
      const acceptanceInputs = page.bars.map((rawBar, index) => ({
        candidate: normalizeMarketBar(rawBar, instrument, options.calendar, job.sessionScope),
        provenance: { idempotencyKey: `${attemptId}:page:${counts.pages}:bar:${index}`,
          jobId: job.jobId, retrievedAt: now().toISOString() },
      }));
      const receipts = options.bars.acceptBatch
        ? await options.bars.acceptBatch(acceptanceInputs)
        : await Promise.all(acceptanceInputs.map((input) => options.bars.accept(input.candidate, input.provenance)));
      if (receipts.length !== acceptanceInputs.length) throw new Error("bar acceptance result count mismatch");
      for (let index = 0; index < receipts.length; index += 1) {
        const normalized = acceptanceInputs[index]!.candidate;
        const receipt = receipts[index]!;
        if (receipt.outcome === "INSERTED" || receipt.outcome === "MATCHED") {
          counts[receipt.outcome === "INSERTED" ? "inserted" : "matched"] += 1;
          if (normalized.outcome === "NORMALIZED") acceptedStarts.add(normalized.bar.barStartUtc);
        } else counts[receipt.outcome === "CONFLICT" ? "conflicts" : "rejected"] += 1;
      }
      pageToken = page.nextPageToken;
      if (pageToken && seenTokens.has(pageToken)) throw new Error("provider repeated a pagination token");
      if (pageToken) seenTokens.add(pageToken);
    } while (pageToken);

    const expected = expectedBars(job, options.calendar);
    const existing = await options.checkpoints.get(expectation.coverageKey);
    const missing = expected.filter((bar) => (!existing?.completeThrough || bar.completesAt > existing.completeThrough)
      && !acceptedStarts.has(bar.identityStart));
    let completeThrough = existing?.completeThrough;
    for (const bar of expected) {
      if (completeThrough && bar.completesAt <= completeThrough) continue;
      if (!acceptedStarts.has(bar.identityStart)) break;
      completeThrough = bar.completesAt;
    }
    const finishedAt = now().toISOString();
    const state = missing.length === 0 ? "COMPLETE" : "PARTIAL";
    const proposed: StoredCoverageCheckpoint = {
      coverageKey: expectation.coverageKey, symbol: instrument.symbol, interval: instrument.cadence,
      sessionScope: job.sessionScope,
      logicalDataVariant: pageVariant(instrument.providerRoute, options.feed),
      completeThrough, state, missingRanges: mergeMissing(missing.map((bar) => bar.range)),
      lastSuccessAt: missing.length === 0 ? finishedAt : existing?.lastSuccessAt,
      lastAttemptAt: finishedAt, sourceObservedThrough: expected.at(-1)?.completesAt,
      retryNotBefore: missing.length > 0 && options.gapRetryDelayMs !== undefined
        ? new Date(Date.parse(finishedAt) + options.gapRetryDelayMs).toISOString()
        : undefined,
      universeRevision: job.universeRevision, version: existing?.version ?? 0,
    };
    const updated = await options.checkpoints.compareAndSet(existing?.version, proposed);
    if (updated.outcome === "VERSION_CONFLICT") throw new Error("checkpoint compare-and-set conflict");
    const outcome = missing.length || counts.conflicts || counts.rejected ? "PARTIAL" : "SUCCEEDED";
    await options.checkpoints.recordAttempt({ attemptId, coverageKey: expectation.coverageKey, jobId: job.jobId,
      startedAt, finishedAt, outcome, diagnostic: { ...counts, missing: missing.length } });
    return { jobId: job.jobId, outcome, ...counts, missing: missing.length };
  } catch (error) {
    await options.checkpoints.recordAttempt({ attemptId, coverageKey: expectation.coverageKey, jobId: job.jobId,
      startedAt, finishedAt: now().toISOString(), outcome: "FAILED",
      diagnostic: { message: error instanceof Error ? error.message : "unknown acquisition error" } });
    throw error;
  }
}

function pageVariant(route: string, feed: string): string {
  return route === "alpaca_crypto_bars" ? "crypto:us" : `stock:${feed}:raw`;
}
