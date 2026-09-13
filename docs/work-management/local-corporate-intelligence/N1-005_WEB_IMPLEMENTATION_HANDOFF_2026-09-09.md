# OrderScope — N1-005 Web Implementation Handoff

Status: **Accepted**
Date: 2026-09-09
Task: `N1-005`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `I0-006`, Accepted `N1-004`

## 1. Acceptance evidence

`N1-005` was promoted to Accepted from user-reported local evidence:

```text
focused N1-005 tests -> 11 passed
full pytest suite     -> 345 passed
git diff --check      -> clean / no findings
```

The preceding N1-004 acceptance remains:

```text
focused N1-004 tests -> 14 passed
full pytest suite     -> 334 passed
git diff --check      -> clean / no findings
```

## 2. WBS completion boundary

N1-005 must:

- delete successful News bodies after extraction;
- delete exception bodies no later than their bounded expiry;
- rely on the Accepted I0-006 maximum exception lifetime of 30 days;
- retain durable metadata / Facts / lifecycle deletion proof without retaining raw body content.

The implementation is storage-neutral: physical deletion is performed only through an injected deleter boundary.

## 3. Changed/added files

- `analysis/app/orderscope_local/news/retention.py`
- `analysis/app/orderscope_local/news/__init__.py`
- `analysis/tests/news/test_news_retention_controller.py`

## 4. Versioned controller

```text
news-retention-controller-v0.1
```

The controller operates only on Accepted `TemporaryContent` lifecycle records.

## 5. Successful-body policy

A `TEMPORARY_SUCCESS` body is deletable only after N1-003 has transitioned it to:

```text
state = extraction_succeeded
extraction_completed_at = <UTC instant>
```

Its deletion due time is exactly `extraction_completed_at`.

Therefore a retention pass at or after extraction completion deletes the content immediately. A staged success body is rejected rather than deleted early.

## 6. Exception-body policy

A `TEMPORARY_EXCEPTION` body in `EXCEPTION` state has deletion due time equal to its existing `expires_at`.

N1-005 does not invent another 30-day clock. I0-006 already rejects exception content whose expiry exceeds:

```text
captured_at + 30 days
```

At `expires_at`, the body is due for deletion. `assert_exception_retention_compliant()` reports a violation if a non-deleted exception body still exists beyond that deadline.

## 7. Physical deletion boundary

`TemporaryContentDeleter.delete(content_ref=...)` is the only physical-storage mutation boundary introduced here.

It returns a bounded durable deletion proof. The controller then returns a new immutable `TemporaryContent` audit state:

```text
state          = deleted
deleted_at     = <UTC delete instant>
deletion_proof = <bounded proof>
```

Raw body content is neither accepted nor returned by the controller.

Exception records retain their bounded `exception_reason`; successful records retain `extraction_completed_at`.

## 8. Idempotency / retry boundary

Already-DELETED content is idempotent:

- no second physical delete call is issued;
- the existing deletion proof is retained unchanged.

If physical deletion raises an error, the controller raises a sanitized `ContractViolation` and does not fabricate a DELETED lifecycle state.

Deletion proof is rejected when blank, oversized, or secret-like.

## 9. Deterministic retention decision

`retention_decision()` exposes:

- `delete_now`
- `due_at`
- bounded reason

Policy:

```text
TEMPORARY_SUCCESS + EXTRACTION_SUCCEEDED
  due_at = extraction_completed_at

TEMPORARY_EXCEPTION + EXCEPTION
  due_at = expires_at

DELETED
  no delete; preserve previous audit
```

Invalid lifecycle combinations fail closed.

## 10. Focused fixtures encoded

The focused module contains 11 tests covering:

1. frozen controller version;
2. success body due immediately at extraction completion;
3. success deletion audit contains proof but no body;
4. exception body retained before expiry and deleted at expiry;
5. I0-006 rejects exception lifetime beyond 30 days;
6. exception retention compliance fails beyond expiry;
7. staged successful body cannot be deleted before extraction;
8. already-deleted replay is idempotent and does not hit storage;
9. physical delete failure is sanitized and does not fabricate deletion;
10. invalid/secret-like deletion proof is rejected;
11. retention clock requires UTC.

Fixtures use only an in-memory injected deleter and never persist raw News bodies in Git.

## 11. Explicit non-scope

N1-005 does not:

- implement a concrete filesystem/object-store deleter;
- choose scheduler cadence;
- encrypt temporary storage;
- retain raw body after deletion;
- expose body/deletion operations over HTTP;
- evaluate News recall;
- integrate the unified timeline.

`N1-006` owns News recall evaluation. `X0-001` owns unified timeline integration and is separately gated by `L1-005`.

## 12. Acceptance result

The focused test, full regression suite, and diff check are clean. N1-005 is therefore safe as a downstream prerequisite.

## 13. News lane state

```text
N0-001..004 Accepted
N1-001 Accepted
N1-002 Accepted
N1-003 Accepted
N1-004 Accepted
N1-005 Accepted
N1-006 Ready subject to evaluation dataset/reference-window availability
```

## 14. Gate implication

The News dependency for `X0-001` is now satisfied. `X0-001` still depends on `L1-005`, `I0-005`, `E0-007`, and `O0-005`; repository reconciliation on 2026-09-09 confirms the remaining unsatisfied runtime gate is the Local foundation / market-quality path culminating in `L1-005`.

## 15. Next action

Reconcile the authoritative Local Corporate Intelligence Progress Tracker. Then prioritize the Local foundation path needed for `L1-005`; N1-006 can proceed in parallel when the 1–3 month SEC/IR comparison dataset is available.