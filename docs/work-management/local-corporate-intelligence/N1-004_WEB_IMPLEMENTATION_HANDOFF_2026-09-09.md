# OrderScope — N1-004 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `N1-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `S0-007`, Accepted `E0-007`, Accepted `N1-003`

## 1. Local acceptance carried into this cycle

`N1-003` was promoted to Accepted from user-reported local evidence:

```text
focused N1-003 tests -> 11 passed
full pytest suite     -> 320 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N1-004 must preserve SEC/IR/News conflicts, ambiguity, and later-confirmation cases with an explicit exception/review reason. It must not overwrite or delete source-grounded Facts merely because a later source disagrees.

This implementation models uncertainty as a separate `PENDING_REVIEW` Fact and models later resolution as an `Interpretation` with complete basis lineage.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/review.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_contradiction_review.py`

## 4. Review reason taxonomy

`NewsReviewReasonKind` is frozen to:

- `source_conflict`
- `ambiguous_subject`
- `ambiguous_value`
- `ambiguous_time`
- `later_confirmation_required`

Every review case also requires a bounded human-readable `exception_reason`. The reason is durable metadata; it must not contain raw article body text or secrets.

## 5. Pending-review representation

`open_news_review_case()` receives one or more already accepted source-grounded Facts. It never edits those records.

The returned `NewsReviewCase` contains a new Fact:

```text
fact_type       = news.review.pending
assertion_kind  = pending_review
status          = pending_review
reason_kind     = <versioned enum>
exception_reason
source_fact_ids = immutable canonical tuple
```

A pending-review Fact is intentionally not promoted into an observed corporate event. Its purpose is to record that accepted source evidence is insufficient or contradictory.

## 6. Source lineage / identity boundary

All source Facts in one review case must:

- be real `Fact` records, not nested review Facts;
- have unique record IDs;
- share one registry-resolved subject;
- already be accepted by the review-open time.

The source Fact IDs are sorted canonically before the review identity is computed. Reversing input order therefore cannot create a second review record with the same semantic inputs.

The original source records retain their own provenance/evidence. The review record references their IDs rather than copying or rewriting those source claims.

## 7. Later confirmation / resolution

`resolve_news_review_case()` requires a **new independent Fact** for the same subject. Reusing one of the original conflicting Facts is rejected as confirmation.

Resolution creates an `Interpretation` rather than mutating the pending review Fact:

```text
interpretation_type = news.review.resolution
assertion_kind      = revision
status              = resolved
resolution_reason
confirmation_fact_id
review_fact_id
basis_record_ids    = original source Facts + review Fact + confirmation Fact
method_version      = news-review-controller-v0.1
```

This preserves the historical state that the case was unresolved at an earlier acceptance time while allowing later as-of views to see the resolution.

## 8. Conflict policy

N1-004 does not automatically rank SEC > IR > News to erase disagreement. Source priority may inform a later review decision, but contradictory accepted source assertions stay durable until an explicit confirmation/resolution record exists.

Likewise, N1-004 does not guess:

- missing subject identity;
- missing numeric value;
- missing effective/event time;
- which source is correct merely from publisher class;
- a future confirmation that has not yet been accepted.

## 9. Focused fixtures encoded

The focused module currently collects 14 cases (10 test functions, including a 5-value reason-kind parametrization) covering:

1. SEC/News-style source conflict opens a separate pending-review Fact;
2. single-source ambiguity remains unresolved without invented resolution;
3. all five review reason kinds are accepted/versioned;
4. source order produces deterministic review identity/lineage;
5. cross-subject and nested-review sources are rejected;
6. review cannot open before source acceptance;
7. later independent confirmation creates a resolution Interpretation with full lineage;
8. same-source reuse and wrong-subject confirmation are rejected;
9. review/resolution timestamp ordering is enforced;
10. blank exception/resolution reasons are rejected.

Fixtures are storage-neutral and use no live provider access.

## 10. Explicit non-scope

N1-004 does not:

- automatically adjudicate which source is true;
- delete or rewrite SEC/IR/News Facts;
- implement manual-review UI/work queues;
- parse new body text;
- introduce LLM conflict resolution;
- delete temporary content;
- generate deletion proof;
- perform sentiment/impact/Regime/prediction interpretation.

N1-005 owns the temporary-content retention controller.

## 11. Local verification boundary

Before promoting N1-004 to Accepted, run:

```bash
uv run pytest -q analysis/tests/news/test_news_contradiction_review.py
uv run pytest -q
git diff --check
```

Acceptance requires focused tests, full regression, and clean diff check.

## 12. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Accepted
N1-003 Accepted
N1-004 Provisional result — local test pending
N1-005 waits for N1-004 acceptance
```

## 13. Next action after acceptance

After N1-004 acceptance, proceed to `N1-005 — retention controller`. That task must promptly delete successful bodies after extraction, delete exception bodies by the 30-day maximum, and retain durable metadata/Fact/delete proof without retaining the body itself.
