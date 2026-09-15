# R0-008 First Remote Custody ACK Acceptance — 2026-09-13

Status: **Accepted through ACKNOWLEDGED — grace policy not yet elapsed/approved**
Scope: First real remote `normalized_bar` custody generation on `live-canary`

## Accepted generation

- generation ID: `d1-custody-5b7c680a337a817950b2de12fa5ee18be54ef06b3336e7386872ded4d87494c7`
- export manifest ID: `d1-export-9498d37fb1681d8369956f0876bedcc51fe4ac35d01ab09edcd2c1f93248e71f`
- table: `normalized_bar`
- half-open window: `[2026-09-01T16:03:00.000Z, 2026-09-01T16:04:00.000Z)`
- row count: `1`
- artifact bytes: `581`
- artifact SHA-256: `de380ae35c1ab50f5e0364585e7f3224512085dc3bcd4abff8e37631938bed56`

## Evidence

Remote custody transfer used two identical read-only D1 SELECT passes. Canonical artifact bytes, export manifest identity, and custody generation identity matched across retry.

Local D1-native custody quality validation accepted the real artifact with the same row count/hash/manifest/generation identity.

Focused local acceptance evidence:

- D1 custody/remote export/quality validator tests: `18/18 passed`;
- first real custody quality check: `PASS`;
- first real lifecycle acknowledgement fixture: `1/1 passed`.

The accepted lifecycle boundary is:

```text
PLANNED
  -> EXPORTED
  -> HASH_VERIFIED
  -> IMPORTED
  -> QUALITY_ACCEPTED
  -> ACKNOWLEDGED
```

## Current gate

`normalized_bar` purge eligibility requires:

```text
custodyAcknowledged = true
qualityAccepted = true
graceElapsed = true
```

The first two gates are satisfied for this generation. `graceElapsed` is **not** yet asserted because no concrete production/canary grace duration has been frozen by the accepted policy.

Therefore current state is:

```text
ACKNOWLEDGED -> GRACE [policy/time evidence pending]
```

This document does not authorize or record `PURGE_ELIGIBLE`, `PURGED`, D1 DELETE, Worker mutation, Cron mutation, or feature activation.

## Next action

Review and explicitly adopt a bounded grace policy for the first remote Canary generation. Only after the policy-defined duration has elapsed may the lifecycle be advanced to `GRACE` with `graceElapsed=true` and evaluated for `PURGE_ELIGIBLE`.
