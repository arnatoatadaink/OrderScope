# OrderScope — REL-11A / C0-001 Implementation Plan — 2026-10-03

Status: **IMPLEMENTATION PLAN — REL-11A START**
Release: `v0.1.11`
Formal WBS: `C0-001`
Canonical source: `UWBS-106`

## 1. Goal

Implement the source-neutral Fact-layer contract for Crypto On-chain Event Intelligence without introducing incident attribution or live-provider side effects.

## 2. Package boundary

Create a dedicated Python package:

`analysis/app/orderscope_local/crypto_onchain/`

Initial REL-11A modules:

- `models.py` — project/chain/component relationship and confirmed-transfer Fact contracts;
- `registry.py` — deterministic registry identity, duplicate/update/conflict handling;
- `__init__.py` — stable public exports.

Focused tests:

`analysis/tests/crypto_onchain/`

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
- relationship: `(project_id, chain_id, address, role)`;
- transfer: `(chain_id, tx_hash, transfer_index)`.

Address normalization is chain-policy-neutral at REL-11A: surrounding whitespace is rejected/trimmed only by contract rules; no universal lower-casing is applied because address case semantics differ across chains.

## 5. Update/conflict rule

- exact duplicate facts are idempotent;
- a newer observation may add source revision/evidence through a separately identified relationship record;
- incompatible facts sharing the same deterministic identity raise a conflict rather than silently overwrite;
- unresolved/disputed relationships remain representable.

## 6. Acceptance scope

Focused REL-11A tests must cover:

1. valid project/chain/component registration;
2. deterministic identity;
3. UTC timestamp enforcement;
4. confirmed-transfer normalization;
5. non-negative finite amount/notional checks;
6. duplicate idempotency;
7. incompatible duplicate conflict;
8. unresolved/disputed relationship preservation;
9. transfer facts containing no incident-attribution field or state.

Release-level full regression remains deferred to REL-11X, but REL-11A should run its focused tests plus full `analysis/tests`, compileall and `git diff --check` before acceptance.

## 7. Non-goals

REL-11A does not implement:

- provider adapters or API activation;
- mempool monitoring;
- abnormal-flow scoring (C0-002);
- market-context joins (C0-003);
- exploit attribution/replay (C0-004);
- Worker/Cron/D1 mutations;
- automated trading.
