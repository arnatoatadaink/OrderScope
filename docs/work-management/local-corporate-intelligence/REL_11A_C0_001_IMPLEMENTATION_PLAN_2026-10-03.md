# OrderScope — REL-11A / C0-001 Implementation Plan — 2026-10-03

Status: **IMPLEMENTATION IN PROGRESS — VALIDATION PENDING**
Release: `v0.1.11`
Formal WBS: `C0-001`
Canonical source: `UWBS-106`
Current implementation branch: `feat/rel-11a-c0-001-onchain-fact-v2`
Superseded setup branch: `feat/rel-11a-c0-001-crypto-onchain-fact`

## 1. Goal

Implement the source-neutral Fact-layer contract for Crypto On-chain Event Intelligence without introducing incident attribution or live-provider side effects.

## 2. Package boundary

Dedicated Python package:

`analysis/app/orderscope_local/crypto_onchain/`

REL-11A modules:

- `models.py` — project/chain/component relationship and confirmed-transfer Fact contracts;
- `registry.py` — deterministic registry identity, duplicate/update/conflict handling;
- `__init__.py` — stable public exports.

Focused tests:

`analysis/tests/crypto_onchain/test_c0_001_registry.py`

## 3. Contract boundary

REL-11A stores only source-grounded facts:

- project identity;
- chain/network identity;
- wallet/contract component identity;
- relationship role plus evidence provenance;
- unresolved/disputed relationship status;
- confirmed transaction hash and block/event timing;
- accepted timestamp;
- asset, amount and optional USD notional;
- source reference/revision.

A transfer fact MUST NOT encode hack, exploit, theft, malicious intent, or incident confirmation.

## 4. Deterministic identity

Registry identity uses explicit normalized keys rather than mutable labels:

- project: canonical project id;
- chain: canonical chain id;
- component: `(chain_id, address)`;
- relationship logical identity: `(project_id, chain_id, address, role)`;
- relationship evidence-record identity: `(project_id, chain_id, address, role, source_ref)`;
- transfer: `(chain_id, tx_hash, transfer_index)`.

The split between logical relationship identity and source-specific evidence identity allows contradictory sources to coexist without silent overwrite.

Address normalization is chain-policy-neutral at REL-11A: surrounding whitespace is rejected by contract rules; no universal lower-casing is applied because address case semantics differ across chains.

## 5. Update/conflict rule

- exact duplicate facts are idempotent;
- distinct sources may retain separate evidence records for the same logical relationship;
- incompatible facts sharing the same deterministic source-specific identity raise a conflict rather than silently overwrite;
- unresolved/disputed relationships remain representable.

## 6. Acceptance scope

Focused REL-11A tests cover:

1. valid project/chain/component registration;
2. deterministic identity;
3. UTC timestamp enforcement;
4. confirmed-transfer normalization;
5. non-negative finite amount/notional checks;
6. duplicate idempotency;
7. incompatible duplicate conflict;
8. unresolved/disputed relationship preservation across distinct sources;
9. transfer facts containing no incident-attribution field or state;
10. no universal address-case normalization.

Required validation before REL-11A acceptance:

```bash
uv run pytest -q analysis/tests/crypto_onchain/test_c0_001_registry.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

Release-level cumulative acceptance remains at REL-11X.

## 7. Current implementation state

Current clean branch relative to `main`:

```text
feat/rel-11a-c0-001-onchain-fact-v2
  ahead: 4
  behind: 0
```

Changed implementation files:

- `analysis/app/orderscope_local/crypto_onchain/__init__.py`
- `analysis/app/orderscope_local/crypto_onchain/models.py`
- `analysis/app/orderscope_local/crypto_onchain/registry.py`
- `analysis/tests/crypto_onchain/test_c0_001_registry.py`

The ChatGPT execution container could not clone GitHub because external DNS resolution was unavailable, so pytest/compileall results are **not yet claimed**. Validation remains pending until run in the repository environment.

## 8. Non-goals

REL-11A does not implement:

- provider adapters or API activation;
- mempool monitoring;
- abnormal-flow scoring (C0-002);
- market-context joins (C0-003);
- exploit attribution/replay (C0-004);
- Worker/Cron/D1 mutations;
- automated trading.
