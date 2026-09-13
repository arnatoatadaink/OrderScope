from __future__ import annotations

from pathlib import Path

TRACKER = Path("docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md")
MARKER = "## A0 — Analyst Expectations / Cross-Market Context"
BLOCK = """## A0 — Analyst Expectations / Cross-Market Context\n\n| Task | Status | Evidence / next action |\n|---|---|---|\n| A0-001 | Accepted locally | 8 focused contract tests; 88 combined contract tests; Cross-Market capital movement remains Interpretation and FX contradiction cannot create a Fact |\n| A0-002 | Provisional validation complete | 20 cross-market tests; 94 real observations; 12/12 required series; H1 SUPPORT, H2 SUPPORT, H3 SUPPORT, H4 UNKNOWN, H5 CONTRADICT. Consensus-gap source remains unresolved; see `A0-002_CBRS_MULTI_LAYER_FLOW_VALIDATION_2026-09-14.md` |\n\n"""


def main() -> None:
    text = TRACKER.read_text(encoding="utf-8")
    if MARKER in text:
        raise SystemExit("A0 tracker section already exists; update manually instead of duplicating it")
    insertion = "\n" + BLOCK
    if "## 4. N1-006" in text:
        text = text.replace("## 4. N1-006", insertion + "## 4. N1-006", 1)
    else:
        text += insertion
    TRACKER.write_text(text, encoding="utf-8")
    print(f"updated = {TRACKER}")


if __name__ == "__main__":
    main()
