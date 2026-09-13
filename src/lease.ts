export interface AcquisitionLeaseStore {
  acquire(coverageKey: string, ownerId: string, now: string, ttlMs: number): Promise<boolean>;
  release(coverageKey: string, ownerId: string): Promise<void>;
}

function instant(value: string, name: string): number {
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) throw new Error(`${name} must be a valid instant`);
  return parsed;
}

export class D1AcquisitionLeaseStore implements AcquisitionLeaseStore {
  constructor(private readonly db: D1Database) {}

  async acquire(coverageKey: string, ownerId: string, now: string, ttlMs: number): Promise<boolean> {
    if (!coverageKey || !ownerId) throw new Error("lease identity fields must be non-empty");
    const nowMs = instant(now, "lease now");
    if (!Number.isSafeInteger(ttlMs) || ttlMs < 1) throw new Error("lease ttlMs must be a positive integer");
    const expiresAt = new Date(nowMs + ttlMs).toISOString();
    const row = await this.db.prepare(`
      INSERT INTO acquisition_lease (coverage_key, owner_id, acquired_at, expires_at)
      VALUES (?, ?, ?, ?)
      ON CONFLICT(coverage_key) DO UPDATE SET
        owner_id = excluded.owner_id,
        acquired_at = excluded.acquired_at,
        expires_at = excluded.expires_at
      WHERE acquisition_lease.expires_at <= excluded.acquired_at
      RETURNING owner_id
    `).bind(coverageKey, ownerId, new Date(nowMs).toISOString(), expiresAt).first<{ owner_id: string }>();
    return row?.owner_id === ownerId;
  }

  async release(coverageKey: string, ownerId: string): Promise<void> {
    if (!coverageKey || !ownerId) throw new Error("lease identity fields must be non-empty");
    await this.db.prepare(
      "DELETE FROM acquisition_lease WHERE coverage_key = ? AND owner_id = ?",
    ).bind(coverageKey, ownerId).run();
  }
}
