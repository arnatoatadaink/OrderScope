import type { BarNormalizationResult, NormalizedMarketBar } from "./bar";

export type BarProvenance = {
  idempotencyKey: string;
  jobId: string;
  retrievedAt: string;
};

export type BarAcceptanceOutcome = "INSERTED" | "MATCHED" | "CONFLICT" | "REJECTED";

export type BarAcceptanceResult = {
  identity?: string;
  outcome: BarAcceptanceOutcome;
  storedVersion?: number;
  acceptanceReceipt: string;
  reason?: string;
  provenanceAppended: boolean;
};

export interface NormalizedBarStore {
  accept(candidate: BarNormalizationResult, provenance: BarProvenance): Promise<BarAcceptanceResult>;
}

type ReceiptRow = {
  idempotency_key: string;
  request_fingerprint: string;
  identity_key: string | null;
  outcome: BarAcceptanceOutcome | null;
  reason: string | null;
  stored_version: number | null;
};

type StoredRow = { canonical_fingerprint: string; version: number };

function parseInstant(value: string, name: string): string {
  const time = Date.parse(value);
  if (!Number.isFinite(time)) throw new Error(`${name} must be a valid instant`);
  return new Date(time).toISOString();
}

function identityFor(bar: NormalizedMarketBar): string {
  return JSON.stringify([
    bar.instrumentId, bar.interval, bar.barStartUtc, bar.sessionKind, bar.logicalDataVariant,
  ]);
}

function semanticContent(bar: NormalizedMarketBar): Readonly<Record<string, unknown>> {
  return {
    open: bar.open, high: bar.high, low: bar.low, close: bar.close, volume: bar.volume,
    tradeCount: bar.tradeCount ?? null, vwap: bar.vwap ?? null,
    barEndUtc: bar.barEndUtc, marketDate: bar.marketDate, sessionKind: bar.sessionKind,
    logicalDataVariant: bar.logicalDataVariant,
  };
}

