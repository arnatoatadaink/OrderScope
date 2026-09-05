# OrderScope — Temporary Content Lifecycle ADR v0.1

Status: Accepted
Date: 2026-09-06
Decision ID: `ADR-TEMP-CONTENT-001`
Work item: `I0-006`

## 1. Decision

Temporary filing, news, and extraction bodies are represented by an immutable
`TemporaryContent` audit record. The record contains a bounded `content_ref`,
retention class, capture and expiry times, lifecycle state, and deletion audit
fields. It never contains the body, provider response, or credentials.

The storage implementation is intentionally out of scope. Adapters and a later
retention worker use this contract to coordinate temporary access and deletion.

## 2. Lifecycle contract

| State | Required fields | Meaning |
|---|---|---|
| `staged` | reference, capture time, expiry | Content is available for bounded extraction; no completion or deletion audit exists. |
| `extraction_succeeded` | `extraction_completed_at` | Extraction completed and the raw body remains temporary under `temporary_success`. |
| `exception` | `exception_reason` | Processing did not complete; content is retained only under `temporary_exception`. |
| `deleted` | `deleted_at`, `deletion_proof` | The temporary body is gone; metadata and the deletion audit may remain. |

`temporary_exception` content must expire no later than 30 days after capture.
Successful content is also temporary and must be deleted by the downstream
retention controller after extraction; this contract records the proof when that
operation completes. `durable_metadata` is not a valid class for a body
reference.

An exception reason is preserved as bounded metadata after deletion. A deletion
proof is an opaque bounded audit reference, not a copy of the deleted body.

## 3. Invariants and handoff

- All operational timestamps are UTC and expiry cannot precede capture.
- Lifecycle metadata is immutable; a state transition creates a new audit record
  in a physical implementation rather than updating historical evidence in place.
- Secret-like metadata, provider response bodies, and credentials are rejected.
- `Evidence.retention_class` remains the durable Fact Store projection; this
  lifecycle record supplies the temporary reference and deletion audit fields.

The contract is implemented in
`analysis/app/orderscope_local/contracts/temporary_content.py` and tested in
`analysis/tests/contracts/test_temporary_content_contract.py`.
