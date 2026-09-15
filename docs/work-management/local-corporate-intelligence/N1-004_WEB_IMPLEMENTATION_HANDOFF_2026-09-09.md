# OrderScope — N1-004 Web Implementation Handoff

Status: **Accepted**
Date: 2026-09-09
Task: `N1-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `S0-007`, Accepted `E0-007`, Accepted `N1-003`

## 1. Local acceptance

N1-004 is Accepted from user-reported local evidence:

```text
focused N1-004 tests -> 14 passed
full pytest suite     -> 334 passed
git diff --check      -> clean / no findings
```

The first focused run had 12 failures / 2 passes because the initial implementation placed a tuple inside `Fact.value`. The Accepted Fact Store permits mapping members only when they are scalar. N1-004 was corrected without widening the shared Fact Store schema, then the full focused and regression suites passed.

## 2. WBS completion boundary

N1-004 preserves SEC/IR/News conflicts, ambiguity, and later-confirmation cases with an explicit exception/review reason. It does not overwrite or delete source-grounded Facts merely because a later source disagrees.

Uncertainty is represented as a separate `PENDING_REVIEW` Fact and later resolution as an `Interpretation` with complete basis lineage.

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

Every review case also requires a bounded human-readable `exception_reason`.

## 5. Pending-review representation

`open_news_review_case()` receives already accepted source-grounded Facts and never edits them.

The review Fact contains scalar audit metadata only:

```text
fact_type             = news.review.pending
assertion_kind        = pending_review
status                = pending_review
reason_kind           = <versioned enum>
exception_reason      = <bounded scalar text>
source_fact_count     = <scalar integer>
source_fact_ids_hash  = <scalar SHA-256>
```

The complete canonical source Fact ID tuple is retained by `NewsReviewCase.source_fact_ids`, outside `Fact.value`.

## 6. Source lineage / identity boundary

All source Facts in one review case must:

- be `Fact` records, not nested review Facts;
- have unique record IDs;
- share one registry-resolved subject;
- already be accepted by the review-open time.

Source Fact IDs are sorted before review identity is computed, so reversing input order cannot create a second semantic review case.

## 7. Later confirmation / resolution

`resolve_news_review_case()` requires a new independent Fact for the same subject. Reusing an original conflicting Fact is rejected.

Resolution creates an `Interpretation` with:

```text
interpretation_type = news.review.resolution
assertion_kind      = revision
status              = resolved
basis_record_ids    = original source Facts + review Fact + confirmation Fact
method_version      = news-review-controller-v0.1
```

Original source Facts and the pending review Fact remain immutable for as-of reconstruction.

## 8. Conflict policy

N1-004 does not automatically rank SEC > IR > News to erase disagreement and does not guess missing subject, value, effective time, or future confirmation.

## 9. Accepted focused coverage

The accepted focused module collects 14 cases covering source conflicts, all five review reasons, canonical source ordering, cross-subject/nested-review rejection, time ordering, independent confirmation, resolution lineage, and bounded reasons.

## 10. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Accepted
N1-003 Accepted
N1-004 Accepted
N1-005 Ready
```

## 11. Next action

Proceed to `N1-005 — retention controller`: delete successful bodies promptly after extraction, delete exception bodies no later than their bounded expiry (maximum 30 days), and retain only durable metadata/Fact/deletion proof rather than raw content.
