# v0.1.4 AI Theme source inventory — 2026-09-29

Status: **BLOCKED: accepted implementation inventory absent; new candidate in development**

Parent boundary: `b4df4e911597d9f17bfa0a50b2057c24159dee9f` (reconstructed v0.1.3). No v0.1.4 synthetic commit or tag has been created.

## Canonical ID mapping

Commit `cfc850c94738820f3b12e783791c9030edd216dc` introduced `WBS_PROVISIONAL_ID_REGISTRY.md`, which resolves the old AI design IDs. The old IDs also denote accepted Cross-Market work, so they cannot identify AI source commits by themselves.

| Historical AI alias | Canonical ID | Expected capability |
| --- | --- | --- |
| UWBS-030 | UWBS-062 | Theme ontology and multi-theme exposure |
| UWBS-031 | UWBS-063 | Event × theme reaction coefficient |
| UWBS-032 | UWBS-064 | Cross-sectional reaction confirmation |
| UWBS-033 | UWBS-065 | Activation, rotation and repricing states |
| UWBS-034 | UWBS-066 | Historical calibration and Canary fixtures |

The release plan reserves v0.1.4 for this lane and explicitly says there is no verified closeout in its reviewed branch. Reservation and numbering do not establish implementation acceptance.

## Classified source candidates

| Source SHA | Role | Paths and decision |
| --- | --- | --- |
| `26212936cd2e0ac148e328f22bf58fe7ee59e6ce` | DESIGN_PROVENANCE_ONLY | Adds `REPORT_AI_THEME_DECOMPOSITION_REACTION_COEFFICIENTS_2026-09-15.md`; retain as design evidence, do not replay into the release snapshot. |
| `49523f52a50136d5d8301d30b1345cfcd9f88aea` | DESIGN_PROVENANCE_ONLY | Adds AI planning rows to `WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md` under old UWBS-030..034; do not replay those colliding identifiers. |
| `cfc850c94738820f3b12e783791c9030edd216dc` | DOC_ONLY_OPTIONAL | Establishes canonical mapping in `WBS_PROVISIONAL_ID_REGISTRY.md`; use for the audit, not as capability implementation. |
| `b7fbd251c12bf3fb163284dc104aac8a37abdbbd`, `d82eae9939b0ca73ced03685226ef09f89f3b537` | OTHER_VERSION | UWBS-086 historical Canary includes `H2_AI_THEME_FLOW`, a cross-market hypothesis, not the UWBS-062..066 theme ontology/reaction lane. |
| `74183b4bf68892ef1b081e6dd84fd183ed7dcda0` | OTHER_VERSION | UWBS-093 Physical-SaaS Canary; not AI Theme calibration. |

No candidate has been classified as MUST_REPLAY_IMPLEMENTATION, MUST_REPLAY_TEST, MUST_REPLAY_EXPORT, or MUST_REPLAY_ACCEPTANCE_CONTENT. There is consequently no source allowlist for a v0.1.4 replay.

## Search and dependency result

After refreshing all origin refs, the audit checked commit subjects for UWBS-062..066 and AI-theme terminology; the origin/main registry, backlog, release plan and current tracking documents; and analysis application/test paths on origin/main. The code tree has no AI-theme ontology, reaction coefficient, theme-state or calibration path. The only found `H2_AI_THEME_FLOW` implementation belongs to the separate UWBS-086 historical Canary. Current planning documents list the AI lane, but provide no accepted implementation closeout.

Reconstructed v0.1.3 already contains market relationship, market reaction, relative repricing and macro primitives. These are potential shared prerequisites, not evidence that the AI lane has been implemented. No later-version capability should be pulled in to fill the gap.

## Release decision

`v0.1.4-replay-manifest.json` is fail closed: `apply_allowed` is false and all five canonical tasks have unresolved implementation, test, export and acceptance roles. Do not create an empty synthetic checkpoint or relabel v0.1.3 as v0.1.4. Re-audit when accepted UWBS-062..066 source commits and local acceptance evidence exist, then freeze an exact source allowlist and run the kickoff acceptance gates.

## 2026-09-30 development update

New candidate implementation is isolated on codex/uwbs-062-066-ai-theme at
e018283549ccbb74ff5309fc4fe0b4addb91fa0d and c4f50c0878e001e8d6b031bf7f15ef188e3d4453. It provides the five task areas as code and synthetic contract tests,
but is not accepted historical calibration evidence. See
V0_1_4_AI_THEME_IMPLEMENTATION_PROGRESS_2026-09-30.md. The accepted replay
allowlist remains empty and apply_allowed remains false.
