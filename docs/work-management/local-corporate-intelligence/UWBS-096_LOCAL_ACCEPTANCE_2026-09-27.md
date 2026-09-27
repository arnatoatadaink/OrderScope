# UWBS-096 Local Acceptance — 2026-09-27

Status: **ACCEPTED**
Task: **UWBS-096 — Define VIX level/change/curve interpretation contract**
Branch: `feat/uwbs-096-vix-etp-roll`

## Validation

Local WSL validation reported by the user:

```text
canonical UWBS-096 focused: 10 passed in 2.41s
auxiliary ETP-roll focused: 10 passed in 2.25s
full regression: 944 passed in 39.08s
compileall: PASS
git diff --check: PASS
```

## Acceptance boundary

Accepted scope:

- source-grounded VIX level/change/curve evidence is consumed as interpretation input;
- `CURVE_STRESS_PERSISTING` requires both curve-level and curve-transition/persistence evidence;
- generic SUPPORT evidence-count validation remains enforced after state-specific semantic validation;
- VIX-linked ETP price/NAV behavior remains auxiliary evidence and is not substituted for VIX itself;
- ETP roll/decay analysis remains auxiliary to canonical UWBS-096 and does not redefine the canonical task.

Not authorized / not included:

- provider activation;
- Worker/Cron/D1 mutation;
- paid procurement;
- PB execution;
- trading action.

## Decision

**ACCEPTED** — UWBS-096 local acceptance is complete and eligible for main integration.
