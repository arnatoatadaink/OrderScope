# UWBS-086 — Historical Canary + Worker/D1 Capacity Acceptance

Status: **WEB IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**

## Objective

Close the oil/BTC cross-asset lane with a replay-only Canary and resource-capacity acceptance gate before any live activation.

## Boundary

UWBS-086 evaluates checked-in fixture/historical scenarios and modeled resource observations only. It does **not** authorize or perform provider activation, Worker/Cron mutation, D1 mutation, paid procurement, or trading action.

### Canary result

Each scenario preserves:

- stable `scenario_id`;
- expected regime;
- observed regime;
- expected alert state;
- observed alert state.

The assessment exposes false-positive, false-negative and regime-mismatch counts.

### Decision rule

```text
capacity headroom < configured minimum -> REJECT
false negative > 0                   -> REJECT
regime mismatch > 0                  -> REJECT
false positive > 0                   -> REVIEW
otherwise                            -> ACCEPT
```

The default capacity headroom floor is 20%. This is an OrderScope acceptance guard, not a claim about a Cloudflare product quota. Provider/platform quotas remain external configuration/evidence and must be refreshed before live deployment.

## Capacity observation

The replay contract records modeled/observed daily quantities for:

- Worker requests;
- D1 rows written;
- D1 bytes written;
- scheduled invocations;
- remaining headroom ratio.

The contract intentionally does not hard-code Cloudflare plan limits. A later live/canary execution packet must compare these quantities with the then-current account/plan limits.

## Acceptance sequence

```text
focused historical-canary contract tests
  -> full Python regression
  -> compileall
  -> git diff --check
  -> inspect representative historical fixtures
  -> capacity decision
```

A clean local contract regression only accepts the software boundary. Final UWBS-086 closure additionally requires historical scenario evidence and a capacity observation with adequate headroom.
