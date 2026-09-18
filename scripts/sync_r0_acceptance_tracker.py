from __future__ import annotations

from pathlib import Path

TRACKER = Path("docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md")
BACKLOG = Path("docs/work-management/local-corporate-intelligence/WBS_UNREFLECTED_TASK_BACKLOG_2026-09-10.md")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"{label}: expected source text not found")
    return text.replace(old, new, 1)


def sync_tracker() -> None:
    text = TRACKER.read_text(encoding="utf-8")
    text = replace_once(text, "Date: 2026-09-12", "Date: 2026-09-13", label="tracker date")

    old_table = """| PX0-001 | Not started | Reviewed operational scheduler job registration |\n| PX0-002 | Accepted locally through Packet D | Durable scheduler run/job evidence and stale-lock/restart recovery implemented and locally accepted; formal WBS incorporation/remap remains pending |\n| PX0-003 | Accepted locally through Packet E | CLI-only retention inspection, explicit due-content deletion, and registered bounded replay accepted; remote D1 export/purge remains separate |\n| PX0-004 | Accepted locally through Packet F | Explicit local backup/restore and restore drill accepted; remote D1 backup/restore remains separate |\n\nThese remain non-normative tracking IDs pending future WBS incorporation/remap.\n"""
    new_table = """| PX0-001 | Accepted locally / remapped to R0-001 | Reviewed scheduler registration plan accepted locally; deploy/trigger mutation remains separately gated |\n| PX0-002 | Accepted locally / remapped to R0-002 | Durable scheduler run/job evidence and stale-lock/restart recovery accepted through Packet D |\n| PX0-003 | Accepted locally / remapped to R0-003 | CLI-only retention inspection, explicit due-content deletion, and registered bounded replay accepted through Packet E; remote D1 export/purge remains separate |\n| PX0-004 | Accepted locally / remapped to R0-004 | Explicit local backup/restore and restore drill accepted through Packet F; remote D1 backup/restore remains separate |\n\nThese legacy PX0 IDs are now formally incorporated as R0-001..004 in the main WBS; retain them here for traceability.\n\n### Formal R0 operations/recovery status\n\n| Task | Status | Evidence / boundary |\n|---|---|---|\n| R0-001 | Accepted locally | Scheduler registration review accepted; no live Cron/Worker mutation authorized |\n| R0-002 | Accepted locally | Packet D durable run evidence/restart recovery accepted |\n| R0-003 | Accepted locally | Packet E bounded retention/replay operator path accepted |\n| R0-004 | Accepted locally | Packet F backup/restore/restore-drill boundary accepted |\n| R0-005 | Accepted evidence boundary; activation gated | AMD/NVDA metadata-only Worker/Schedule orchestration exercised through accepted local regressions and reviewed live Canary evidence; Worker remains Shadow after rollback and reactivation requires a separate change window |\n| R0-006 | Accepted locally | D1 retention contract accepted; current control truth never purge eligible |\n| R0-007 | Accepted locally / fixture export+custody | Deterministic half-open bounded export/custody accepted; remote D1 export remains change-window gated |\n| R0-008 | Accepted locally through `PURGE_ELIGIBLE` | Ordered ACK/quality/grace/replay/resolution lifecycle accepted; `PURGED` remains remote-only and separately authorized |\n| R0-009 | Accepted locally | Failure/recovery fixtures accepted; final full TypeScript 178/178, typecheck passed, full Python 555/555, compileall passed |\n\nDetailed R0-006..009 acceptance: `R0_D1_DRAIN_LOCAL_ACCEPTANCE_2026-09-13.md`.\n"""
    text = replace_once(text, old_table, new_table, label="PX0/R0 status table")

    text = replace_once(
        text,
        "- `PX0-002..004` local hardening boundaries are Accepted. `PX0-001` reviewed operational scheduler registration remains Not started.\n- `UWBS-023..026` record the D1 hot-store drain lifecycle design; remote export/purge remains separately gated.\n",
        "- `PX0-001..004` are Accepted locally and formally remapped to `R0-001..004`.\n- `R0-006..009` D1 hot-store drain local/fixture boundaries are Accepted; remote export/purge and the actual `PURGED` transition remain separately gated.\n",
        label="parallel lanes",
    )

    text = replace_once(
        text,
        "5. The next safe local post-X0 follow-up is `PX0-001` reviewed operational scheduler job registration. Do not silently convert that into live scheduler/Cron activation; registration design/review remains separate from any deployment window.\n6. Keep `L1-003/SMOKE-007`, migration `0008` remote application, scheduler-evidence activation, remote D1 export/purge/backup/restore, and other Worker mutations separately gated.\n",
        "5. Treat `R0-001..004` and `R0-006..009` as locally Accepted at their recorded non-live boundaries. Treat `R0-005` as evidence-complete for reviewed orchestration while activation remains separately gated after rollback.\n6. Keep `L1-003/SMOKE-007`, migration `0008` remote application, scheduler-evidence activation, actual D1 export/purge/`PURGED`, remote backup/restore, and other Worker/Cron mutations separately gated.\n",
        label="restart rule",
    )

    anchor = "| Packet F | locally Accepted; focused backup/restore 5 then focused backup/restore+drill 10; full Python 537; compileall and diff check passed; clean restore, hash verification, SQLite integrity/migration checks, and Parquet/manifest provenance validation covered |\n"
    r0_rows = """| R0-001 | locally Accepted; reviewed scheduler registration plan; no live trigger mutation |\n| R0-002 | locally Accepted through Packet D |\n| R0-003 | locally Accepted through Packet E |\n| R0-004 | locally Accepted through Packet F |\n| R0-005 | reviewed orchestration evidence complete; activation still change-window gated |\n| R0-006 | locally Accepted; retention contract focused 6; TypeScript 167; Python 537 |\n| R0-007 | locally Accepted fixture export/custody; focused 22; Python 551; compileall passed |\n| R0-008 | locally Accepted through `PURGE_ELIGIBLE`; focused 13/13; TypeScript 174/174; Python 551/551; typecheck/compileall passed |\n| R0-009 | locally Accepted; targeted provider-digest fixture 5/5 after false-positive repair; lease contention 6/6 after deterministic barrier repair; full TypeScript 178/178; typecheck passed; full Python 555/555; compileall passed |\n"""
    if r0_rows not in text:
        if anchor not in text:
            raise RuntimeError("acceptance table anchor not found")
        text = text.replace(anchor, anchor + r0_rows, 1)

    text = replace_once(
        text,
        "- `UWBS-023..026` D1 hot-store drain lifecycle is captured for future WBS/CP incorporation; local Packet E/F hardening does not authorize remote drain/purge operations.\n- UWBS-016 future WBS incorporation and reviewed Worker News activation.\n- PX0-001 reviewed scheduler registration remains Not started.\n",
        "- `UWBS-023..026` are formally incorporated as `R0-006..009` and locally accepted; remote D1 drain/purge remains unauthorized.\n- `UWBS-016` is incorporated as `R0-005`; reviewed Worker News activation remains separately gated after rollback.\n- `PX0-001` is incorporated as `R0-001` and accepted locally; live scheduler/Cron mutation remains separately gated.\n",
        label="unresolved R0 items",
    )

    TRACKER.write_text(text, encoding="utf-8")


