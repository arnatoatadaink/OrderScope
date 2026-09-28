#!/usr/bin/env python3
"""One bounded PB-09 entry acquisition + Phase B window. Never runs without --execute."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://orderscope-market-worker-live-canary.yuihout2.workers.dev"
DB = "orderscope-state-live-canary"
KEYS = (
    "AMD|1Min|REGULAR|stock:iex:raw",
    "NVDA|1Min|REGULAR|stock:iex:raw",
    "QQQ|1Min|REGULAR|stock:iex:raw",
    "SPY|1Min|REGULAR|stock:iex:raw",
    "BTCUSD|1Min|ALL_TRADING|crypto:us",
)
CUSTODY_SHA = "de380ae35c1ab50f5e0364585e7f3224512085dc3bcd4abff8e37631938bed56"


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def run(*args, check=True):
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode and check:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}\n{result.stderr[-3000:]}")
    return result.stdout


def d1(sql):
    raw = run("bash", "scripts/run-wrangler-with-env.sh", "d1", "execute", DB,
              "--remote", "--json", "--command", sql)
    groups = json.loads(raw)
    if not isinstance(groups, list) or any(g.get("success") is not True or
        g.get("meta", {}).get("changed_db") is not False for g in groups):
        raise RuntimeError("D1 read incomplete or mutating")
    return [g["results"] for g in groups]


def snapshot():
    rows = d1("SELECT coverage_key,version,complete_through,source_observed_through,"
              "state,missing_ranges_json,blocker_json,retry_not_before FROM coverage_checkpoint "
              "WHERE coverage_key IN (" + ",".join("'" + k + "'" for k in KEYS) + ");"
              "SELECT COUNT(*) AS unresolved FROM acquisition_attempt WHERE coverage_key IN (" +
              ",".join("'" + k + "'" for k in KEYS) +
              ") AND finished_at IS NULL AND outcome IS NULL;"
              "SELECT generated_at,payload_json FROM latest_digest WHERE digest_key='market';")
    if len(rows) != 3 or len(rows[0]) != 5 or len(rows[1]) != 1 or len(rows[2]) != 1:
        raise RuntimeError("incomplete competition snapshot")
    return rows[0], int(rows[1][0]["unresolved"]), rows[2][0]


def healthy(cp):
    return (cp["state"] == "COMPLETE" and cp["missing_ranges_json"] == "[]"
            and cp["blocker_json"] is None and cp["retry_not_before"] is None
            and cp["complete_through"] == cp["source_observed_through"])


def session_at(calendar, now):
    return next((s for s in calendar["sessions"] if s["sessionKind"] == "REGULAR"
                 and dt(s["opensAt"]) <= dt(now) < dt(s["closesAt"])), None)


def require_active(session, reserve_minutes=0):
    now = dt(utc())
    if not dt(session["opensAt"]) <= now < dt(session["closesAt"]) - timedelta(minutes=reserve_minutes):
        raise RuntimeError("active REGULAR session time reserve exhausted")


def candidate(rows, session, observed):
    payload = json.dumps(dict(observedNow=observed, health=dict(mode="shadow", feed="iex",
                   news=dict(mode="disabled")), calendar=dict(sessions=[session]),
                   checkpoints=rows, unresolvedAttempts=0, lagMinutes=1))
    script = "import {assessPhaseBEntry} from './scripts/l1_003_pb09_packet.mjs';" \
             "console.log(JSON.stringify(assessPhaseBEntry(JSON.parse(process.argv[1]))))"
    return json.loads(run("node", "--input-type=module", "-e", script, payload))["candidate"]


def health(mode):
    h = json.loads(run("curl", "-fsS", BASE + "/health"))
    if h.get("mode") != mode or h.get("feed") != "iex" or h.get("news", {}).get("mode") != "disabled":
        raise RuntimeError(f"unsafe Worker health: {h}")


def controls_closed():
    for endpoint in ("historical-recovery/nvda/local-evidence-next-chunk",
                     "pb08/reproducible-absence/ack"):
        code = run("curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                   "-X", "POST", BASE + "/control/" + endpoint)
        if code != "404":
            raise RuntimeError(f"temporary control open: {endpoint} {code}")


def preparation():
    output = run("bash", "scripts/l1_003_pb09_readonly_preparation.sh")
    match = re.search(r"read-only preparation artifacts: (\S+)", output)
    if not match:
        raise RuntimeError("preparation packet path absent")
    packet = json.loads((Path(match.group(1)) / "packet.json").read_text())
    print(f"packet={match.group(1)}/packet.json status={packet['assessment']['status']}", flush=True)
    return packet


def verify_custody():
    directory = Path(os.getenv("ORDERSCOPE_PB09_CUSTODY_DIR",
        ROOT / "var/d1-custody/l1-003-smoke-007-20260915"))
    try:
        expected = (directory / "normalized_bar_20260901T160300Z_20260901T160400Z.ndjson").read_bytes()
        manifest = json.loads((directory / "export-manifest.json").read_text())
    except (OSError, ValueError) as error:
        raise RuntimeError(f"accepted Phase A custody unavailable: {error}") from error
    if len(expected) != 581 or hashlib.sha256(expected).hexdigest() != CUSTODY_SHA or \
       manifest.get("sha256") != CUSTODY_SHA or manifest.get("row_count") != 1:
        raise RuntimeError("accepted Phase A custody identity changed")
    print(f"custody={directory} sha256={CUSTODY_SHA}", flush=True)


def deploy(config=None):
    args = ["bash", "scripts/run-wrangler-with-env.sh", "deploy"]
    if config:
        args += ["--config", str(config)]
    print(f"deploy={'temporary live' if config else 'checked-in shadow'} at {utc()}", flush=True)
    print(run(*args)[-2000:], flush=True)


def restore_shadow():
    last_error = None
    for attempt in range(1, 4):
        try:
            deploy()
            for probe in range(12):
                try:
                    health("shadow")
                    controls_closed()
                    return
                except RuntimeError as error:
                    last_error = error
                    if probe < 11:
                        time.sleep(2)
        except RuntimeError as error:
            last_error = error
        print(f"shadow restore attempt {attempt}/3 failed: {last_error}", file=sys.stderr)
    raise RuntimeError(f"SHADOW RESTORE FAILED: {last_error}")


def next_live_digest(last, deadline=100):
    until = time.monotonic() + deadline
    while time.monotonic() < until:
        rows, unresolved, digest = snapshot()
        if digest["generated_at"] != last:
            payload = json.loads(digest["payload_json"])
            if payload.get("mode") == "live":
                if unresolved:
                    raise RuntimeError("unfinished canary attempt after live scheduler digest")
                budget = payload.get("budget", {})
                if budget.get("withinBudget") is not True or \
                   budget.get("totalExternalSubrequests", 999) > 40 or \
                   budget.get("totalD1Queries", 999) > 40 or \
                   budget.get("externalBudgetCeiling") != 40 or \
                   budget.get("d1BudgetCeiling") != 40 or \
                   payload.get("maxJobsPerTick") != 2 or \
                   len(payload.get("jobPlans", [])) > 2 or \
                   payload.get("news", {}).get("mode") != "disabled" or \
                   any(s.get("outcome") != "SUCCEEDED" for s in payload.get("summaries", [])):
                    raise RuntimeError("non-clean live scheduler digest")
                print(f"scheduler={digest['generated_at']} summaries={len(payload.get('summaries', []))}", flush=True)
                return digest["generated_at"], rows, payload
        time.sleep(2)
    raise RuntimeError("no distinct normal live scheduler digest within 100 seconds")


def pause_gap(session, before, after, start, end):
    payload = json.dumps(dict(session=session, beforePause=before, beforeResume=after,
                              pauseStart=start, resumeAt=end))
    script = "import {freezePauseGap} from './scripts/l1_003_pb09_packet.mjs';" \
             "console.log(JSON.stringify(freezePauseGap(JSON.parse(process.argv[1]))))"
    return json.loads(run("node", "--input-type=module", "-e", script, payload))


def accepted_gap(key, gap, window_start, through, live_payloads):
    # Normal scheduler jobPlans provide ranges; run evidence is disabled on this deployment.
    plans = {}
    for payload in live_payloads:
        successful = {s["jobId"] for s in payload.get("summaries", []) if s.get("outcome") == "SUCCEEDED"}
        for plan in payload.get("jobPlans", []):
            if plan["jobId"] in successful:
                plans[plan["jobId"]] = plan["requestedRange"]
    sql = ("SELECT job_id,outcome,diagnostic_json FROM acquisition_attempt "
           "WHERE coverage_key='" + key + "' AND started_at>='" + window_start +
           "' ORDER BY started_at;"
           "SELECT b.bar_start_utc,r.job_id,r.outcome FROM normalized_bar b "
           "JOIN bar_acceptance_receipt r ON r.identity_key=b.identity_key "
           "WHERE b.bar_start_utc>='" + gap["startInclusive"] +
           "' AND b.bar_start_utc<'" + through +
           "' AND r.outcome IN ('INSERTED','MATCHED') ORDER BY b.bar_start_utc;")
    attempts, bars = d1(sql)
    clean = {}
    for attempt in attempts:
        diag = json.loads(attempt["diagnostic_json"] or "{}")
        if attempt["outcome"] != "SUCCEEDED" or any(
            int(diag.get(x, 0)) != 0 for x in ("conflicts", "rejected", "missing")):
            raise RuntimeError("unclean target attempt")
        if int(diag.get("pages", 999)) > 10 or not 1 <= int(diag.get("inserted", 0)) + int(diag.get("matched", 0)) <= 100:
            raise RuntimeError("target attempt exceeded pages/bars limits")
        plan = plans.get(attempt["job_id"])
        if not plan:
            raise RuntimeError("successful target attempt lacks observed scheduler job plan")
        clean[attempt["job_id"]] = (plan["startInclusive"], plan["endExclusive"])
    covered = {b["bar_start_utc"] for b in bars if b["job_id"] in clean
               and clean[b["job_id"]][0] <= b["bar_start_utc"] < clean[b["job_id"]][1]}
    minutes = int((dt(through) - dt(gap["startInclusive"])).total_seconds() / 60)
    required = { (dt(gap["startInclusive"]) + timedelta(minutes=i)).isoformat(
        timespec="milliseconds").replace("+00:00", "Z")
        for i in range(minutes) }
    return required <= covered, dict(required=sorted(required), covered=sorted(covered),
                                     cleanJobIds=sorted(clean))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization-id", help="single approval covering entry acquisition and Phase B")
    parser.add_argument("--entry-opportunities-limit", type=int, default=16,
                        help="remaining normal scheduler opportunities in the approved session (1-16)")
    args = parser.parse_args()
    if not args.execute:
        print("DRY RUN: no remote mutation. Use --execute --authorization-id after bounded approval.")
        return
    if not args.authorization_id:
        parser.error("--execute requires --authorization-id")
    if not 1 <= args.entry_opportunities_limit <= 16:
        parser.error("entry-opportunities-limit must be between 1 and 16")
    if os.getenv("CLOUDFLARE_ENV", "live-canary") != "live-canary":
        raise RuntimeError("wrong Cloudflare environment")
    os.environ["CLOUDFLARE_ENV"] = "live-canary"
    os.environ.setdefault("WRANGLER_LOG_PATH", "/tmp/orderscope-pb10-combined-wrangler.log")
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    signal.signal(signal.SIGINT, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    if run("git", "branch", "--show-current").strip() != "l1-003-local-market-recovery" or \
       run("git", "status", "--porcelain").strip():
        raise RuntimeError("PB branch must be clean")
    if run("git", "rev-list", "--left-right", "--count",
           "HEAD...origin/l1-003-local-market-recovery").strip() != "0\t0":
        raise RuntimeError("PB branch differs from fetched remote")
    source = (ROOT / "wrangler.jsonc").read_text()
    if source.count('"WORKER_MODE": "shadow"') != 2 or \
       source.count('"PB08_ABSENCE_ACK_ENABLED": "false"') != 2 or \
       source.count('"ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES": "1"') != 2:
        raise RuntimeError("checked-in safe config changed")
    temp = ROOT / ".wrangler.pb10-combined-live-canary.jsonc"
    if temp.exists():
        raise RuntimeError("temporary config already exists")
    verify_custody()
    packet = preparation()
    if packet["release"] != run("git", "rev-parse", "HEAD").strip() or packet["worktree"]:
        raise RuntimeError("release/worktree drift")
    session = session_at(packet["calendar"], utc())
    if not session:
        raise RuntimeError("no active authoritative REGULAR session")
    require_active(session, reserve_minutes=60)
    health("shadow")
    controls_closed()
    live_possible = False
    accepted = False
    selected_key = None
    print(f"authorization={args.authorization_id} session={session['marketDate']}", flush=True)
    try:
        temp.write_text(source.replace('"WORKER_MODE": "shadow"', '"WORKER_MODE": "live"'))
        run("bash", "scripts/run-wrangler-with-env.sh", "deploy", "--dry-run", "--config", str(temp))
        rows, unresolved, digest = snapshot()
        if unresolved or any(not healthy(c) for c in rows):
            raise RuntimeError("unsafe entry checkpoint competition")
        chosen = candidate(rows, session, utc())
        entry_used = 0
        last = digest["generated_at"]
        while True:
            if not chosen:
                if entry_used >= args.entry_opportunities_limit:
                    raise RuntimeError("no current candidate within remaining approved entry opportunities")
                if not live_possible:
                    live_possible = True
                    deploy(temp)
                    health("live")
                require_active(session, reserve_minutes=25)
                last, rows, _ = next_live_digest(last)
                require_active(session, reserve_minutes=25)
                entry_used += 1
                chosen = candidate(rows, session, utc())
                print(f"entry opportunity={entry_used}/{args.entry_opportunities_limit} candidate={chosen and chosen['coverage_key']}", flush=True)
                continue
            if live_possible:
                restore_shadow()
                live_possible = False
            health("shadow")
            controls_closed()
            require_active(session, reserve_minutes=25)
            rows, unresolved, digest = snapshot()
            pause_start = utc()
            selected = candidate(rows, session, pause_start)
            if unresolved:
                raise RuntimeError("unfinished canary attempt at pause entry")
            if selected and all(selected[k] == chosen[k] for k in
                ("coverage_key", "version", "complete_through", "source_observed_through")):
                break
            print("candidate drifted while shadow became effective; continuing within entry limit", flush=True)
            chosen = None
        selected_key = selected["coverage_key"]
        print(f"pauseStart={pause_start} key={selected['coverage_key']} version={selected['version']}", flush=True)
        output = Path(tempfile.mkdtemp(prefix="orderscope-pb10-export-", dir="/tmp"))
        print(run("bash", "scripts/l1_003_pb09_paused_export_readonly.sh", str(output)), flush=True)
        target = dt(pause_start) + timedelta(minutes=3)
        if dt(utc()) < target:
            time.sleep((target - dt(utc())).total_seconds())
        rows, unresolved, _ = snapshot()
        resume_at = utc()
        before_resume = next(c for c in rows if c["coverage_key"] == selected["coverage_key"])
        if unresolved:
            raise RuntimeError("unfinished attempt during pause")
        gap = pause_gap(session, selected, before_resume, pause_start, resume_at)
        print(f"frozenGap={json.dumps(gap)} resumeAt={resume_at}", flush=True)
        _, _, digest = snapshot()
        last = digest["generated_at"]
        live_possible = True
        deploy(temp)
        health("live")
        live_payloads = []
        for opportunity in range(1, 17):
            require_active(session)
            last, rows, payload = next_live_digest(last)
            live_payloads.append(payload)
            cp = next(c for c in rows if c["coverage_key"] == selected["coverage_key"])
            if not healthy(cp):
                raise RuntimeError("target checkpoint regressed")
            through = max(cp["complete_through"], gap["endExclusive"])
            done, receipt = accepted_gap(selected["coverage_key"], gap, resume_at, through, live_payloads)
            print(f"resume opportunity={opportunity}/16 completeThrough={cp['complete_through']} gapCovered={done}", flush=True)
            if done and dt(cp["complete_through"]) >= dt(gap["endExclusive"]):
                accepted = True
                print(f"acceptance={json.dumps(receipt)}", flush=True)
                break
        if not accepted:
            raise RuntimeError("fresh gap not explained within 16 normal scheduler opportunities")
    finally:
        try:
            if live_possible:
                restore_shadow()
        finally:
            temp.unlink(missing_ok=True)
        health("shadow")
        controls_closed()
        rows, unresolved, _ = snapshot()
        if unresolved or any(not healthy(c) for c in rows):
            raise RuntimeError("unsafe final checkpoint state")
        if selected_key:
            final_cp = next(c for c in rows if c["coverage_key"] == selected_key)
            print(f"finalCheckpoint={json.dumps(final_cp)}", flush=True)
        print(f"safeClose={utc()} accepted={accepted}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyboardInterrupt) as error:
        print(f"PB-10 STOP: {error}", file=sys.stderr)
        sys.exit(1)
