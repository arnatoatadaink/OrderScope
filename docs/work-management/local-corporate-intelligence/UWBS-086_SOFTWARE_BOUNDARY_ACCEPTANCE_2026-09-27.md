# UWBS-086 — Software Boundary Acceptance — 2026-09-27

Status: **SOFTWARE BOUNDARY ACCEPTED / HISTORICAL-CAPACITY ACCEPTANCE STILL OPEN**
Branch: `l1-003-local-market-recovery`

## Accepted local verification

```text
cross-asset Canary contract focused tests: 8 passed
full Python regression:                  770 passed
compileall:                              PASS
git diff --check:                        PASS
```

This accepts the deterministic contract/software boundary only.

## Accepted software semantics

- false negative -> REJECT;
- regime mismatch -> REJECT;
- capacity headroom below the configured floor -> REJECT;
- false positive -> REVIEW;
- clean replay + sufficient headroom -> ACCEPT;
- capacity limits remain external inputs rather than hard-coded provider quotas;
- no provider activation, Worker/Cron mutation, D1 mutation, PB authorization, or trading action occurred.

## Still required before final UWBS-086 acceptance

1. deterministic replay evaluator verification;
2. clearly labelled synthetic regression cases for classifier/decision mechanics;
3. repository-grounded historical replay evidence, or an explicit historical-evidence-pending disposition if suitable data is not yet present;
4. projected Worker/D1 usage measurement;
5. fresh platform quota evidence and headroom calculation;
6. false-positive / false-negative / regime-mismatch summary;
7. final acceptance decision.

Synthetic fixtures must never be presented as historical evidence.
