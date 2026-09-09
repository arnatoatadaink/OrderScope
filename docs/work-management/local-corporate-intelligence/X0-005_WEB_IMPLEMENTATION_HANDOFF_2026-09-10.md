# OrderScope — X0-005 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-10
Task: `X0-005`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `X0-001`, `X0-002`, `X0-003`, `X0-004`

## 1. Completion boundary

X0-005 adds one deterministic fixture replay that exercises the accepted integration path across:

```text
filing input
IR earnings input
news input
official input
  -> Fact + Evidence regeneration
  -> temporary-news retention deletion
  -> unified as-of timeline
  -> bounded scheduler execution / resume
```

Implemented file:

- `analysis/tests/integration/test_end_to_end_fixture.py`

No live provider call, remote D1 operation, Worker mutation, secret, or production-only shortcut was added.

## 2. Fixture source set

The focused fixture uses four explicit source-neutral inputs for AMD:

- SEC filing-style input -> `filing.detected`;
- company IR-style input -> `earnings.revenue`;
- secondary-news input -> `news.event.contract`;
- official-government input -> `official.statement`.

Stable Fact/Evidence IDs are derived from canonical JSON plus SHA-256, so identical input must reproduce identical identities.

The fixture builder is test-only. It does not claim to replace the separately accepted source-specific extraction/adaptation tests.

## 3. Retention path

The news side includes an extracted successful temporary content record and runs the accepted N1-005 retention controller.

Expected result:

```text
TemporaryContentState.EXTRACTION_SUCCEEDED
  -> delete_due_content(...)
  -> TemporaryContentState.DELETED
```

Only deletion audit metadata/proof remains; no body is persisted in the fixture state.

## 4. Timeline path

After Fact/Evidence validation, the replay runs the accepted X0-001 unified timeline query.

Expected source-kind order follows information availability:

```text
FILING
EARNINGS
NEWS
OFFICIAL
```

The replay verifies that the same fixture produces the same timeline item identities and kinds across separate runs.

## 5. Scheduler path

The fixture runs through the accepted X0-004 scheduler as explicit deterministic jobs:

```text
ingest-filing
ingest-ir
ingest-news
ingest-official
retention
timeline
```

A second focused case splits execution after `ingest-news`, then resumes from that job boundary and confirms the remaining jobs complete the same fixture state.

## 6. Focused tests

The X0-005 module contains 4 cases:

1. full fixture regenerates Fact, retention state, and timeline;
2. identical replay is deterministic across Fact IDs, Evidence IDs, timeline, and deletion audit state;
3. timeline order is information-time deterministic;
4. scheduler job-boundary resume completes the fixture correctly.

## 7. Local verification boundary

Run from repository root:

```bash
uv run pytest -q analysis/tests/integration/test_end_to_end_fixture.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires all four checks to pass.

## 8. Next action after acceptance

If local verification passes:

```text
X0-005 Accepted
  -> X0-006 Canary operations runbook
```

`L1-006` remains independently Ready. `L1-003` / `SMOKE-007` real-D1 work remains separately gated and is not implied by fixture acceptance.
