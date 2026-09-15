# OrderScope — Local Analysis Stack ADR v0.1

Status: Accepted for the initial local MVP; reversible
Date: 2026-09-03
Decision ID: `ADR-LOCAL-STACK-001`
Work item: `L0-001`

## 1. Context

The local analysis service imports immutable exports, validates and transforms data, stores provenance and operational metadata, and exposes read-only views on the Main PC. It must remain independent of the Cloudflare Worker runtime and must not turn the local HTTP service into a Worker control plane.

`W0-001` permits this local work to proceed while the remaining `SMOKE-*` and `CANARY-*` checks stay in their separate Worker backlog. This decision does not authorize a remote D1 export, Worker change, paid provider contract, or live provider request.

The stack must support the following later work without changing its basic execution boundary:

- reproducible import and migration tests;
- SQLite metadata and D1-dump reconstruction;
- analytical queries over local data;
- deterministic Arrow/Parquet datasets;
- a localhost-only, read-only API;
- execution on the current Windows Main PC without concurrent Windows/WSL database access.

## 2. Decision

### 2.1 Runtime and package management

- Use CPython `3.13.x`; declare `requires-python = ">=3.13,<3.14"` and commit a `.python-version` containing `3.13` when the scaffold is created.
- Use `uv` for interpreter selection, virtual-environment creation, dependency resolution, command execution, and locking.
- Keep project metadata and direct dependency constraints in `pyproject.toml` and commit `uv.lock`. The lockfile, not an independently maintained `requirements.txt`, is the exact transitive dependency record.
- Install and run with `uv sync --locked` and `uv run ...`. CI and documented verification must use the locked environment.
- Keep the existing Node/Worker package and Python/local package independent. The repository root `package.json` does not invoke, install, or publish the Python service.

The Python minor version is intentionally bounded. A move to Python 3.14 or a different package manager requires a lock regeneration, full local test pass, and an ADR revision because native wheels and dataset serialization behavior can change.

### 2.2 Storage and query roles

Use each engine for one explicit role:

| Component | Role | Authority and write rule |
|---|---|---|
| Python `sqlite3` / SQLite | migration state, import manifests, source registry, cursors, quality results, run metadata, and reconstruction of imported D1 SQL | Authoritative local operational metadata. Writes occur through CLI/application repositories and versioned numbered SQL migrations. |
| DuckDB Python package | analytical joins, scans, aggregation, and local query/catalog acceleration | Derived and rebuildable. It may read SQLite through an explicit adapter or exported views and read Parquet directly; it is not a second authority for mutable operational state. |
| PyArrow | provider-neutral in-memory schemas, typed interchange, and Parquet serialization | Canonical schema/serialization layer for curated datasets. |
| Parquet | immutable, partitioned curated datasets and later feature datasets | Durable derived dataset. Files are written to a staging name, validated, then atomically published with a manifest/hash; an existing content-addressed object is not silently overwritten. |

Initial transformations use PyArrow and DuckDB. Polars is deferred until measurement shows that it materially simplifies or accelerates a workload; it is not part of the L0 dependency baseline.

SQLite and DuckDB files must not be opened concurrently by unrelated processes. The initial server is a single local application process, and mutating CLI operations use the same repository/storage layer with a single-instance lock. Multi-writer or network-filesystem operation is out of scope.

### 2.3 API and CLI

- Use FastAPI for HTTP routing and schema generation and Uvicorn as the ASGI server.
- The application-owned `serve` command fixes the listen address to `127.0.0.1`. It must reject configuration or arguments requesting `0.0.0.0`, `::`, a LAN address, or another external interface; relying only on a documented default is insufficient.
- The HTTP surface is read-only. Initial endpoints expose health and later metadata/query results; import, migration, quality, dataset build, retention, and provider operations remain CLI-only.
- Use Typer for the application CLI and expose it as the `orderscope` project script. The planned groups include `serve`, `import`, `quality`, and migration/dataset operations.
- API responses must not include credentials, provider response bodies, temporary news bodies, raw dumps, or unrestricted local paths.

### 2.4 Tests and quality gate

- Use pytest as the test runner and `httpx`'s ASGI transport/client for API tests. Use pytest temporary directories for all database and dataset writes.
- Tests must not use the operator's persistent `var` directory, network, provider credentials, remote D1, or Cloudflare bindings.
- SQLite migration tests rebuild an empty database from versioned migrations. Dataset tests compare schema, canonical row ordering, hashes, and semantic values rather than relying on incidental filesystem ordering.
- Local verification starts with `uv sync --locked` followed by `uv run pytest`. The existing Worker verification remains `npm test` and `npm run typecheck`; neither suite replaces the other.

Exact library and transitive versions will be resolved and committed in `uv.lock` during `L0-002`. Direct runtime dependencies expected by this decision are `fastapi`, `uvicorn`, `typer`, `duckdb`, and `pyarrow`; test dependencies are `pytest` and `httpx`.

### 2.5 Windows / WSL boundary

WSL2 is the authoritative Python execution and mutable-data environment.

