export const LATEST_DIGEST_KEY = "market";
export const DIGEST_SCHEMA_VERSION = 1;
export const DIGEST_HISTORY_RETENTION = 96;
export const DIGEST_HISTORY_DEFAULT_LIMIT = 20;
export const DIGEST_HISTORY_MAX_LIMIT = 100;

export type StoredDigest<T extends Readonly<Record<string, unknown>>> = {
  digestKey: string;
  generatedAt: string;
  schemaVersion: number;
  payload: T;
};

type DigestRow = { digest_key: string; generated_at: string; payload_json: string; schema_version: number };

function validInstant(value: string): boolean { return Number.isFinite(Date.parse(value)); }

function parsePayload(value: string): Readonly<Record<string, unknown>> {
  const parsed: unknown = JSON.parse(value);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("latest_digest payload_json is corrupt");
  }
  return Object.fromEntries(Object.entries(parsed));
}

export class D1LatestDigestStore {
  private readonly db: D1Database;

  constructor(db: D1Database) {
    this.db = db;
  }

  async put<T extends Readonly<Record<string, unknown>>>(digestKey: string, generatedAt: string, payload: T): Promise<void> {
    if (!digestKey) throw new Error("digestKey must be non-empty");
    if (!validInstant(generatedAt)) throw new Error("generatedAt must be a valid instant");
    const payloadJson = JSON.stringify(payload);
    await this.db.batch([
      this.db.prepare(`
      INSERT INTO latest_digest (digest_key, generated_at, payload_json, schema_version)
      VALUES (?, ?, ?, ?)
      ON CONFLICT(digest_key) DO UPDATE SET
        generated_at = excluded.generated_at,
        payload_json = excluded.payload_json,
        schema_version = excluded.schema_version
      WHERE excluded.generated_at >= latest_digest.generated_at
      `).bind(digestKey, generatedAt, payloadJson, DIGEST_SCHEMA_VERSION),
      this.db.prepare(`
        INSERT INTO digest_history (digest_key, generated_at, payload_json, schema_version)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(digest_key, generated_at) DO UPDATE SET
          payload_json = excluded.payload_json,
          schema_version = excluded.schema_version
      `).bind(digestKey, generatedAt, payloadJson, DIGEST_SCHEMA_VERSION),
      this.db.prepare(`
        DELETE FROM digest_history
        WHERE digest_key = ? AND generated_at NOT IN (
          SELECT generated_at FROM digest_history
          WHERE digest_key = ?
          ORDER BY generated_at DESC
          LIMIT ?
        )
      `).bind(digestKey, digestKey, DIGEST_HISTORY_RETENTION),
    ]);
  }

  async get<T extends Readonly<Record<string, unknown>> = Readonly<Record<string, unknown>>>(digestKey: string): Promise<StoredDigest<T> | undefined> {
    if (!digestKey) throw new Error("digestKey must be non-empty");
    const row = await this.db.prepare(`
      SELECT digest_key, generated_at, payload_json, schema_version
      FROM latest_digest WHERE digest_key = ?
    `).bind(digestKey).first<DigestRow>();
    if (!row) return undefined;
    if (!validInstant(row.generated_at) || row.schema_version !== DIGEST_SCHEMA_VERSION) {
      throw new Error(`latest_digest row is corrupt: ${row.digest_key}`);
    }
    return { digestKey: row.digest_key, generatedAt: row.generated_at, schemaVersion: row.schema_version,
      payload: parsePayload(row.payload_json) as T };
  }

  async list<T extends Readonly<Record<string, unknown>> = Readonly<Record<string, unknown>>>(
    digestKey: string,
    limit = DIGEST_HISTORY_DEFAULT_LIMIT,
  ): Promise<Array<StoredDigest<T>>> {
    if (!digestKey) throw new Error("digestKey must be non-empty");
    if (!Number.isInteger(limit) || limit < 1 || limit > DIGEST_HISTORY_MAX_LIMIT) {
      throw new Error(`limit must be an integer from 1 to ${DIGEST_HISTORY_MAX_LIMIT}`);
    }
    const result = await this.db.prepare(`
      SELECT digest_key, generated_at, payload_json, schema_version
      FROM digest_history
      WHERE digest_key = ?
      ORDER BY generated_at DESC
      LIMIT ?
    `).bind(digestKey, limit).all<DigestRow>();
    return result.results.map((row) => {
      if (!validInstant(row.generated_at) || row.schema_version !== DIGEST_SCHEMA_VERSION) {
        throw new Error(`digest_history row is corrupt: ${row.digest_key}/${row.generated_at}`);
      }
      return { digestKey: row.digest_key, generatedAt: row.generated_at, schemaVersion: row.schema_version,
        payload: parsePayload(row.payload_json) as T };
    });
  }
}
