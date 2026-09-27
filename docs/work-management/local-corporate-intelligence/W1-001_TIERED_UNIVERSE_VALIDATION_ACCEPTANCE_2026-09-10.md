# OrderScope — W1-001 Tiered Universe Validation Acceptance

Status: **Accepted with count discrepancy recorded**
Date: 2026-09-10
Scope: `stock_monitoring_v0.1_universe_spec.md` alignment / non-live only

## 1. Acceptance evidence

Local validation reported:

```text
Universe focused tests: 4/4 pass
Full tests: 117/117 pass
Typecheck: pass
Wrangler dry-run/build: pass
git diff --check: pass
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

The synchronized branch confirms that `src/universe.ts` implements the tiered price cadence model from the v0.1 Universe specification:

```text
Tier A -> 1Min
Tier B -> 15Min
Tier C -> 1Day
```

The synchronized tests explicitly verify the full profile cadence and provider-route mapping and fail closed on unknown profile names.

## 2. Count discrepancy

The authoritative v0.1 Universe list currently contains:

```text
Tier A = 25
Tier B = 28
Tier C = 53
Total  = 106
```

This is consistent between the specification list and `src/universe.ts`, and the synchronized test now asserts 106 instruments.

However, prior operational planning repeatedly referred to a 105-instrument target. Therefore the implementation/spec alignment is accepted, but the **105 vs 106 planning discrepancy remains unresolved**.

Do not remove or reclassify a symbol merely to force the count to 105. A separate explicit Universe decision must identify whether:

1. 106 is the intended final v0.1 count and planning documents should be corrected; or
2. one listed instrument is a legacy/placeholder entry and should be removed by an explicit revision.

## 3. Budget implication

The earlier `105 x all-1Min` simplification is invalid for the current implementation. Stage B resource projection must use the actual mixed cadence profile and must currently model 106 instruments until the count discrepancy is resolved.

The count discrepancy does not block the current `canary-v0.1` profile, which remains a separate five-instrument profile. It does block declaring a final full-v0.1 daily write/backlog budget based on a presumed count of 105.

## 4. State

```text
Tier/cadence implementation alignment -> Accepted
Universe focused/full/typecheck/build/diff -> Accepted
Live/runtime mutation -> not authorized / not performed
105 vs 106 final Universe count -> unresolved planning discrepancy
W1-001 Stage B -> remains preflight/instrumentation gated
```

## 5. Next action

Resolve the 105-vs-106 Universe count explicitly, then run the tiered full-profile projection for:

- NEW bars/day by cadence;
- overlap/MATCHED observations/day;
- Market D1 rows written/day;
- News D1 rows written/day;
- total D1 rows written/day;
- combined D1 queries/tick;
- combined external subrequests/tick;
- maximum backlog age by cadence.

No remote D1, Worker deploy, Cron change, or Worker mode change is authorized by this acceptance.