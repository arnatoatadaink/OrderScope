from __future__ import annotations

from pathlib import Path

BACKLOG = Path("docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md")

REPLACEMENTS = {
    "| UWBS-011 | Define Macro-Market non-price Fact contract | A0 / I0 Cross-Market integration | Define normalized raw Facts for policy rates, short-market rates, sovereign 2Y/5Y/10Y/30Y yields, USD/JPY and eligible volatility/flow context; preserve event/available/accepted/as-of times, units, market/tenor identity and source provenance; inferred capital movement must not be stored as Fact | A0-001; I0-002/004/005; provider/source gates | Ready for WBS design | Pending |":
    "| UWBS-011 | Define Macro-Market non-price Fact contract | A0 / I0 Cross-Market integration | Define normalized raw Facts for policy rates, short-market rates, sovereign 2Y/5Y/10Y/30Y yields, USD/JPY and eligible volatility/flow context; preserve event/available/accepted/as-of times, units, market/tenor identity and source provenance; inferred capital movement must not be stored as Fact | A0-001; I0-002/004/005; provider/source gates | Ready for WBS design | Local implementation accepted 2026-09-14; 4 focused / 626 full Python pass; pending WBS incorporation |",
    "| UWBS-012 | Implement rate-curve and cross-country Derived Metrics | A0 Derived Metrics | Compute tested 2s10s/10s30s slopes, U.S.-Japan 2Y/10Y spreads, fixed-window FX/yield deltas and change velocity; distinguish steepening, flattening and inversion without converting them into causal claims; preserve as-of semantics | UWBS-011; A0-001; I0 Fact/Derived Metric boundary | Ready for WBS design | Pending |":
    "| UWBS-012 | Implement rate-curve and cross-country Derived Metrics | A0 Derived Metrics | Compute tested 2s10s/10s30s slopes, U.S.-Japan 2Y/10Y spreads, fixed-window FX/yield deltas and change velocity; distinguish steepening, flattening and inversion without converting them into causal claims; preserve as-of semantics | UWBS-011; A0-001; I0 Fact/Derived Metric boundary | Ready for WBS design | Local implementation accepted 2026-09-14; 4 focused / 630 full Python pass; pending WBS incorporation |",
    "| UWBS-013 | Define carry-unwind / deleveraging Interpretation contract | A0 Interpretation / Regime | Define `CARRY_UNWIND_CANDIDATE`, `DELEVERAGING_REGIME`, `RATE_SHOCK`, `FX_SHOCK_JPY` and related evidence rules using multiple independent signals; support SUPPORT/PARTIAL/CONTRADICT/UNKNOWN and prohibit USD/JPY or one news item from establishing capital movement as Fact | UWBS-011/012; A0-001 hypothesis rules; News evidence | Ready for WBS design | Pending |":
    "| UWBS-013 | Define carry-unwind / deleveraging Interpretation contract | A0 Interpretation / Regime | Define `CARRY_UNWIND_CANDIDATE`, `DELEVERAGING_REGIME`, `RATE_SHOCK`, `FX_SHOCK_JPY` and related evidence rules using multiple independent signals; support SUPPORT/PARTIAL/CONTRADICT/UNKNOWN and prohibit USD/JPY or one news item from establishing capital movement as Fact | UWBS-011/012; A0-001 hypothesis rules; News evidence | Ready for WBS design | Local implementation accepted 2026-09-14; 5 focused / 635 full Python pass; pending WBS incorporation |",
    "| UWBS-014 | Macro stress / carry-unwind validation fixtures and Canary cases | A0 QA / Cross-Market validation | Fixture set covers policy-rate up + long-yield down, steepening/flattening/inversion, rapid JPY appreciation, broad selloff with/without company-specific negative evidence, explicit carry-reduction report, event-risk de-risking and false-positive cases; validates Fact/Derived Metric/Interpretation separation | UWBS-011..013; A0-002 validation pattern | Ready for WBS design | Pending |":
    "| UWBS-014 | Macro stress / carry-unwind validation fixtures and Canary cases | A0 QA / Cross-Market validation | Fixture set covers policy-rate up + long-yield down, steepening/flattening/inversion, rapid JPY appreciation, broad selloff with/without company-specific negative evidence, explicit carry-reduction report, event-risk de-risking and false-positive cases; validates Fact/Derived Metric/Interpretation separation | UWBS-011..013; A0-002 validation pattern | Ready for WBS design | Local Canary accepted 2026-09-14; 6 focused / 641 full Python pass; pending WBS incorporation |",
    "| UWBS-015 | Survey and select structured macro-rate / FX / flow data sources | Provider contracts / A0 | Identify permissible official/structured sources for policy rates, sovereign curves, FX, FX-volatility and eligible fund-flow series; record terms, cadence, historical depth, timestamps, revision behavior, cost, rate limits and fallback boundary; do not activate live providers as part of survey | Existing provider/terms/security gates; UWBS-011 data requirements | Needs decomposition | Pending |":
    "| UWBS-015 | Survey and select structured macro-rate / FX / flow data sources | Provider contracts / A0 | Identify permissible official/structured sources for policy rates, sovereign curves, FX, FX-volatility and eligible fund-flow series; record terms, cadence, historical depth, timestamps, revision behavior, cost, rate limits and fallback boundary; do not activate live providers as part of survey | Existing provider/terms/security gates; UWBS-011 data requirements | Ready for WBS design | Research completed 2026-09-14; see `UWBS-015_MACRO_PROVIDER_SURVEY_2026-09-14.md`; official-direct primary path selected, commercial high-frequency fund-flow survey deferred |",
}


def main() -> None:
    text = BACKLOG.read_text(encoding="utf-8")
    missing: list[str] = []
    for old, new in REPLACEMENTS.items():
        if new in text:
            continue
        if old not in text:
            missing.append(old.split(" | ", 2)[1])
            continue
        text = text.replace(old, new, 1)
    if missing:
        raise SystemExit(f"backlog rows not found: {', '.join(missing)}")
    BACKLOG.write_text(text, encoding="utf-8")
    print(f"updated = {BACKLOG}")
    print("UWBS-011 = Accepted locally")
    print("UWBS-012 = Accepted locally")
    print("UWBS-013 = Accepted locally")
    print("UWBS-014 = Accepted locally")
    print("UWBS-015 = Research complete / Ready for WBS design")


if __name__ == "__main__":
    main()
