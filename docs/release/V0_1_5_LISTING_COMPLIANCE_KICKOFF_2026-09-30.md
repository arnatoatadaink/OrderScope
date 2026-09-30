# OrderScope v0.1.5 Listing Compliance kickoff — 2026-09-30

Status: **IMPLEMENTATION REQUIRED / RELEASE BOUNDARY NOT YET CREATED**

## 1. Parent boundary

The cumulative reconstructed release line is accepted through v0.1.4:

```text
v0.1.4 = a798622f839b836f8b60f52dd700b8fd87147991
```

v0.1.5 must be constructed cumulatively on top of that boundary. Do not branch from historical main or from the old pre-reconstruction line.

## 2. Canonical scope

Canonical version ownership:

```text
v0.1.5 = UWBS-067
lane   = Listing Compliance / Earnings Repricing Canary
```

Historical alias:

```text
UWBS-035 -> UWBS-067
```

The historical alias is unsafe for source selection because `UWBS-035` also identifies accepted v0.1.3 Cross-Market work. Use canonical ID plus code/path/behavior review rather than commit-subject matching alone.

Canonical remap authority:

```text
cfc850c94738820f3b12e783791c9030edd216dc
```

## 3. Existing source evidence

The reviewed historical candidates are planning/design provenance only:

| SHA | Role | Release decision |
| --- | --- | --- |
| `1d158642f98ae57c2cd38ce76059b34b29426abb` | LVWR price-rediscovery case report | DESIGN_PROVENANCE_ONLY |
| `d7eaffec4371a3594fcbc561cc1f2df5d136b059` | Listing-compliance repricing backlog registration | DESIGN_PROVENANCE_ONLY |
| `cfc850c94738820f3b12e783791c9030edd216dc` | canonical ID registry | DOC_ONLY / audit authority |

No verified UWBS-067 implementation closeout was identified in the earlier readiness pass. v0.1.5 is therefore an implementation lane, not a replay-only reconstruction lane.

## 4. Intended capability boundary

v0.1.5 should implement a conservative Listing Compliance / Earnings Repricing contract that can represent the following without converting uncertainty into Fact:

1. observed exchange/listing compliance events;
2. explicit issuer/exchange notices about deficiency, cure, extension, hearing, suspension or delisting;
3. relevant price-threshold / minimum-bid context only when its source and applicable rule are explicit;
4. earnings or company-specific evidence that may explain repricing around the compliance period;
5. a Canary interpretation that separates compliance-risk relief from unrelated price moves.

The lane must preserve the project-wide boundary:

```text
source notice / filing / observed price              -> Fact
rule-derived compliance state                        -> Derived Metric or structured state
"listing relief caused repricing"                    -> Interpretation
future price target / investment action               -> out of scope
```

## 5. Suggested package decomposition

A compact v0.1.5 implementation is preferred. Suggested structure:

```text
analysis/app/orderscope_local/listing_compliance/
  __init__.py
  models.py
  rules.py
  canary.py

analysis/tests/listing_compliance/
  test_listing_compliance.py
```

The exact filenames may differ if an existing package owns the contract cleanly. Avoid duplicating existing Fact Store, market-reaction, repricing-state or earnings models.

## 6. Minimum contract

### ListingComplianceEvent / evidence

Represent at minimum:

- instrument/company reference;
- venue/exchange;
- event type;
- event/available/accepted timestamps;
- source/evidence references;
- explicit rule reference where applicable;
- observed status only, without inferring issuer intent.

Candidate event vocabulary:

```text
DEFICIENCY_NOTICE
COMPLIANCE_PERIOD_STARTED
COMPLIANCE_REGAINED
EXTENSION_GRANTED
HEARING_REQUESTED
HEARING_DECISION
SUSPENSION_ANNOUNCED
DELISTING_ANNOUNCED
DELISTING_EFFECTIVE
UNKNOWN
```

Do not hard-code this exact vocabulary if repository conventions require a different naming scheme; preserve the semantics.

### Compliance state

A derived/structured state may distinguish:

```text
COMPLIANT
DEFICIENT
CURE_WINDOW_ACTIVE
REGAINED_PENDING_CONFIRMATION
REGAINED_CONFIRMED
DELISTING_RISK_ACTIVE
DELISTING_EFFECTIVE
UNKNOWN
```

The state must be source-grounded and must not infer exchange decisions not present in evidence.

### Repricing Canary

The Canary should test whether listing-compliance evidence and earnings/company evidence can be evaluated together without collapsing them into one causal Fact.

