from __future__ import annotations

from pathlib import Path

TRACKER = Path("docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md")
MARKER = "## A0 — Analyst Expectations / Cross-Market Context"
NEXT_MARKER = "## 4. N1-006"
STALE_A0 = "- `A0-001` remains Provisional and `A0-002` remains separate validation work."
CURRENT_A0 = "- `A0-001` and `A0-002` are Accepted locally; A0 is complete at the current v0.1 validation boundary."
MAINT_MARKER = "## Maintenance — Python warning/resource lifecycle"
MAINT_BLOCK = """## Maintenance — Python warning/resource lifecycle

- SQLite connection lifecycle remediation: **Accepted locally**.
- Strict warning policy remains enabled; SQLite warnings are not suppressed.
- Acceptance evidence: `595 passed in 20.93s`; with `PYTHONTRACEMALLOC=10`, `595 passed in 43.12s`.
- See `PYTEST_SQLITE_RESOURCE_WARNING_INVESTIGATION_2026-09-14.md`.

"""
BLOCK = """## A0 — Analyst Expectations / Cross-Market Context

| Task | Status | Evidence / next action |
|---|---|---|
| A0-001 | Accepted locally | 8 focused contract tests; 88 combined contract tests; Cross-Market capital movement remains Interpretation and FX contradiction cannot create a Fact |
| A0-002 | Accepted locally | 22 focused Cross-Market tests; 94 real observations; 12/12 required series; H1 SUPPORT, H2 SUPPORT, H3 SUPPORT, H4 UNKNOWN, H5 CONTRADICT. Consensus gap explicitly evaluated as UNKNOWN because no reviewed historical as-of source is available; no current-value backfill. See `A0-002_CBRS_MULTI_LAYER_FLOW_ACCEPTANCE_2026-09-14.md` |

"""


def main() -> None:
    text = TRACKER.read_text(encoding="utf-8")
    if MARKER in text:
        start = text.index(MARKER)
        end = text.find(NEXT_MARKER, start)
        if end < 0:
            text = text[:start] + BLOCK
        else:
            text = text[:start] + BLOCK + text[end:]
    elif NEXT_MARKER in text:
        text = text.replace(NEXT_MARKER, "\n" + BLOCK + NEXT_MARKER, 1)
    else:
        text += "\n" + BLOCK

    if STALE_A0 in text:
        text = text.replace(STALE_A0, CURRENT_A0, 1)

    if MAINT_MARKER not in text:
        text = text.rstrip() + "\n\n" + MAINT_BLOCK

    TRACKER.write_text(text, encoding="utf-8")
    print(f"updated = {TRACKER}")
    print("A0-001 = Accepted locally")
    print("A0-002 = Accepted locally")
    print("SQLite maintenance = Accepted locally")


if __name__ == "__main__":
    main()
