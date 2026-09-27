import { PB08_REPRODUCIBLE_ABSENCES } from "./pb08-reproducible-absence";

type AckRow = {
  coverage_key: string;
  version: number;
};

export async function acknowledgePb08ReproducibleAbsencesD1(
  db: D1Database,
  acknowledgedAt: string,
): Promise<readonly AckRow[]> {
  const at = Date.parse(acknowledgedAt);
  if (!Number.isFinite(at) || new Date(at).toISOString() !== acknowledgedAt) {
    throw new Error("acknowledgedAt must be a canonical UTC instant");
  }
  const [amd, qqq] = PB08_REPRODUCIBLE_ABSENCES;
  if (!amd || !qqq) throw new Error("PB-08 absence specification is incomplete");

  const result = await db.prepare(`
    WITH eligible AS (
      SELECT coverage_key
      FROM coverage_checkpoint
      WHERE
        (
          coverage_key = ?
          AND version = ?
          AND complete_through = ?
          AND source_observed_through = ?
          AND state = 'PARTIAL'
          AND missing_ranges_json = ?
          AND blocker_json IS NULL
        )
        OR
        (
          coverage_key = ?
          AND version = ?
          AND complete_through = ?
          AND source_observed_through = ?
          AND state = 'PARTIAL'
          AND missing_ranges_json = ?
          AND blocker_json IS NULL
        )
    )
    UPDATE coverage_checkpoint
    SET
      complete_through = source_observed_through,
      state = 'COMPLETE',
      missing_ranges_json = '[]',
      last_success_at = ?,
      retry_not_before = NULL,
      blocker_json = NULL,
      version = version + 1
    WHERE coverage_key IN (?, ?)
      AND (SELECT COUNT(*) FROM eligible) = 2
      AND coverage_key IN (SELECT coverage_key FROM eligible)
    RETURNING coverage_key, version
  `).bind(
    amd.coverageKey,
    amd.expectedVersion,
    amd.expectedCompleteThrough,
    amd.expectedSourceObservedThrough,
    JSON.stringify([{ startInclusive: amd.missingStart, endExclusive: amd.missingEnd }]),
    qqq.coverageKey,
    qqq.expectedVersion,
    qqq.expectedCompleteThrough,
    qqq.expectedSourceObservedThrough,
    JSON.stringify([{ startInclusive: qqq.missingStart, endExclusive: qqq.missingEnd }]),
    acknowledgedAt,
    amd.coverageKey,
    qqq.coverageKey,
  ).all<AckRow>();

  if (result.results.length !== 2) return [];
  return [...result.results].sort((a, b) => a.coverage_key.localeCompare(b.coverage_key));
}