def sync_backlog() -> None:
    text = BACKLOG.read_text(encoding="utf-8")

    mappings = {
        "| UWBS-001 | PX0-001 | Register reviewed operational scheduler jobs | Operations / Integration | At least one reviewed adapter-owned scheduler plan is registered; dry-run displays intended jobs; zero-job success cannot be mistaken for workload completion; HTTP mutation remains prohibited | X0-004, owning adapters, provider/terms gates | Ready for WBS design | Pending |":
        "| UWBS-001 | PX0-001 | Register reviewed operational scheduler jobs | Operations / Integration | At least one reviewed adapter-owned scheduler plan is registered; dry-run displays intended jobs; zero-job success cannot be mistaken for workload completion; HTTP mutation remains prohibited | X0-004, owning adapters, provider/terms gates | Incorporated | R0-001 |",
        "| UWBS-002 | PX0-002 | Durable scheduler run evidence and stale-lock recovery | Operations / Recovery | Persist run/job identity, status, completion boundary, revision and sanitized failure state; make last completed boundary inspectable; stale-lock ownership/clearance is testable and robust against PID reuse | X0-004; I0-003 remains provider/source checkpoint owner | Ready for WBS design | Pending |":
        "| UWBS-002 | PX0-002 | Durable scheduler run evidence and stale-lock recovery | Operations / Recovery | Persist run/job identity, status, completion boundary, revision and sanitized failure state; make last completed boundary inspectable; stale-lock ownership/clearance is testable and robust against PID reuse | X0-004; I0-003 remains provider/source checkpoint owner | Incorporated | R0-002 |",
        "| UWBS-003 | PX0-003 | Retention and bounded-reprocessing operator CLI | News / Operations integration | Operator can inspect backlog/overdue state, perform bounded delete/retry through concrete storage, and plan/run bounded replay without exposing bodies/secrets | N1-005, L0-006, integration/storage layer | Ready for WBS design | Pending |":
        "| UWBS-003 | PX0-003 | Retention and bounded-reprocessing operator CLI | News / Operations integration | Operator can inspect backlog/overdue state, perform bounded delete/retry through concrete storage, and plan/run bounded replay without exposing bodies/secrets | N1-005, L0-006, integration/storage layer | Incorporated | R0-003 |",
        "| UWBS-004 | PX0-004 | Reproducible backup/restore and restore drill | Storage / Recovery | Freeze data-root layout and backup set; implement consistent SQLite snapshot and dataset/catalog validation; define manifest/hashes, destination protections, generations/RPO, restore validation and drill evidence | L0-005, L1 storage/datasets, X0-006 policy | Ready for WBS design | Pending |":
        "| UWBS-004 | PX0-004 | Reproducible backup/restore and restore drill | Storage / Recovery | Freeze data-root layout and backup set; implement consistent SQLite snapshot and dataset/catalog validation; define manifest/hashes, destination protections, generations/RPO, restore validation and drill evidence | L0-005, L1 storage/datasets, X0-006 policy | Incorporated | R0-004 |",
        "| UWBS-016 | Implement Worker/Schedule News metadata acquisition job | Worker acquisition / Operations integration | Run reviewed AMD/NVDA metadata-only News jobs on bounded session-aware cadence; reuse I0-003 checkpoint and I0-004 idempotency; preserve cross-symbol article identity; bound pagination/call budget; expose retryable failure state; keep secrets out of persistence/logs; require separate Worker activation review/change window | N0-002; I0-003/004; X0-002; N1-006 measured recall for cadence validation; UWBS-001/PX0-001; SMOKE-006; SMOKE-007 only for approved historical catch-up | Ready for WBS design | Pending |":
        "| UWBS-016 | Implement Worker/Schedule News metadata acquisition job | Worker acquisition / Operations integration | Run reviewed AMD/NVDA metadata-only News jobs on bounded session-aware cadence; reuse I0-003 checkpoint and I0-004 idempotency; preserve cross-symbol article identity; bound pagination/call budget; expose retryable failure state; keep secrets out of persistence/logs; require separate Worker activation review/change window | N0-002; I0-003/004; X0-002; N1-006 measured recall for cadence validation; UWBS-001/PX0-001; SMOKE-006; SMOKE-007 only for approved historical catch-up | Incorporated | R0-005 |",
        "| UWBS-023 | Define D1 hot-store / local-history retention contract | L1 / Storage / Operations | Classify D1 rows into current control state, hot acquired data, acceptance/idempotency evidence, operational evidence and exception/blocker state; define authoritative store, configurable retention/grace policy and purge eligibility; explicitly separate acquisition lookback from deletion eligibility | L1-001..006; I0-003/004; UWBS-002/003/004; current D1 schema | Ready for WBS design | Pending |":
        "| UWBS-023 | Define D1 hot-store / local-history retention contract | L1 / Storage / Operations | Classify D1 rows into current control state, hot acquired data, acceptance/idempotency evidence, operational evidence and exception/blocker state; define authoritative store, configurable retention/grace policy and purge eligibility; explicitly separate acquisition lookback from deletion eligibility | L1-001..006; I0-003/004; UWBS-002/003/004; current D1 schema | Incorporated | R0-006 |",
        "| UWBS-024 | Implement bounded incremental D1 export and custody manifest | L1 export / Local ingestion | Export explicit half-open table/source/time windows with generation ID, source environment/database identity, schema/source revision, row count, size/hash and local destination; retries are idempotent; steady-state path does not repeatedly full-scan/download all history | UWBS-023; L1-001/002/003/004; local catalog/import path; remote export remains change-window gated | Needs decomposition | Pending |":
        "| UWBS-024 | Implement bounded incremental D1 export and custody manifest | L1 export / Local ingestion | Export explicit half-open table/source/time windows with generation ID, source environment/database identity, schema/source revision, row count, size/hash and local destination; retries are idempotent; steady-state path does not repeatedly full-scan/download all history | UWBS-023; L1-001/002/003/004; local catalog/import path; remote export remains change-window gated | Incorporated | R0-007 |",
        "| UWBS-025 | Implement export acknowledgement and bounded D1 purge lifecycle | Operations / Retention | Implement `PLANNED -> EXPORTED -> HASH_VERIFIED -> IMPORTED -> QUALITY_ACCEPTED -> ACKNOWLEDGED -> GRACE -> PURGE_ELIGIBLE -> PURGED`; dry-run shows bounded purge candidates; purge requires verified local custody and preserves checkpoint/control truth; purge retry is idempotent and bounded | UWBS-023/024; L1-005; UWBS-003; I0-003; Packet D/UWBS-002 evidence boundary | Needs decomposition | Pending |":
        "| UWBS-025 | Implement export acknowledgement and bounded D1 purge lifecycle | Operations / Retention | Implement `PLANNED -> EXPORTED -> HASH_VERIFIED -> IMPORTED -> QUALITY_ACCEPTED -> ACKNOWLEDGED -> GRACE -> PURGE_ELIGIBLE -> PURGED`; dry-run shows bounded purge candidates; purge requires verified local custody and preserves checkpoint/control truth; purge retry is idempotent and bounded | UWBS-023/024; L1-005; UWBS-003; I0-003; Packet D/UWBS-002 evidence boundary | Incorporated | R0-008 |",
        "| UWBS-026 | D1 drain lifecycle acceptance and failure fixtures | Storage / Recovery QA | Fixtures cover Local unavailable/backlog growth, export failure/retry, hash mismatch, duplicate export, import/quality block, update after earlier export, purge failure/retry, checkpoint preservation, unresolved retention blocker, local queryability after D1 purge and bounded D1 budget behavior | UWBS-023..025; UWBS-004 backup/restore remains separate | Needs decomposition | Pending |":
        "| UWBS-026 | D1 drain lifecycle acceptance and failure fixtures | Storage / Recovery QA | Fixtures cover Local unavailable/backlog growth, export failure/retry, hash mismatch, duplicate export, import/quality block, update after earlier export, purge failure/retry, checkpoint preservation, unresolved retention blocker, local queryability after D1 purge and bounded D1 budget behavior | UWBS-023..025; UWBS-004 backup/restore remains separate | Incorporated | R0-009 |",
    }

    for old, new in mappings.items():
        if new in text:
            continue
        if old not in text:
            raise RuntimeError(f"backlog mapping source not found for: {old.split('|')[1].strip()}")
        text = text.replace(old, new, 1)

    BACKLOG.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    sync_tracker()
    sync_backlog()
    print(f"synced {TRACKER}")
    print(f"synced {BACKLOG}")
