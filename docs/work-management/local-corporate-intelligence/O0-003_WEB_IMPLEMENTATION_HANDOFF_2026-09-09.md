# OrderScope — O0-003 Web Implementation Handoff

Status: **Accepted**
Date: 2026-09-09
Task: `O0-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Research input: `REPORT_OFFICIAL_STATEMENT_IMPLEMENTATION_WEB_017_2026-09-04.md`
Depends on: Accepted `I0-005`, Accepted `O0-002`

## 1. Local acceptance evidence

User-reported local verification:

```text
focused official-statement tests -> 8 passed
full pytest suite                -> 239 passed
git diff --check                 -> clean / no findings
```

The semantic review boundary remains unchanged: statement/proposal never become operative Facts without explicit decision/implementation evidence, and one source document may yield multiple semantic Facts.

## 2. WBS completion boundary

O0-003 requires statement/proposal semantics to remain separate from signed/effective/formal-decision Facts.

Implemented semantic Fact types:

- `official.statement`
- `official.proposal`
- `official.decision`
- `official.implementation`

Classification is semantic-assertion level, not document level.

## 3. Changed/added files

- `analysis/app/orderscope_local/official/official_statement.py`
- `analysis/app/orderscope_local/official/__init__.py`
- `analysis/tests/official/test_official_statement.py`

## 4. Timestamp and promotion rules

- statement/proposal cannot carry `decision_at`, `effective_at`, or `effective_expression`;
- decision requires explicit source-grounded `decision_at`;
- decision cannot carry implementation-effective semantics;
- implementation cannot reuse `decision_at`;
- implementation requires exactly one explicit `effective_at` or source-preserved `effective_expression`.

`SourceTimestamp` precision is retained. DATE_ONLY values remain date-only.

## 5. Fact Store integration

Each semantic observation builds one I0-005 `Fact` plus one Tier-1 official `Evidence` record. Fact and Evidence share canonical source URL/hash/retrieval provenance and remain bidirectionally linked by record ID.

## 6. Actor boundary

O0-003 accepts an upstream-resolved canonical `actor_id`; it does not silently replace an unresolved individual with a source owner.

## 7. Acceptance result

`O0-003` is **Accepted** based on the focused/full regression/diff evidence above. It is safe as the dependency for O0-004.

## 8. Next action

Proceed to `O0-004 — Link instrument/theme relevance` using `REPORT_OFFICIAL_INSTRUMENT_THEME_LINKAGE_WEB_018_2026-09-04.md`. Preserve direct AMD/NVDA relevance separately from indirect semiconductor-theme exposure and mention-only/unresolved cases.
