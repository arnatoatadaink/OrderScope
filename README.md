# OrderScope

OrderScope is the Code of Truth repository for the Stock Monitoring Fact project.

## Code of Truth v0.1

The v0.1 Code of Truth consists of four normative documents under `docs/`.

### Parent specification

- `docs/stock_monitoring_v0.1_spec.md`
  - Integrated v0.1 specification and entry point.
  - Defines project purpose, scope, market analysis, calendar/session handling, corporate intelligence, source tiers, SEC/fundamental handling, Regime overview, Fact model, and Definition of Done.

### Reference specifications

- `docs/stock_monitoring_v0.1_universe_spec.md`
  - Fixed initial Universe, Tier A/B/C price cadences, themes, characters, and Universe update policy.
- `docs/stock_monitoring_v0.1_regime_spec.md`
  - Regime strength/status/history, provisional decay, contract handling, negative evidence, and reactivation.
- `docs/stock_monitoring_v0.1_provider_research.md`
  - Provider boundary, candidate APIs, current research notes, costs, and provider STUB requirements.

The parent specification is the entry point. The three reference specifications are part of the same v0.1 Code of Truth and are normative for their respective domains.

### Documentation conventions and traceability

- `docs/MERMAID_CONVENTIONS.md`
  - Non-normative, reusable guidance for Mermaid diagrams and requirement → high-level design → detailed design traceability.
- `docs/REQUIREMENTS_TRACEABILITY_v0.1.md`
  - Non-normative stable requirement IDs derived from the four v0.1 Code of Truth documents, including acceptance/verification links and unresolved design questions.
- `docs/HIGH_LEVEL_DESIGN_v0.1.md`
  - Provisional, non-normative high-level component boundaries mapped to the requirement IDs.
- `docs/DETAILED_DESIGN_CFG_PROVIDER_v0.1.md`
  - Detailed-design Slice 01 for `HLD-CFG-001 + HLD-PROV-001`: Universe configuration, provider-neutral schemas, provider contracts, timestamps, cursors, completeness and error boundaries.
- `docs/DETAILED_DESIGN_SCHEDULER_MARKET_v0.1.md`
  - Detailed-design Slice 02 for `HLD-SCH-001 + HLD-MKT-001`: acquisition jobs, coverage checkpoints, catch-up overlap, cadence/session normalization, idempotent bar acceptance and retry/failure boundaries.
- `docs/DESIGN_DECISIONS_v0.1.md`
  - Reversible implementation-level decisions. `DD-DEPLOY-001` currently selects Cloud + Main PC for the initial v0.1 deployment while keeping module contracts placement-independent.
- `docs/REPORT_VOLUME_FLOW_ALPACA_2026-08-28.md`
  - Non-normative report defining the volume / relative-volume / traded-notional proxy boundary, IEX-vs-SIP validation loop, and the distinction between observed OHLCV, Derived Metrics, and capital-flow interpretation.
- `docs/RUNBOOK_CLOUDFLARE_WORKER_SCHEDULE_v0.1.md`
  - Non-normative deployment/operations runbook for Cloudflare Worker + Cron acquisition and ChatGPT Scheduled Task digest consumption.
- `docs/IMPLEMENTATION_DECISIONS_WORKER_v0.1.md`
  - Provisional Worker implementation choices derived from the functional requirements, including D1/R2 responsibilities, cadence-vs-Attention semantics, RVOL baseline, notional activity proxy, digest exposure, IEX/SIP quality gating, volatility baseline and shadow-mode promotion criteria.
- `docs/WORK_PLAN_INITIAL_VALIDATION_AND_LONG_TERM_OPERATIONS_2026-09-01.md`
  - Non-normative phased work plan separating bounded live validation and D1-export-based local analysis from R2-backed long-term retention, reconciliation, recovery and prediction-research preparation.