At minimum cover:

- compliance regained + positive earnings / repricing;
- compliance regained but no durable repricing;
- positive repricing without compliance evidence;
- deficiency remains active despite temporary price recovery;
- contradictory or missing evidence -> UNKNOWN / candidate only.

LVWR may be used as the motivating fixture, but the implementation should be generic and must not encode LVWR-specific values as universal rules.

## 7. Acceptance philosophy

v0.1.5 is part of the v0.1 development series. As with v0.1.4, empirical market calibration may remain incomplete if the limitation is explicit.

Allowed development-release posture:

```text
contract behavior tested                  = required
full regression                           = required
compile/typecheck/diff check              = required
historical false-positive calibration     = may remain experimental
causal repricing attribution              = must remain provisional
```

Do not block v0.1.5 solely because historical reaction thresholds are not calibrated. Do block it for contract ambiguity, Fact/Interpretation leakage, failing regression, or missing source lineage.

## 8. Local implementation workflow

Recommended development branch:

```text
codex/uwbs-067-listing-compliance
```

Base it on the accepted reconstructed v0.1.4 boundary:

```bash
git fetch origin release/reconstructed-v0.1 release/reconstruction-tools

git switch --detach a798622f839b836f8b60f52dd700b8fd87147991
git switch -c codex/uwbs-067-listing-compliance
```

Before coding:

```bash
git status --short
git rev-parse HEAD
```

Expected parent:

```text
a798622f839b836f8b60f52dd700b8fd87147991
```

## 9. Required tests

Focused tests must cover at least:

1. event/source provenance validation;
2. UTC/as-of semantics consistent with repository contracts;
3. deficiency -> cure-window -> regained progression where supported;
4. invalid or unsupported transition rejection;
5. no causal claim from price movement alone;
6. earnings/company evidence remains distinct from listing evidence;
7. contradictory/missing evidence remains UNKNOWN or candidate;
8. serialization/export surface if the package exposes public contracts.

After focused tests pass, run the repository-wide acceptance commands appropriate to the current tree, including:

```bash
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check a798622f839b836f8b60f52dd700b8fd87147991..HEAD
```

Run TypeScript tests/typecheck if TypeScript sources, generated/shared contracts, package wiring, or root build surface changed. If no TypeScript-relevant change occurs, record that fact explicitly rather than silently omitting the check.

## 10. Release-boundary preparation

After implementation acceptance, produce:

```text
docs/release/V0_1_5_LISTING_COMPLIANCE_IMPLEMENTATION_PROGRESS_2026-09-30.md
docs/release/V0_1_5_LISTING_COMPLIANCE_BOUNDARY_REPORT_2026-09-30.md
docs/release/v0.1.5-replay-manifest.json
```

The v0.1.5 manifest should contain only accepted implementation/test/fix/export commits from the UWBS-067 development branch. Historical design commits `1d158642...` and `d7eaffec...` remain provenance unless their documentation is intentionally carried into the release snapshot.

## 11. Synthetic boundary

Once accepted, create one cumulative synthetic v0.1.5 checkpoint on top of v0.1.4, preserving source history unchanged.

Target lineage:

```text
v0.1.4  a798622f...
   |
   v
v0.1.5  <new synthetic SHA>
```

Do not create a tag or integrate main merely as a side effect of constructing the boundary.

## 12. Stop conditions

Stop and report instead of auto-resolving when any of the following occurs:

- the local base is not the accepted v0.1.4 boundary;
- an implementation change requires importing v0.1.6+ logical-lane code;
- an existing contract already owns the semantic concept and duplication would result;
- Fact and Interpretation cannot be separated cleanly;
- tests fail outside the touched lane;
- a historical LVWR-specific value is about to become a universal threshold without calibration;
- remote/live mutation would be required for acceptance.

## 13. Expected handoff summary

At completion report:

```text
v0.1.5 UWBS-067
parent: a798622f839b836f8b60f52dd700b8fd87147991
implementation commits: <SHAs>
focused tests: <count> passed
full Python: <count> passed
compileall: PASS/FAIL
TypeScript: PASS / not required with reason
diff check: PASS/FAIL
release classification: Experimental or Accepted
remaining empirical limitations: <explicit list>
synthetic boundary: <SHA or not yet created>
```

## 14. Non-goals

v0.1.5 does not implement the v0.1.6 Crypto lane, execute trades, infer exchange intent, establish a universal delisting probability model, or turn one historical LVWR case into a calibrated market rule.
