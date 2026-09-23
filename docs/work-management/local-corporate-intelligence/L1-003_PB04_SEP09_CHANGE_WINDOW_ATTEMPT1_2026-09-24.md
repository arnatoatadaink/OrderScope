# OrderScope — L1-003 PB-04 September 9 Change-window Attempt 1

Status: **SAFE ABORT — no recovery chunk executed**
Date: 2026-09-24 JST
Environment: `live-canary`

## Outcome

The first authorized September 9 change-window attempt stopped at the
post-deploy gate smoke check before the four-chunk campaign began.

Observed sequence:

```text
local packet/evidence identity       PASS
focused tests                        17/17 PASS
TypeScript typecheck                 PASS
health safe baseline                 PASS
exact remote checkpoint preflight    PASS
temporary true-gate dry-run          PASS
temporary control secret             created
temporary true-gate deploy           succeeded
immediate unauthenticated endpoint   HTTP 404 (expected 401)
campaign chunks                      NOT STARTED
safe-close false-gate deploy         succeeded
temporary control secret             deleted
final endpoint                       HTTP 404
```

No chunk invocation occurred, so this attempt did not intentionally mutate
normalized bars, acceptance receipts, acquisition attempts, or the NVDA
coverage checkpoint.

## Cause / hardening

The immediate post-deploy probe could hit the previously active false-gate
version before the new Worker version had propagated. The operator script has
therefore been changed to use a bounded endpoint-status probe instead of a
single immediate request.

A second issue was found during code review: the chunk POST command did not
actually include the frozen `x-orderscope-evidence-sha256` header. That header
is now mandatory and is sent on every chunk request.

The hardened script now:

1. polls the local-evidence endpoint until it returns 401 after the true-gate
   deployment;
2. sends the exact Sep9 evidence SHA-256 on every chunk;
3. polls until the endpoint returns 404 during safe-close.

## Re-entry condition

Before retrying, require the remote checkpoint still to be exactly:

```text
version            18
complete through   2026-09-08T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            null
unresolved attempts 0
```

If any field differs, stop and investigate instead of retrying the campaign.