- `docs/WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
  - Reviewable task breakdown for the next local-analysis, SEC/earnings, news, official-context, retention, and localhost integration phase; keeps remaining Worker operational checks as a separate backlog.
- `docs/REPORT_WEB_CORPORATE_INTELLIGENCE_WORKSTREAM_2026-09-03.md`
  - Cross-session map of the corporate-intelligence research and documentation that ChatGPT Web can complete or prepare, with explicit local handoff boundaries.
- `docs/WEB_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-03.md`
  - Active ledger for `WEB-001` through `WEB-020`, including dependencies, evidence links, session ownership, handoff state and next action.
- `docs/ADR_LOCAL_ANALYSIS_STACK_v0.1.md`
  - Accepted `L0-001` stack decision for the local MVP: Python/uv, SQLite/DuckDB, Arrow/Parquet, localhost API and the Windows/WSL execution boundary.
- `docs/ADR_FACT_STORE_LOGICAL_SCHEMA_v0.1.md`
  - Proposed `I0-005` logical boundary separating Fact, Evidence, Relationship, Derived Metric and Interpretation; acceptance remains gated by I0-002 provenance types and contract fixtures.
- `docs/REPORT_LOCAL_SEC_FORM_FILTER_S0_004_S0_007_2026-09-04.md`
  - Local `S0-004` strict SEC form filter implementation evidence and the completed fixture-only portion / remaining dependency boundary for `S0-007`.
- `docs/REPORT_LOCAL_COMMON_CONTRACT_TEST_KIT_I0_007_2026-09-04.md`
  - Local `I0-007` provider-neutral contract test kit for bounded pagination, timestamps, partial/retryable errors and secret non-exposure; adapter integration remains dependency-gated.
- `docs/REPORT_JAPAN_LOCAL_MARKET_DATA_OPTIONS_2026-09-03.md`
  - Current research on MARKET SPEED II RSS/Excel constraints, kabu Station API, J-Quants plans and safe Windows-to-WSL handoff options for local Japanese market data.
- `docs/PROVISIONAL_DESIGN_JP_US_PREDICTION_v0.1.md`
  - Non-normative Japan-to-U.S. prediction extension: separate predictor/target registries, Japan provider fallback, four U.S. Premarket/Regular horizons, as-of/leakage rules, provisional labels and probabilistic output contracts.
- `docs/PREDICTION_REGISTRY_SEMICONDUCTOR_CANARY_v0.1.md`
  - Evidence and limits for the first versioned Japanese semiconductor-input / U.S. theme-target canary profile.
- `docs/HANDOFF_LOCAL_JP_US_PREDICTION_2026-08-31.md`
  - Local continuation handoff for the provider-neutral immutable Japanese-input snapshot slice, including safety boundaries, required tests and completion criteria.

These derived documents do not add to or replace the four-document Code of Truth. Authoritative rules remain in the normative specifications above.

## Baseline

- Status: v0.1 fixed for implementation
- Target market: U.S. market
- Initial Universe: 106 fixed instruments (Tier A 25 / Tier B 28 / Tier C 53), with cadence defined in the Universe specification
- Initial market-data candidate: Alpaca
- SEC / Fundamental baseline: SEC EDGAR / XBRL
- Initial deployment design: Cloud acquisition + Main PC heavy analysis (reversible design decision)
- Initial Worker runtime: Cloudflare Worker shadow-mode scaffold with per-minute Cron wake-up
- Initial operational storage split: D1 for hot scheduler/checkpoint/digest state; R2 for long-lived/batched OHLCV archive (provisional implementation decision)
- Internal timestamps: UTC
- Market classification timezone: America/New_York
- Display timezone: Asia/Tokyo

## Local environment operation boundary

The complete setup, daily operation, verification, data, and secret-handling
sequence is in [`docs/RUNBOOK_LOCAL_ENVIRONMENT_WSL_WINDOWS_2026-09-21.md`](docs/RUNBOOK_LOCAL_ENVIRONMENT_WSL_WINDOWS_2026-09-21.md).
The rules below are the short, always-applicable boundary summary.

The local development environment uses a Windows-side source workspace and a WSL runtime:

| Operation | Execution location |
| --- | --- |
| Edit and save source with Codex Desktop | Windows-side source: `/mnt/c/Users/Y/Projects/codex_work/OrderScope` |
| Python dependency sync, Python tests, and the Local API | WSL, from the Windows-side source workspace, using `bash scripts/run-local-wsl.sh ...` and a WSL-native Python environment |
| `npm ci`, Node tests, and typecheck | WSL, from the Windows-side source workspace, with Node.js 24 selected and source-local `node_modules` |
| Wrangler commands and deploy dry-runs | WSL, from the Windows-side source workspace |
| Windows-native Python or Node execution | Not permitted for this project |

Run project commands from the canonical source workspace, for example:

```bash
cd /mnt/c/Users/Y/Projects/codex_work/OrderScope
source "$HOME/.nvm/nvm.sh"
nvm use
node --version                 # v24.21.0 from .nvmrc
bash scripts/run-local-wsl.sh sync
bash scripts/run-local-wsl.sh python -c 'import sys; print(sys.version); print(sys.executable)'
npm ci
bash scripts/run-local-wsl.sh env
bash scripts/run-local-wsl.sh api
```

`node_modules` remains a Linux/WSL runtime dependency generated under the Windows-side workspace. The Python project environment does **not** live under the source checkout; `scripts/run-local-wsl.sh` fixes `UV_PROJECT_ENVIRONMENT` to `${HOME}/.local/share/orderscope/venv` by default. A legacy source-local `.venv` may remain temporarily during migration, but the wrapper does not use it. Do not invoke the project with Windows-native Python or Node. The WSL-side copy at `/home/y/code/OrderScope` is a migration backup/comparison copy; while it is retained, do not edit or execute the project from that copy. Operational mutable data is canonical under `${HOME}/data/orderscope` in the WSL-native filesystem: Python uses `${HOME}/data/orderscope/local` through `ORDERSCOPE_DATA_ROOT`, and local Wrangler uses `${HOME}/data/orderscope/wrangler-state` through `--persist-to`. Use `bash scripts/run-local-wsl.sh ...` or `npm run dev` so these boundaries are applied. Do not open SQLite files concurrently from multiple processes or copies. See `docs/REPORT_LOCAL_DB_WSL_CANONICALIZATION_2026-09-20.md` for migration evidence and `docs/REPORT_LOCAL_ENVIRONMENT_MIGRATION_REMAINING_TASKS_2026-09-20.md` for remaining operational work.

If `/mnt/c` EIO reappears during `npm ci` or other heavy Node dependency I/O, stop the acceptance run and preserve the error output. The current design keeps source-local `node_modules` because MIG-09A could not reproduce the failure after restart and MIG-09C passed `npm ci`, 199 Node tests, and typecheck. A generated WSL-native runtime mirror is the first fallback to evaluate if the failure becomes reproducible; do not introduce `NODE_PATH`, source symlinks, or bind mounts ad hoc.

The initial data migration is reproducible with `bash scripts/migrate-local-data-to-wsl.sh`. It copies the Windows-side `var/` and `.wrangler/state/` into the WSL-native data root and writes a timestamped manifest there. The source-side directories remain as non-operational migration backups until the final acceptance and retention decision is complete.

Cloudflare environment safety is mandatory for deployment commands. Use an explicit
named environment for every deploy or dry-run:

```bash
npm run deploy:check -- --env live-canary
# or, for a shell-scoped default:
CLOUDFLARE_ENV=live-canary npm run deploy:check
```

The repository wrapper rejects an omitted environment and rejects a conflict between
`--env` and `CLOUDFLARE_ENV`. Remote D1 commands must likewise include the same
`--env <name>` value. Before any remote mutation, confirm the named Worker and D1
resource with the read-only checks below; `d1 info` is intentionally run against the
binding so the environment-specific resource is resolved from `wrangler.jsonc`:

```bash
npx wrangler d1 info STATE_DB --env live-canary
npx wrangler deployments list --env live-canary
```

Do not use an unqualified `npm run deploy`, `wrangler deploy`, or remote D1 command.

### Secret boundary

Keep the credential namespaces separate:

| Use | Environment variable names | Boundary |
| --- | --- | --- |
| Worker provider secret | `ALPACA_API_KEY`, `ALPACA_API_SECRET` | Cloudflare Worker Secret bindings; local Worker development may read the ignored `.env` |
| Python local adapter | `ORDERSCOPE_SECRET_ALPACA_API_KEY`, `ORDERSCOPE_SECRET_ALPACA_API_SECRET` | WSL process environment only; read by the registered adapter boundary |
| Wrangler administration | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` | Wrangler read-only/admin commands only; never a Worker binding |

