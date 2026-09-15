# OrderScope — R0-007 First Remote Custody Acceptance

Status: **ACCEPTED — first bounded remote custody transfer**
Date: 2026-09-13 JST
Branch: `docs/mermaid-conventions-v0.1`
Scope: one historical `normalized_bar` half-open window from live-canary D1 into local immutable custody

## 1. Accepted source window

```text
environment = live-canary
database = orderscope-state-live-canary
table = normalized_bar
window = [2026-09-01T16:03:00.000Z, 2026-09-01T16:04:00.000Z)
row_count = 1
```

The candidate was discovered with read-only D1 queries. The immediately preceding attempted 2026-09-11 window contained zero rows and was not treated as acceptance evidence.

## 2. Remote-to-local custody evidence

The frozen one-row window was fetched twice using read-only remote SELECTs. Both responses were canonicalized through the reviewed R0-007 remote adapter into canonical NDJSON and the existing L1-001 export-manifest / R0-007 custody-manifest contracts.

Accepted values:

```text
row_count     = 1
byte_size     = 581
sha256        = de380ae35c1ab50f5e0364585e7f3224512085dc3bcd4abff8e37631938bed56
manifest_id   = d1-export-9498d37fb1681d8369956f0876bedcc51fe4ac35d01ab09edcd2c1f93248e71f
generation_id = d1-custody-5b7c680a337a817950b2de12fa5ee18be54ef06b3336e7386872ded4d87494c7
repeat_identity = PASS
```

`repeat_identity = PASS` means the repeated read produced identical canonical artifact bytes, export manifest identity, and custody generation identity.

## 3. Acceptance boundary

This closes R0-007 through the first real bounded remote custody-transfer evidence:

```text
remote bounded SELECT
  -> canonical NDJSON
  -> SHA-256
  -> D1ExportManifest
  -> D1CustodyManifest
  -> repeated read / identity confirmation
```

The remote D1 side was read-only. No D1 row was changed or deleted. No Worker/Cron/config mutation, migration, News activation, or feature activation was part of this acceptance.

## 4. Next gate

R0-008 must not begin with purge. The accepted custody generation must first proceed through the reviewed local lifecycle prerequisites:

```text
PLANNED
  -> EXPORTED
  -> HASH_VERIFIED
  -> IMPORTED
  -> QUALITY_ACCEPTED
  -> ACKNOWLEDGED
  -> GRACE
  -> PURGE_ELIGIBLE
```

For `normalized_bar`, purge eligibility requires custody acknowledgement, quality acceptance, replay-horizon elapsed, and grace elapsed. Actual `PURGED` remains a separately authorized remote mutation and is not authorized by this acceptance.
