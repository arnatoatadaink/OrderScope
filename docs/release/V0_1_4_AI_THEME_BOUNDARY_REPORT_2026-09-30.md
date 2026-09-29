# v0.1.4 AI Theme boundary report — 2026-09-30

Status: **IMPLEMENTATION CANDIDATE READY FOR REVIEW; RELEASE BOUNDARY NOT ACCEPTED**

## Decision

The accepted reconstructed release line still ends at v0.1.3,
b4df4e911597d9f17bfa0a50b2057c24159dee9f. No v0.1.4 checkpoint,
tag, or main integration has been created. The v0.1.4 manifest remains
fail closed (apply_allowed=false; accepted source_commits=[]).

The canonical v0.1.4 scope is UWBS-062..066. Commit
cfc850c94738820f3b12e783791c9030edd216dc established the mapping from
historical AI-theme aliases UWBS-030..034. Those old IDs also identify the
accepted v0.1.3 Cross-Market lane, so old-ID matching is unsafe.

## Candidate implementation

The new candidate is isolated on codex/uwbs-062-066-ai-theme, based directly
on reconstructed v0.1.3:

| Source commit | Contribution |
| --- | --- |
| e018283549ccbb74ff5309fc4fe0b4addb91fa0d | Theme ontology/exposures, event hypotheses, cross-sectional observation, conservative state assessment, calibration summary and tests |
| c4f50c0878e001e8d6b031bf7f15ef188e3d4453 | Include the source event evidence in theme-state Interpretation lineage |

| Task | Implemented candidate behavior | Acceptance limit |
| --- | --- | --- |
| UWBS-062 | Versioned AI and adjacent theme identities; evidence-backed many-to-many structural exposure | No accepted company-theme registry population |
| UWBS-063 | Categorical event × theme hypotheses, with evidence and rationale; no numeric coefficient | No historically calibrated direction/strength matrix |
| UWBS-064 | Basket-relative return, breadth, volume coverage and persistence summaries as Derived Metric | Synthetic fixtures only; no accepted historical baskets |
| UWBS-065 | Candidate/confirmed activation, rotation and repricing states as Interpretation | Confirmation requires externally reviewed calibration criteria |
| UWBS-066 | Positive, negative, control and contradictory case classification and descriptive summary | No source-grounded reviewed historical case set or thresholds |

The diff from v0.1.3 contains only analysis/app/orderscope_local/theme/ and
analysis/tests/theme/test_theme.py. It imports accepted Fact Store contracts and
contains no PB work, later-version implementation, live provider operations,
or TypeScript changes.

## Verification

- Focused AI Theme tests: 12 passed.
- Full Python regression after the final code change: 626 passed, 2 warnings.
- Python compileall: passed.
- Diff check against v0.1.3: passed.
- TypeScript regression was not rerun because this candidate changes no TypeScript source.

The tests establish contract behavior, including many-to-many exposure,
multi-theme reactions, single-name rejection, missing-volume restraint,
event-evidence lineage and conservative uncalibrated states. Synthetic
observations in tests do not establish historical market calibration.

## Remaining boundary work

1. Freeze source-grounded positive, negative, control and contradictory
   historical cases with event, member, benchmark, window, return, volume,
   persistence and provenance references.
2. Review those cases and publish versioned empirical criteria. Validate
   false positives and mixed regimes, including single-name moves.
3. Review the complete v0.1.3-to-v0.1.4 export and package diff and rerun the
   kickoff acceptance gates on the final candidate.
4. Only then place accepted source commits in the replay allowlist and create
   one cumulative synthetic v0.1.4 boundary on release/reconstructed-v0.1.

The earlier source audit and current fail-closed manifest are
V0_1_4_AI_THEME_SOURCE_INVENTORY_2026-09-29.md and
v0.1.4-replay-manifest.json. Detailed implementation notes remain in
V0_1_4_AI_THEME_IMPLEMENTATION_PROGRESS_2026-09-30.md.