Do not rely on automatic conversion between the Worker and Python names. If the
same provider credential is intentionally used for a local adapter check, pass
it explicitly to the `ORDERSCOPE_SECRET_*` names in one WSL process and do not
save the converted values, put them in command arguments, or record them in
logs, manifests, or reports. Keep `.env` and `.env.cloudflare` ignored by Git.
On the WSL-native filesystem, keep any retained dotenv copy at mode `600`.
The `/mnt/c` source workspace is a drvfs mount, so its WSL mode display is not
a reliable native-filesystem permission check; do not treat that copy as the
WSL secret store.

For Wrangler read-only identity checks, use the existing WSL Wrangler profile
or a separately approved short-lived management credential. Do not include
`.env.cloudflare` in `wrangler types` input or Worker bindings. Use an explicit
environment for every remote check, for example:

```bash
npx wrangler whoami
npx wrangler d1 info STATE_DB --env live-canary
```

See `docs/REPORT_LOCAL_SECRET_BOUNDARY_TASK_8_2026-09-21.md` for the value-free
verification record and the `/mnt/c` versus WSL-native permission caveat.

## Core principle

The system records what changed as Fact and separates Fact / Derived Metric / Interpretation / Prediction.

Provider-specific schemas must remain behind provider interfaces so the Core can evolve independently of individual API vendors.

