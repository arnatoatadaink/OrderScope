# v0.1.4 AI Theme implementation progress — 2026-09-30

Status: **CANDIDATE IMPLEMENTATION; RELEASE BOUNDARY NOT ACCEPTED**

The accepted reconstructed parent remains b4df4e911597d9f17bfa0a50b2057c24159dee9f (v0.1.3). New work is isolated on branch codex/uwbs-062-066-ai-theme at commits e018283549ccbb74ff5309fc4fe0b4addb91fa0d and c4f50c0878e001e8d6b031bf7f15ef188e3d4453 and has not been added to release/reconstructed-v0.1.

## Candidate source

| Canonical task | Candidate content |
| --- | --- |
| UWBS-062 | Versioned AI/adjacent theme hierarchy and evidence-backed, many-to-many structural exposures |
| UWBS-063 | Event × theme categorical direction hypotheses, with event evidence and no fixed numeric coefficient |
| UWBS-064 | Cross-sectional relative-return, volume, breadth and persistence observations, materialized as Derived Metric |
| UWBS-065 | Conservative activation, rotation and repricing states, materialized as Interpretation |
| UWBS-066 | Historical-case classification and descriptive calibration summary; no automatic threshold generation |

Source commits: e018283549ccbb74ff5309fc4fe0b4addb91fa0d and c4f50c0878e001e8d6b031bf7f15ef188e3d4453. The candidate adds analysis/app/orderscope_local/theme/ and analysis/tests/theme/test_theme.py. It depends on the accepted v0.1.3 Fact Store contracts and does not import later logical lanes. It contains no PB or live provider operations.

## Local validation

- AI Theme focused tests: 12 passed.
- Full Python regression: 626 passed, 2 warnings.
- Python compileall: passed.
- Diff check against v0.1.3: passed.
- TypeScript source was unchanged.

The focused tests use synthetic market observations to verify contract behavior. They are not historical calibration evidence.

## Remaining acceptance gates

1. Assemble source-grounded positive, negative, contradictory and control historical cases for the relevant event/theme pairs. Preserve news/event refs, member baskets, benchmark, time windows, volume and persistence lineage.
2. Review the cases and derive versioned empirical confirmation criteria. Current CalibratedCriteria accepts externally supplied reviewed criteria; this commit does not claim a validated threshold.
3. Validate false positives, single-name cases and mixed regimes with accepted historical samples.
4. Review the package/export surface and the pure v0.1.3-to-v0.1.4 diff, then run the kickoff's full acceptance sequence against the final candidate.
5. Only after acceptance, freeze the source allowlist and create one synthetic cumulative v0.1.4 commit on release/reconstructed-v0.1. No tag or main integration is implied.

The existing v0.1.4-replay-manifest.json remains fail closed with an empty accepted source_commits list.
