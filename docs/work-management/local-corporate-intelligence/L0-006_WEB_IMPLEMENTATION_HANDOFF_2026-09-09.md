# OrderScope — L0-006 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `L0-006`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-003`, `L0-004`, `L0-005`

## 1. Completion boundary

L0-006 provides the application-owned Typer CLI entry point required before X0-004.

Implemented/changed files:

- `analysis/app/orderscope_local/cli.py`
- `analysis/tests/cli/test_cli.py`
- `pyproject.toml`

Project script:

```text
orderscope = orderscope_local.cli:app
```

## 2. Command surface

Top-level surface:

```text
orderscope serve
orderscope import ...
orderscope quality ...
```

`import` and `quality` are CLI-only command groups. Their current `status` commands expose the execution boundary without starting arbitrary jobs; operation-specific commands remain owned by their respective implementation tasks.

## 3. Serve boundary

`orderscope serve`:

- constructs the accepted read-only FastAPI application;
- binds only to literal `127.0.0.1` through `LocalServerBinding`;
- exposes no host override option;
- accepts only a bounded TCP port option;
- uses non-secret `LocalConfig.log_level` for Uvicorn logging;
- does not expose an HTTP mutation route;
- does not start import, quality, scheduler, provider, D1, or Worker operations.

The initial read snapshot is empty. Loading persisted accepted views into the serving process is a later integration concern and is not fabricated in L0-006.

## 4. Focused tests

The focused module contains 6 cases covering:

1. root help exposes `serve`, `import`, and `quality`;
2. import group is CLI-only;
3. quality group is CLI-only;
4. serve passes literal `127.0.0.1`, selected port, and a read-only app to Uvicorn;
5. external host override is rejected because no `--host` option exists;
6. invalid port is rejected.

## 5. Local verification boundary

Run from repository root:

```bash
uv run pytest -q analysis/tests/cli/test_cli.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires all four checks to pass.

## 6. Next action after acceptance

```text
L0-006 Accepted
  -> X0-004 local scheduler
```

X0-004 remains responsible for manual-CLI start, single-instance lock, bounded run, resume, and dry-run behavior. L0-006 does not implement scheduler semantics itself.