Deployment placement must also remain behind module contracts: moving acquisition from Cloud to a future always-on server must not require rewriting Core-facing provider contracts.

## Worker scaffold

The repository now includes a minimal deployable Cloudflare Worker scaffold:

- `src/index.ts`
- `wrangler.jsonc`
- `package.json`
- `tsconfig.json`

The Worker defaults to `WORKER_MODE = "shadow"`. Shadow mode exposes `/health` and `/digest/latest` and accepts Cron Trigger wake-ups without market-data writes. The live acquisition path requires Alpaca secrets and the D1 binding. Regular acquisition remains unchanged. The separate `PREDICTION_MODE = "shadow"` profile records its configured registry in the digest while the outer Worker is in shadow mode; after the outer Worker is promoted to `live`, it also plans target-only Premarket coverage without executing those Premarket jobs or writing bars.

The provisional prediction implementation is isolated in `src/prediction.ts` and `src/prediction-registry.ts`. It provides executable contracts for versioned predictor/target registries, the four horizon/anchor chain, Premarket anchor windows, readiness deadlines, leakage guards, a reviewed semiconductor canary profile and bounded Premarket shadow planning without adding Japanese instruments to the fixed monitoring Universe.

## Implementation entry point

Implementation should be checked against the v0.1 Definition of Done in `docs/stock_monitoring_v0.1_spec.md`. Domain-specific behavior must also conform to the corresponding reference specification.

Use `docs/REQUIREMENTS_TRACEABILITY_v0.1.md` as the stable bridge from normative requirements into design and verification. Use `docs/HIGH_LEVEL_DESIGN_v0.1.md` for architectural responsibility, the `docs/DETAILED_DESIGN_*_v0.1.md` files for contract-level design slices, and `docs/DESIGN_DECISIONS_v0.1.md` for reversible deployment/implementation choices. Use the volume/activity report, deployment runbook and Worker implementation-decision document as implementation guidance; if they conflict with Code of Truth or contract-level design, the normative/contract documents win.

The Japan-to-U.S. prediction document is a provisional research extension. It keeps Japanese predictor instruments outside the fixed monitoring Universe and does not add prediction accuracy to the current v0.1 Definition of Done.