async function sha256(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function canonicalBarFingerprint(bar: NormalizedMarketBar): Promise<string> {
  return sha256(JSON.stringify(semanticContent(bar)));
}

function completedResult(row: ReceiptRow, appended: boolean): BarAcceptanceResult {
  if (!row.outcome) throw new Error("acceptance receipt is incomplete");
  return {
    identity: row.identity_key ?? undefined,
    outcome: row.outcome,
    storedVersion: row.stored_version ?? undefined,
    acceptanceReceipt: row.idempotency_key,
    reason: row.reason ?? undefined,
    provenanceAppended: appended,
  };
}

export class D1NormalizedBarStore implements NormalizedBarStore {
  private readonly db: D1Database;

  constructor(db: D1Database) {
    this.db = db;
  }

  async accept(candidate: BarNormalizationResult, provenance: BarProvenance): Promise<BarAcceptanceResult> {
    if (!provenance.idempotencyKey || !provenance.jobId) {
      throw new Error("acceptance provenance identity fields must be non-empty");
    }
    const retrievedAt = parseInstant(provenance.retrievedAt, "retrievedAt");
    const identity = candidate.outcome === "NORMALIZED" ? identityFor(candidate.bar) : undefined;
    const requestFingerprint = candidate.outcome === "NORMALIZED"
      ? await canonicalBarFingerprint(candidate.bar)
      : await sha256(JSON.stringify([candidate.code, candidate.reason]));
    const provider = candidate.outcome === "NORMALIZED" ? candidate.bar.provider : null;
    const sourceTimestamp = candidate.outcome === "NORMALIZED" ? candidate.bar.sourceTimestamp : null;

    const reserved = await this.db.prepare(`
      INSERT INTO bar_acceptance_receipt (
        idempotency_key, request_fingerprint, identity_key, provider, job_id,
        source_timestamp, retrieved_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(idempotency_key) DO NOTHING
      RETURNING idempotency_key, request_fingerprint, identity_key, outcome, reason, stored_version
    `).bind(
      provenance.idempotencyKey, requestFingerprint, identity ?? null, provider,
      provenance.jobId, sourceTimestamp, retrievedAt,
    ).first<ReceiptRow>();

    const existing = reserved ?? await this.db.prepare(`
      SELECT idempotency_key, request_fingerprint, identity_key, outcome, reason, stored_version
      FROM bar_acceptance_receipt WHERE idempotency_key = ?
    `).bind(provenance.idempotencyKey).first<ReceiptRow>();
    if (!existing) throw new Error("acceptance receipt reservation failed");
    if (existing.request_fingerprint !== requestFingerprint || existing.identity_key !== (identity ?? null)) {
      throw new Error("idempotencyKey is already associated with a different bar observation");
    }
    if (existing.outcome) return completedResult(existing, false);

    if (candidate.outcome === "REJECTED") {
      return this.completeReceipt(provenance.idempotencyKey, "REJECTED", undefined,
        `${candidate.code}: ${candidate.reason}`, reserved !== null);
    }

    const bar = candidate.bar;
    const inserted = await this.db.prepare(`
      INSERT INTO normalized_bar (
        identity_key, instrument_id, interval, bar_start_utc, bar_end_utc, market_date,
        session_kind, is_shortened_session, logical_data_variant, open, high, low, close,
        volume, trade_count, vwap, canonical_fingerprint, accepted_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(identity_key) DO NOTHING
      RETURNING canonical_fingerprint, version
    `).bind(
      identity, bar.instrumentId, bar.interval, bar.barStartUtc, bar.barEndUtc, bar.marketDate,
      bar.sessionKind, bar.isShortenedSession ? 1 : 0, bar.logicalDataVariant,
      bar.open, bar.high, bar.low, bar.close, bar.volume, bar.tradeCount ?? null, bar.vwap ?? null,
      requestFingerprint, retrievedAt,
    ).first<StoredRow>();
    const stored = inserted ?? await this.db.prepare(`
      SELECT canonical_fingerprint, version FROM normalized_bar WHERE identity_key = ?
    `).bind(identity).first<StoredRow>();
    if (!stored) throw new Error("canonical bar insert/read failed");

    if (stored.canonical_fingerprint === requestFingerprint) {
      return this.completeReceipt(provenance.idempotencyKey, inserted ? "INSERTED" : "MATCHED",
        stored.version, undefined, reserved !== null);
    }

    await this.db.prepare(`
      INSERT INTO bar_conflict (
        idempotency_key, identity_key, stored_fingerprint, observed_fingerprint,
        observed_content_json, detected_at
      ) VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(idempotency_key) DO NOTHING
    `).bind(
      provenance.idempotencyKey, identity, stored.canonical_fingerprint, requestFingerprint,
      JSON.stringify(semanticContent(bar)), retrievedAt,
    ).run();
    return this.completeReceipt(provenance.idempotencyKey, "CONFLICT", stored.version,
      "canonical identity already exists with different semantic content", reserved !== null);
  }

  private async completeReceipt(
    idempotencyKey: string,
    outcome: BarAcceptanceOutcome,
    storedVersion: number | undefined,
    reason: string | undefined,
    appended: boolean,
  ): Promise<BarAcceptanceResult> {
    const row = await this.db.prepare(`
      UPDATE bar_acceptance_receipt SET
        outcome = ?, stored_version = ?, reason = ?, completed_at = retrieved_at
      WHERE idempotency_key = ? AND outcome IS NULL
      RETURNING idempotency_key, request_fingerprint, identity_key, outcome, reason, stored_version
    `).bind(outcome, storedVersion ?? null, reason ?? null, idempotencyKey).first<ReceiptRow>()
      ?? await this.db.prepare(`
        SELECT idempotency_key, request_fingerprint, identity_key, outcome, reason, stored_version
        FROM bar_acceptance_receipt WHERE idempotency_key = ?
      `).bind(idempotencyKey).first<ReceiptRow>();
    if (!row) throw new Error("acceptance receipt completion failed");
    return completedResult(row, appended);
  }
}
