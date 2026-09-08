# OrderScope — O0-003 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `O0-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_OFFICIAL_STATEMENT_IMPLEMENTATION_WEB_017_2026-09-04.md`
Depends on: Accepted `I0-005`, Accepted `O0-002`

## 1. Local acceptance carried into this cycle

`O0-002` was promoted to Accepted from user-reported local evidence:

```text
focused official-feed tests -> 9 passed
full pytest suite           -> 231 passed
git diff --check            -> clean / no findings
```

Its handoff was updated before O0-003 implementation.

## 2. WBS completion boundary

O0-003 requires statement/proposal semantics to remain separate from signed/effective/formal-decision Facts.

This implementation therefore fixes four semantic Fact types:

- `official.statement`
- `official.proposal`
- `official.decision`
- `official.implementation`

The classification is semantic-assertion level, not document level. One source document may emit more than one Fact.

## 3. Changed/added files

- `analysis/app/orderscope_local/official/official_statement.py`
- `analysis/app/orderscope_local/official/__init__.py`
- `analysis/tests/official/test_official_statement.py`

## 4. Timestamp and promotion rules

The contract deliberately prevents semantic promotion:

- statement/proposal cannot carry `decision_at`, `effective_at`, or `effective_expression`;
- decision requires explicit source-grounded `decision_at`;
- decision cannot carry implementation-effective semantics;
- implementation cannot reuse `decision_at`;
- implementation requires exactly one explicit `effective_at` or source-preserved `effective_expression`.

`SourceTimestamp` precision is retained. DATE_ONLY values remain date-only and are never converted to midnight UTC.

Relative source expressions such as `90 days after publication in the Federal Register` are retained as source meaning without computing an absolute date in O0-003.

## 5. Fact Store integration

Each accepted semantic observation builds one I0-005 `Fact` plus one Tier-1 official `Evidence` record.

The Fact preserves:

- `policy_thread_id`
- upstream-resolved `actor_id`
- O0-001 `source_id`
- canonical official item URL
- semantic Fact kind
- bounded normalized assertion
- only the source-established semantic timestamps applicable to that kind

The Evidence and Fact are linked bidirectionally by record IDs and share source URL/hash/retrieval provenance.

No source body is stored by this contract.

## 6. Actor boundary

O0-001 contains source-owner seed Actors, while individual officials are resolved from item content later. O0-003 therefore accepts an already-resolved canonical `actor_id` from the upstream actor-resolution boundary instead of forcing every content Actor to be one of the five O0-001 seed owners.

It does **not** silently replace an unresolved individual with the source owner.

## 7. Canary / negative fixtures encoded

Focused tests cover:

- statement/proposal cannot be promoted with effective semantics;
- decision requires decision timestamp;
- decision timestamp cannot be reused as effective timestamp;
- implementation requires explicit effective timestamp or relative effective expression;
- DATE_ONLY decision remains DATE_ONLY;
- one White House proclamation document can produce separate decision, implementation, and future-intent statement Facts;
- FOMC target-range decision remains separate from forward guidance statement;
- Treasury NPRM remains proposal with no inferred effective time;
- SEC-style relative effective expression is retained without calculating a date;
- Fact/Evidence linkage and Tier-1 quality are preserved;
- duplicate Fact/Evidence IDs are rejected.

The fixtures are contract cases derived from WEB-017 semantic patterns; they are not intended as a complete live-policy dataset.

## 8. Explicit non-scope

O0-003 does not yet:

- parse official HTML/RSS text into semantic observations automatically;
- infer individual Actor identity from titles/names;
- calculate relative effective expressions into absolute dates;
- link AMD/NVDA versus semiconductor-theme relevance;
- decide revocation/suspension semantics;
- run live policy verification.

Instrument/theme linkage is O0-004. End-to-end Official Signal quality and update/delete/relevance error fixtures are O0-005.

## 9. Local verification boundary

Before promoting O0-003 to Accepted, run:

```bash
uv run pytest -q analysis/tests/official/test_official_statement.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check. Semantic review should confirm that statement/proposal never become operative Facts without explicit later decision/implementation evidence and that a document can yield multiple semantic Facts.

## 10. Tracker reconciliation note

The integrated runtime Progress Tracker still contains a stale top snapshot from before the E0/O0 execution cycles. It must be reconciled by complete-file update rather than overwriting from a truncated fetch. This Web cycle does not replace that authority file from partial content.

Current repository evidence establishes at least:

```text
E0-001..007 Accepted
O0-001       Accepted
O0-002       Accepted
O0-003       Provisional result — local test pending
```

## 11. Next action after acceptance

If local verification passes, promote `O0-003` to Accepted and begin `O0-004 — Link instrument/theme relevance`, using the existing WEB-018 research input and retaining direct AMD/NVDA relevance separately from indirect semiconductor-theme relevance.
