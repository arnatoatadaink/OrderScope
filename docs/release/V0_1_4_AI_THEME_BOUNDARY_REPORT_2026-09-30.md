# v0.1.4 AI Theme boundary report — 2026-09-30

Status: **EXPERIMENTAL / UNCALIBRATED ACCEPTED; SYNTHETIC BOUNDARY PUSHED**

## Decision

v0.1.4 is accepted for release as an **experimental analytical capability**.
Historical market calibration is explicitly not a release blocker for the v0.1 development series.

The accepted reconstructed parent remains:

```text
v0.1.3 = b4df4e911597d9f17bfa0a50b2057c24159dee9f
v0.1.4 = a798622f839b836f8b60f52dd700b8fd87147991
```

The canonical v0.1.4 scope is UWBS-062..066. Commit
`cfc850c94738820f3b12e783791c9030edd216dc` established the mapping from
historical AI-theme aliases UWBS-030..034. Those old IDs also identify the
accepted v0.1.3 Cross-Market lane, so old-ID matching remains unsafe.

## Release classification

v0.1.4 must be interpreted as:

```text
AI Theme — Experimental / Uncalibrated
```

Accepted:

- versioned AI / adjacent theme ontology;
- evidence-backed many-to-many structural exposure;
- categorical event × theme hypotheses;
- cross-sectional relative-return / breadth / volume / persistence observation;
- provisional activation / rotation / repricing states;
- calibration-case representation and descriptive summaries;
- regression-tested contract behavior and conservative failure modes.

Not yet empirically validated:

- historical confirmation thresholds;
- false-positive rate;
- persistence thresholds;
- calibrated event × theme direction / strength matrix;
- accepted company-theme registry population;
- economic materiality interpretation;
- revenue / gross-profit / operating-profit attribution to theme exposure.

These limitations must remain visible in release notes and downstream interpretation.

## Accepted candidate source

The implementation candidate is isolated on `codex/uwbs-062-066-ai-theme`, based directly on reconstructed v0.1.3:

| Source commit | Contribution |
| --- | --- |
| `e018283549ccbb74ff5309fc4fe0b4addb91fa0d` | Theme ontology/exposures, event hypotheses, cross-sectional observation, conservative state assessment, calibration summary and tests |
| `c4f50c0878e001e8d6b031bf7f15ef188e3d4453` | Include source event evidence in theme-state Interpretation lineage |

These two commits are accepted as the v0.1.4 experimental source allowlist.

## Task boundary

| Task | Accepted experimental behavior | Known limitation |
| --- | --- | --- |
| UWBS-062 | Versioned AI and adjacent theme identities; evidence-backed many-to-many structural exposure | Company-theme registry remains incomplete and requires later source-backed population |
| UWBS-063 | Categorical event × theme hypotheses with evidence and rationale | No historically calibrated numeric coefficient matrix |
| UWBS-064 | Basket-relative return, breadth, volume coverage and persistence summaries as Derived Metric | Historical basket validation incomplete |
| UWBS-065 | Candidate/confirmed activation, rotation and repricing states as Interpretation | Confirmed states remain provisional until empirical criteria are calibrated |
| UWBS-066 | Positive, negative, control and contradictory case classification and descriptive summary | Threshold calibration remains future work |

The v0.1.3→candidate diff contains only `analysis/app/orderscope_local/theme/` and
`analysis/tests/theme/test_theme.py`. It imports accepted Fact Store contracts and contains no PB work, later-version implementation, live provider operations, or TypeScript changes.

## Verification

- Focused AI Theme tests: **12 passed**.
- Full Python regression after the final code change: **626 passed, 2 warnings**.
- Python compileall: **PASS**.
- Diff check against v0.1.3: **PASS**.
- TypeScript regression was not rerun because this candidate changes no TypeScript source.

The verification establishes software-contract behavior, not historical-market accuracy.

## Experimental interpretation policy

AI Theme must not collapse theme relevance, commercial evidence, persistence and profitability into one score.

Use four independent axes:

```text
Theme Exposure
× Evidence Maturity
× Economic Materiality
× Persistence
```

A company can therefore be strongly AI-related while still having unverified economic benefit.

Examples:

```text
AI_APPLICATION
Evidence Maturity = NEWS_ONLY
Economic Materiality = UNKNOWN
Persistence = UNCONFIRMED
```

and

```text
AI_FOUNDATION
Evidence Maturity = RECURRING_COMMERCIAL
Economic Materiality = MATERIAL
Persistence = CONFIRMED
```

must remain semantically distinct.

## Evidence maturity extension

The next analytical extension should model the progression:

```text
NEWS
  -> NARRATIVE
  -> COMMERCIAL_EVIDENCE
  -> RECURRING_EVIDENCE
  -> PROFIT_ATTRIBUTED
```

Suggested meaning:

- **NEWS**: first announcement, partnership, startup support, PoC, MOU, planned deployment.
- **NARRATIVE**: surrounding market narrative / policy / peer / thematic expectation without company-specific realized economics.
- **COMMERCIAL_EVIDENCE**: explicit contract, order, recognized revenue, disclosed customer use, or other realized commercial evidence.
- **RECURRING_EVIDENCE**: repeated evidence in a later period, such as a second earnings cycle, renewal, expanded order, or recurring revenue contribution.
- **PROFIT_ATTRIBUTED**: the theme contribution can be linked to gross profit, operating profit or free cash flow with sufficiently explicit source evidence.

Do not label promotional or weakly supported AI announcements as fraud or deception without evidence. Use observable classifications such as:

```text
PROMOTIONAL_ONLY
UNVERIFIED_COMMERCIAL_CLAIM
NO_REVENUE_EVIDENCE
NO_REPEAT_EVIDENCE
ECONOMIC_MATERIALITY_UNKNOWN
```

This preserves the Fact / Derived Metric / Interpretation boundary.

## Deferred calibration work

Historical calibration remains required for later confidence upgrades, but no longer blocks the v0.1.4 development release. Follow-up work should:

1. freeze positive / negative / contradictory / control historical cases;
2. derive versioned empirical thresholds;
3. measure false positives and single-name misclassification;
4. validate persistence and mixed-regime behavior;
5. add economic-materiality and profit-attribution evidence contracts.

Until that work is accepted, all empirically derived confirmation criteria must remain explicitly experimental or provisional.

## Release action

The two accepted source commits were replayed into one cumulative synthetic v0.1.4 checkpoint, `a798622f839b836f8b60f52dd700b8fd87147991`, on `release/reconstructed-v0.1` and pushed to origin. Its parent is exactly `b4df4e911597d9f17bfa0a50b2057c24159dee9f`. Local acceptance passed: 12 focused tests, 626 full Python tests with 2 warnings, compileall and diff check. No TypeScript source changed.

Historical empirical confirmation thresholds are not validated. False-positive rate is not validated on accepted historical samples. Persistence criteria are provisional. Economic materiality is not validated. Profit attribution is not implemented as an accepted validation layer.

No tag or `main` integration is implied by this decision.
