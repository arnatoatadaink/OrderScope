# OrderScope — REL-11A / C0-001 Acceptance — 2026-10-03

Status: **ACCEPTED / INTEGRATED**
Release: `v0.1.11`
Formal WBS: `C0-001`
Canonical source: `UWBS-106`
Integrated commit: `230f301a8676a6c10e773edd9f8aa6c994c90211`
Implementation branch: `feat/rel-11a-c0-001-onchain-fact-v2`

## Acceptance evidence

Repository-environment validation supplied on 2026-10-03:

```text
uv run pytest -q analysis/tests/crypto_onchain/test_c0_001_registry.py
9 passed in 2.04s

uv run pytest -q analysis/tests
1127 passed in 61.43s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no error output)
```

## Accepted capability

- source-neutral project / chain / wallet-contract Fact identities;
- source-specific relationship evidence while retaining logical relationship identity;
- unresolved and disputed relationship evidence preserved rather than overwritten;
- confirmed-transfer Fact identity `(chain_id, tx_hash, transfer_index)`;
- UTC and observation/availability/acceptance timing boundaries;
- finite non-negative Decimal amount / optional USD notional;
- exact duplicate idempotency;
- incompatible same-identity conflict detection;
- no universal address lower-casing;
- no incident / hack / exploit / theft / malicious attribution in transfer Fact.

## Boundary retained

REL-11A does not implement abnormal-flow scoring, market-context correlation, exploit attribution, provider activation, mempool monitoring, Worker/Cron/D1 mutation, or automated trading.

## Critical-path transition

```text
REL-11A / C0-001 / UWBS-106  ACCEPTED / INTEGRATED
    -> REL-11B / C0-002 / UWBS-107  NEXT
```

Release-level cumulative `v0.1.11` acceptance remains deferred to `REL-11X`.
