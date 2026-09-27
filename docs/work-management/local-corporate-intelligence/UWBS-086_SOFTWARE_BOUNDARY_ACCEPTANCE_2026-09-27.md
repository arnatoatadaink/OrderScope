# UWBS-086 — Software Boundary Acceptance — 2026-09-27

Status: **SOFTWARE BOUNDARY ACCEPTED / HISTORICAL-CAPACITY ACCEPTANCE STILL OPEN**
Branch: `l1-003-local-market-recovery`

## Accepted local verification

```text
cross-asset Canary contract focused tests: 8 passed
replay/capacity focused tests:             10 passed
full Python regression:                   780 passed
compileall:                               PASS
git diff --check:                         PASS
```

This accepts the deterministic contract/replay/capacity software boundary only.

## Accepted software semantics

- false negative -> REJECT;
- regime mismatch -> REJECT;
- capacity headroom below the configured floor -> REJECT;
- false positive -> REVIEW;
- clean replay + sufficient headroom -> ACCEPT;
- capacity limits remain external inputs rather than hard-coded provider quotas;
- synthetic regression scenarios remain explicitly synthetic and cannot be reported as historical evidence;
- no provider activation, Worker/Cron mutation, D1 mutation, PB authorization, or trading action occurred.

## Still required before final UWBS-086 acceptance

1. repository-backed historical replay packet covering the canonical UWBS-080..085 inputs, or a separately approved reduced historical scope with explicit limitations;
2. projected or measured Worker/D1 usage using billing-relevant rows read/written and storage growth rather than statement execution count alone;
3. fresh platform quota evidence and headroom calculation;
4. historical false-positive / false-negative / regime-mismatch summary;
5. final ACCEPT / REVIEW / REJECT decision.

Synthetic fixtures must never be presented as historical evidence.
