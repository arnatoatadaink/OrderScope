# OrderScope — CS0 / MR0 Local Acceptance Handoff

Status: **READY FOR LOCAL ACCEPTANCE REVIEW**
Date: 2026-09-15
Branch: `docs/mermaid-conventions-v0.1`
Formal WBS: `docs/WORK_BREAKDOWN_CAPITAL_STRUCTURE_MARKET_REACTION_2026-09-15.md`

## 1. Purpose

The formal WBS now maps:

- `UWBS-017..019` -> `CS0-001..003`
- `UWBS-020..022` -> `MR0-001..003`

Repository inspection shows that a substantial implementation already exists under the former UWBS identifiers. Therefore the next safe closed-market action is **local acceptance/reconciliation**, not blind reimplementation.

Do not mark any CS0/MR0 task Accepted from this document alone. Local test evidence and boundary review remain required.

## 2. Existing implementation discovered

### CS0-001 / former UWBS-017

Existing files include:

- `analysis/app/orderscope_local/contracts/capital_instrument.py`
- `analysis/app/orderscope_local/contracts/capital_instrument_state.py`
- `analysis/tests/contracts/test_capital_instrument_fact.py`
- `analysis/tests/contracts/test_capital_instrument_state.py`

Observed contract characteristics:

- capital instrument is represented as a source-grounded lifecycle Fact;
- instrument and issuer identities are explicit;
- state transition validation exists;
- provenance and accepted time must agree;
- maturity and conversion-window dates are source timestamps;
- principal/currency and conversion discount are bounded;
- state history can reference a previous state record.

### CS0-002 / former UWBS-018

Existing files include:

- `analysis/app/orderscope_local/contracts/debt_resolution.py`
- `analysis/tests/contracts/test_debt_resolution.py`

Observed boundary:

- `DebtResolutionWindowAssessment` produces an Interpretation, not a repayment Fact;
- terminal/resolved instruments cannot enter a new resolution window;
- instrument/timing/financing/use-of-proceeds evidence classes are kept distinct;
- elevated attention requires both financing and explicit repayment-use evidence;
- output records `outcome_prediction = none` and `threshold_policy = not_fixed_v0.1`.

### CS0-003 / former UWBS-019

Existing files include:

- `analysis/app/orderscope_local/contracts/capital_structure.py`
- `analysis/tests/contracts/test_capital_structure.py`

Observed boundary:

- convertible-note overhang removal is separate from total issuer dilution removal;
- a terminal convertible-note state is required;
- residual instruments can be retained explicitly;
- `ResidualDilutionState.REMAINS` requires residual-instrument lineage;
- higher-level capital-structure regime output remains Interpretation.

### MR0-001 / former UWBS-020

Existing files include:

- `analysis/app/orderscope_local/contracts/catalyst_reaction_window.py`
- `analysis/tests/contracts/test_catalyst_reaction_window_basic.py`
- `analysis/tests/contracts/test_catalyst_reaction_window_validation.py`

Acceptance review should confirm that fixed observation windows remain deterministic/session-aware and that market response is represented as measurement rather than catalyst causation.

### MR0-002 / former UWBS-021

Existing files include:

- `analysis/app/orderscope_local/contracts/catalyst_repricing_types.py`
- `analysis/app/orderscope_local/contracts/catalyst_repricing_assessment.py`
- `analysis/app/orderscope_local/contracts/catalyst_repricing_materialize.py`
- `analysis/tests/contracts/test_catalyst_repricing.py`

Observed boundary:

- initial reaction must contradict the catalyst for divergence/delayed-repricing assessment;
- delayed repricing requires later reaction evidence aligned with the catalyst;
- evidence classes cannot overlap;
- divergence cannot silently include later confirmation.

Acceptance review must additionally confirm coverage of the full formal MR0-002 state set, including spike / discovery / equilibrium / confirmed / failed states. Existing filenames prove implementation presence, not necessarily complete WBS coverage.

