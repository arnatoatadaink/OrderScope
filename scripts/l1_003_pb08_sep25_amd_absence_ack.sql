-- PB-08 Sep25 AMD reproducible provider absence only.
-- Readiness is not authorization. Execute only after explicit window approval.
-- Reproduced twice at 2026-09-26T07:38:56Z: IEX AMD 15:33Z absent;
-- adjacent 15:32Z and 15:34Z present. Preserve previously inserted bars.
WITH frozen(coverage_key, version, complete_through, source_observed_through,
            state, missing_ranges_json, retry_not_before) AS (
  VALUES
  ('AMD|1Min|REGULAR|stock:iex:raw',45,'2026-09-25T15:33:00.000Z','2026-09-25T16:49:00.000Z','PARTIAL','[{"startInclusive":"2026-09-25T15:33:00.000Z","endExclusive":"2026-09-25T15:34:00.000Z"}]','2026-09-26T07:51:19.000Z'),
  ('NVDA|1Min|REGULAR|stock:iex:raw',62,'2026-09-25T15:10:00.000Z','2026-09-25T15:10:00.000Z','COMPLETE','[]',NULL),
  ('QQQ|1Min|REGULAR|stock:iex:raw',13,'2026-09-25T15:10:00.000Z','2026-09-25T15:10:00.000Z','COMPLETE','[]',NULL),
  ('SPY|1Min|REGULAR|stock:iex:raw',45,'2026-09-25T15:10:00.000Z','2026-09-25T15:10:00.000Z','COMPLETE','[]',NULL),
  ('BTCUSD|1Min|ALL_TRADING|crypto:us',52,'2026-09-25T12:31:00.000Z','2026-09-25T12:31:00.000Z','COMPLETE','[]',NULL)
), eligible AS (
  SELECT c.coverage_key FROM coverage_checkpoint c JOIN frozen f
  ON c.coverage_key=f.coverage_key AND c.version=f.version
  AND c.complete_through=f.complete_through
  AND c.source_observed_through=f.source_observed_through
  AND c.state=f.state AND c.missing_ranges_json=f.missing_ranges_json
  AND c.retry_not_before IS f.retry_not_before AND c.blocker_json IS NULL
)
UPDATE coverage_checkpoint
SET complete_through=source_observed_through, state='COMPLETE',
    missing_ranges_json='[]', retry_not_before=NULL, blocker_json=NULL,
    last_success_at=strftime('%Y-%m-%dT%H:%M:%fZ','now'), version=version+1
WHERE coverage_key='AMD|1Min|REGULAR|stock:iex:raw'
  AND (SELECT COUNT(*) FROM eligible)=5
  AND NOT EXISTS (
    SELECT 1 FROM acquisition_attempt
    WHERE coverage_key IN (SELECT coverage_key FROM frozen)
      AND finished_at IS NULL AND outcome IS NULL
  )
  AND julianday('now','-1440 minutes') <= julianday('2026-09-25T13:30:00.000Z')
RETURNING coverage_key,version,complete_through,state,missing_ranges_json;