- Run `uv`, Python, Uvicorn, SQLite, DuckDB, migrations, imports, tests, and dataset publication inside one WSL2 distribution.
- Source code may remain in the current Windows-mounted checkout for development. Persistent SQLite/DuckDB files, Parquet datasets, locks, and high-volume raw imports must use a WSL-native filesystem location for canary/operational runs, not `/mnt/c`, `/mnt/d`, a Windows network share, OneDrive, or another synchronised folder.
- `var/` is the logical mutable-data root and is Git-ignored in `L0-002`. Tests use temporary roots. The configuration work in `L0-003` will provide an explicit local data-root setting so an operational root on the WSL filesystem can be selected without committing a machine-specific path.
- Windows-native adapters needed later for Excel or a logged-in desktop application may write a closed, immutable, hashed handoff artifact. They do not import the Python application, open its SQLite/DuckDB files, write Parquet partitions, or call a mutating HTTP endpoint.
- Transfer across the Windows/WSL boundary is file/message based: write to a temporary name, close it, compute/verify its hash and manifest, copy it to a temporary name in the inbound filesystem if needed, then atomically rename it there. The WSL process is the sole importer.
- Timestamps stored by the application are UTC. `America/New_York` is used only for market/session classification and `Asia/Tokyo` only for presentation where requested.

The supported startup sequence is therefore:

```bash
# In WSL, from the repository root
uv sync --locked
uv run orderscope serve
```

Normal interactive shutdown is `Ctrl+C`. Forced termination must not be used as the normal stop path; imports and dataset publication must leave either the previous committed artifact or a complete new artifact.

## 3. Consequences

### Positive

- One Python environment covers ingestion, analytical SQL, typed columnar data, API, CLI, and tests.
- SQLite retains a small, inspectable migration surface while DuckDB and Parquet handle analytical volume without making DuckDB the operational source of truth.
- PyArrow fixes the schema and serialization boundary independently of a dataframe library.
- A single WSL writer avoids unsupported cross-OS file locking and reduces the chance of database corruption or partial dataset publication.
- The API remains a local observation surface rather than a remote-control interface.

### Costs and limitations

- Operators must install WSL2 and `uv`, and operational data must be backed up from the WSL filesystem deliberately.
- Running the source checkout under `/mnt/d` is acceptable for development but may be slower; persistent data cannot simply default there for canary operation.
- DuckDB catalog state is rebuildable by design, so schemas and manifests must carry enough provenance to reproduce it.
- Polars, notebooks, background schedulers, containers, authentication, and a Windows-native server are not selected by this ADR.

## 4. Alternatives considered

| Alternative | Decision |
|---|---|
| Run the service natively on Windows | Rejected for the initial MVP because it would create two supported execution paths and increase file-locking, path, shell, and native-package variation. Windows-only sources stay behind a handoff adapter. |
| Use only SQLite | Rejected because large Parquet scans and analytical joins are a distinct workload, while SQLite remains suitable for transactional metadata and import reconstruction. |
| Use only DuckDB | Rejected because mutable operational metadata, migration state, and cursor updates should not share authority with a rebuildable analytical catalog. |
| Use pandas or Polars as the canonical data contract | Rejected/deferred. Their dataframe APIs are implementation choices; Arrow schemas and Parquet are the stable interchange/storage contract. |
| Poetry, pip-tools, or unpinned `pip install` | Rejected for the initial stack. `uv` provides one project and lock workflow and is already available in the target WSL environment. |
| Flask or Django | Rejected. FastAPI supplies typed request/response boundaries and ASGI test support with less application structure than Django; the API remains deliberately small. |
| Docker as the mandatory local runtime | Deferred. It adds filesystem-mount and Desktop/WSL lifecycle concerns without solving an initial deployment requirement. A container can be evaluated later without changing provider-neutral contracts. |

## 5. Guardrails and revisit triggers

Revise this ADR before any of the following:

- supporting a second Python minor version or native-Windows execution;
- allowing multiple processes to write the same SQLite/DuckDB/catalog or Parquet root;
- exposing the API beyond loopback or adding an HTTP mutation endpoint;
- making DuckDB catalog state authoritative or replacing Arrow/Parquet as the curated contract;
- adding a dataframe framework to the required baseline;
- adding a scheduler, container, authentication layer, or remotely hosted local-analysis service.

Dependency patch/minor upgrades within the declared Python/runtime boundaries do not require a new ADR, but do require a reviewed `uv.lock` diff and successful local tests. File-format- or query-result-affecting upgrades also require deterministic fixture regeneration checks.

## 6. L0-001 acceptance mapping

| Required decision | Resolution |
|---|---|
| Python runtime | CPython `3.13.x`, bounded to `<3.14` |
| Package / lock management | `uv`, `pyproject.toml`, committed `uv.lock`, `uv sync --locked` |
| SQLite / DuckDB | SQLite is authoritative operational metadata and D1 reconstruction; DuckDB is rebuildable analytics/query state |
| Arrow / Parquet | PyArrow is the canonical schema/serialization layer; immutable Parquet is the curated dataset format |
| API | FastAPI + Uvicorn, enforced `127.0.0.1`, read-only HTTP |
| Test | pytest + httpx, temporary isolated storage, no network or credentials |
| Windows / WSL | WSL2 is sole runtime/writer; Windows-only acquisition crosses an immutable handoff boundary |

## 7. Related documents

- `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
- `WORK_PLAN_INITIAL_VALIDATION_AND_LONG_TERM_OPERATIONS_2026-09-01.md`
- `DESIGN_DECISIONS_v0.1.md` (`DD-DEPLOY-001`)
- `HANDOFF_LOCAL_JP_US_PREDICTION_2026-08-31.md`