### MR0-003 / former UWBS-022

The formal WBS requires TNON/CHPT historical Canary fixtures plus false positives. During this Web-side pass, contract tests were located, but a complete task-specific TNON/CHPT fixture acceptance artifact was not established. Treat MR0-003 as **acceptance pending** until the local run proves the required fixtures exist and pass.

## 3. Local acceptance sequence

Run from the repository root using the existing project environment. Prefer the already-used environment path that does not rewrite dependency locks.

Suggested focused command:

```bash
uv run --no-sync pytest -q \
  analysis/tests/contracts/test_capital_instrument_fact.py \
  analysis/tests/contracts/test_capital_instrument_state.py \
  analysis/tests/contracts/test_debt_resolution.py \
  analysis/tests/contracts/test_capital_structure.py \
  analysis/tests/contracts/test_catalyst_reaction_window_basic.py \
  analysis/tests/contracts/test_catalyst_reaction_window_validation.py \
  analysis/tests/contracts/test_catalyst_repricing.py
```

Then run the full Python suite using the repository's normal accepted command, followed by:

```bash
python -m compileall analysis/app

git diff --check

git status --short
```

Do not update lock/dependency files merely to execute this acceptance pass.

## 4. Required review matrix

| Formal task | Implementation presence | Local acceptance required | Key review question |
|---|---|---|---|
| CS0-001 | Present | Yes | Are all allowed/forbidden lifecycle transitions and provenance/history rules tested? |
| CS0-002 | Present | Yes | Can financing/use-of-proceeds raise attention without becoming predicted repayment? |
| CS0-003 | Present | Yes | Is instrument-specific overhang removal kept distinct from total dilution removal? |
| MR0-001 | Present | Yes | Are observation windows deterministic/session-aware and non-causal? |
| MR0-002 | Present | Yes | Does implementation cover the complete formal state machine without fixed thresholds? |
| MR0-003 | Partial/uncertain from Web inspection | Yes | Do TNON + CHPT + all required false-positive fixtures exist and pass? |

## 5. Acceptance disposition rules

For each task choose exactly one:

```text
ACCEPTED
  = focused tests + required full suite pass and WBS completion condition is covered.

PROVISIONAL
  = implementation is present and tests pass, but one formal WBS boundary/fixture remains incomplete.

BLOCKED
  = a missing dependency/source fixture prevents completion.

FAILED
  = deterministic contract/test behavior violates the formal WBS boundary.
```

Do not use `ACCEPTED` merely because files exist.

## 6. Closed-market suitability

All work in this acceptance pass is valid while U.S. markets are closed:

- contract review;
- fixture/historical replay;
- deterministic unit/integration tests;
- compile/static checks;
- WBS/CP reconciliation.

No fresh-session evidence is required for CS0-001..003 contract acceptance or MR0-001/002 deterministic acceptance. MR0-003 may use historical TNON/CHPT data. Any future live post-catalyst observation is a separate market-day-gated validation and is not required to complete this pass unless the WBS is later amended.

## 7. Runtime/change-control boundary

This handoff does not authorize:

- Worker/Cron changes;
- live provider activation;
- remote D1 mutation;
- purge;
- live trading signal activation;
- fixed numeric price/attention thresholds.

## 8. Return evidence

Return the following to the integrated Progress Tracker after local execution:

```text
focused tests: <passed/failed count>
full Python suite: <passed/failed count>
compileall: <result>
git diff --check: <result>
git status --short: <result>
CS0-001 disposition:
CS0-002 disposition:
CS0-003 disposition:
MR0-001 disposition:
MR0-002 disposition:
MR0-003 disposition:
missing formal-WBS coverage, if any:
files changed, if any:
```

If MR0-003 fixture coverage is missing, implement only the smallest deterministic historical fixture slice needed to cover TNON, CHPT and the listed false-positive cases; do not introduce normative thresholds during that repair.
