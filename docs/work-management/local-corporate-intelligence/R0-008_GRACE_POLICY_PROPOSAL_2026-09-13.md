# R0-008 Grace Policy Proposal — 2026-09-13

Status: **Proposal — not yet adopted**
Scope: First remote Canary `normalized_bar` custody generation only

## Background

The accepted R0 D1 drain design requires an explicit grace period between `ACKNOWLEDGED` and `PURGE_ELIGIBLE`. The design intentionally does not freeze a universal duration such as 24 hours, 7 days, or 30 days without measured operational evidence.

For the first real remote generation, custody, hash verification, local D1-native quality validation, and acknowledgement have all succeeded. The remaining non-destructive decision is how long to retain the acknowledged source rows before they may become purge eligible.

## Proposed first-Canary policy

Adopt a **24-hour grace period measured from the acknowledgement timestamp** for the first isolated `normalized_bar` Canary generation only.

Rationale:

- the candidate is exactly one historical row in a one-minute half-open window;
- custody was re-read twice and produced identical artifact/manifest/generation identity;
- local quality acceptance succeeded against the real D1-native row schema;
- `normalized_bar` is HOT_DATA, not current control truth;
- the one-row source window is already historical and not needed as the current acquisition checkpoint;
- a 24-hour hold preserves a full-day rollback/inspection interval before any destructive action;
- this does not establish the steady-state production retention duration.

## Scope limits

This proposed 24-hour duration applies only to:

- generation `d1-custody-5b7c680a337a817950b2de12fa5ee18be54ef06b3336e7386872ded4d87494c7`;
- table `normalized_bar`;
- window `[2026-09-01T16:03:00.000Z, 2026-09-01T16:04:00.000Z)`;
- isolated `live-canary` acceptance work.

It does **not** define:

- full-v0.1 production retention;
- News retention;
- acceptance-receipt/conflict/run-evidence retention;
- current-control/checkpoint retention;
- a universal D1 purge policy.

## Required lifecycle interpretation if adopted

```text
ACKNOWLEDGED
  -> GRACE
     graceElapsed = false until acknowledgement_time + 24h
  -> PURGE_ELIGIBLE
     only after graceElapsed = true and the existing normalized_bar policy still evaluates eligible
  -> PURGED
     still separately authorized remote destructive mutation
```

The local lifecycle may prove `PURGE_ELIGIBLE` after the grace period. Actual D1 DELETE / `PURGED` remains outside this proposal and requires a separate explicit remote mutation authorization.

## Recommendation

Use the 24-hour Canary-only grace as an acceptance scaffold, then revisit steady-state duration using measured D1 growth, replay needs, incident-response needs, export cadence, and actual operational headroom.
