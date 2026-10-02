#!/usr/bin/env python3
"""Bounded equity-only continuation of the frozen Sep 28 QQQ Phase B gap."""
import argparse
from datetime import timedelta
import json
import os
from pathlib import Path
import signal
import sys
import time

import l1_003_pb10_combined_window as common

ROOT = Path(__file__).resolve().parents[1]
QQQ = "QQQ|1Min|REGULAR|stock:iex:raw"
BTC = "BTCUSD|1Min|ALL_TRADING|crypto:us"
GAP = {"startInclusive": "2026-09-28T13:49:00.000Z",
       "endExclusive": "2026-09-28T13:52:00.000Z", "expectedFreshMinutes": 3}
RESUME_AT = "2026-09-28T13:53:44.584Z"
ABSENT = ["2026-09-27T17:41:00.000Z", "2026-09-27T17:44:00.000Z",
          "2026-09-27T17:54:00.000Z", "2026-09-27T18:01:00.000Z",
          "2026-09-27T18:04:00.000Z", "2026-09-27T18:14:00.000Z"]
EQUITIES = {"AMD", "NVDA", "QQQ", "SPY"}


def calendar():
    script = "import {AlpacaMarketCalendarProvider} from './src/calendar.ts';" \
        "const p=new AlpacaMarketCalendarProvider({credentials:{keyId:process.env.ALPACA_API_KEY," \
        "secretKey:process.env.ALPACA_API_SECRET}});" \
        "console.log(JSON.stringify(await p.getCalendar('2026-09-28','2026-09-29')))"
    return json.loads(common.run("node", "--env-file=.env", "--experimental-strip-types",
                                 "--input-type=module", "-e", script))


def require_baseline(rows, unresolved):
    if unresolved or len(rows) != 5:
        raise RuntimeError("unresolved or incomplete five-checkpoint snapshot")
    by_symbol = {c["coverage_key"].split("|")[0]: c for c in rows}
    if set(by_symbol) != EQUITIES | {"BTCUSD"}:
        raise RuntimeError("unexpected competition universe")
    if any(not common.healthy(by_symbol[s]) for s in EQUITIES):
        raise RuntimeError("unhealthy equity checkpoint")
    q = by_symbol["QQQ"]
    if q["version"] != 17 or q["complete_through"] != GAP["startInclusive"]:
        raise RuntimeError("frozen QQQ pause entry changed")
    b = by_symbol["BTCUSD"]
    missing = json.loads(b["missing_ranges_json"])
    expected_missing = [{"startInclusive": t, "endExclusive":
        (common.dt(t) + timedelta(minutes=1)).isoformat(timespec="milliseconds").replace("+00:00", "Z")}
        for t in ABSENT]
    if b["version"] != 59 or b["state"] != "PARTIAL" or \
       b["complete_through"] != "2026-09-27T17:41:00.000Z" or \
       b["source_observed_through"] != "2026-09-27T18:38:00.000Z" or \
       b["retry_not_before"] != "2026-09-28T14:09:19.000Z" or \
       missing != expected_missing:
        raise RuntimeError("BTCUSD baseline changed; new review required")
    return b


def btc_attempt_count():
    rows = common.d1("SELECT COUNT(*) AS attempts FROM acquisition_attempt "
        "WHERE coverage_key='" + BTC + "' AND started_at>='2026-09-28T15:00:00.000Z';")
    return int(rows[0][0]["attempts"])


def wait_mode(mode, seconds=35):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            common.health(mode)
            return
        except RuntimeError:
            time.sleep(2)
    raise RuntimeError(f"Worker did not become {mode} within {seconds} seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization-id")
    parser.add_argument("--max-opportunities", type=int, default=15)
    args = parser.parse_args()
    if not args.execute:
        print("DRY RUN: no remote calls or mutation")
        return
    if not args.authorization_id or not 1 <= args.max_opportunities <= 15:
        parser.error("--execute requires authorization-id and max-opportunities 1-15")
    os.environ["CLOUDFLARE_ENV"] = "live-canary"
    os.environ.setdefault("WRANGLER_LOG_PATH", "/tmp/orderscope-pb10-equity-resume-wrangler.log")
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    signal.signal(signal.SIGINT, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    if common.run("git", "branch", "--show-current").strip() != "l1-003-local-market-recovery" or \
       common.run("git", "status", "--porcelain").strip():
        raise RuntimeError("clean PB branch required")
    source = (ROOT / "wrangler.jsonc").read_text()
    shadow = '"WORKER_MODE": "shadow"'
    profile = '"UNIVERSE_PROFILE": "canary-v0.1"'
    if source.count(shadow) != 2 or source.count(profile) != 2 or \
       source.count('"PB08_ABSENCE_ACK_ENABLED": "false"') != 2:
        raise RuntimeError("checked-in safe config changed")
    temp = ROOT / ".wrangler.pb10-equity-resume-live-canary.jsonc"
    if temp.exists():
        raise RuntimeError("temporary config already exists")
    common.health("shadow")
    common.controls_closed()
    cal = calendar()
    session = common.session_at(cal, common.utc())
    if not session or session["marketDate"] != "2026-09-28":
        raise RuntimeError("Sep 28 REGULAR session is not active")
    common.require_active(session, reserve_minutes=25)
    rows, unresolved, digest = common.snapshot()
    baseline_btc = require_baseline(rows, unresolved)
    baseline_attempts = btc_attempt_count()
    config = source.replace(shadow, '"WORKER_MODE": "live"').replace(
        profile, '"UNIVERSE_PROFILE": "canary-equity-v0.1"')
    live_possible = False
    accepted = False
    print(f"authorization={args.authorization_id} release={common.run('git','rev-parse','HEAD').strip()}")
    print(f"frozenGap={json.dumps(GAP)} baselineBTC={json.dumps(baseline_btc)}")
    try:
        temp.write_text(config)
        dry = common.run("bash", "scripts/run-wrangler-with-env.sh", "deploy",
                         "--dry-run", "--config", str(temp))
        if 'env.UNIVERSE_PROFILE ("canary-equity-v0.1")' not in dry or \
           'env.WORKER_MODE ("live")' not in dry:
            raise RuntimeError("equity-only dry-run binding mismatch")
        live_possible = True
        common.deploy(temp)
        wait_mode("live")
        last = digest["generated_at"]
        payloads = []
        for opportunity in range(1, args.max_opportunities + 1):
            common.require_active(session)
            last, rows, payload = common.next_live_digest(last)
            payloads.append(payload)
            if not all(common.healthy(c) for c in rows if c["coverage_key"].split("|")[0] in EQUITIES):
                raise RuntimeError("equity checkpoint regressed")
            btc = next(c for c in rows if c["coverage_key"] == BTC)
            if btc != baseline_btc or btc_attempt_count() != baseline_attempts:
                raise RuntimeError("excluded BTCUSD changed during equity-only window")
            qqq = next(c for c in rows if c["coverage_key"] == QQQ)
            through = max(qqq["complete_through"], GAP["endExclusive"])
            complete, receipt = common.accepted_gap(QQQ, GAP, RESUME_AT, through, payloads)
            print(f"equity opportunity={opportunity}/{args.max_opportunities} QQQ={qqq['complete_through']} gapCovered={complete}", flush=True)
            if complete and common.dt(qqq["complete_through"]) >= common.dt(GAP["endExclusive"]):
                accepted = True
                print(f"acceptance={json.dumps(receipt)}", flush=True)
                break
        if not accepted:
            raise RuntimeError("frozen QQQ gap not explained within bounded opportunities")
    finally:
        try:
            if live_possible:
                common.restore_shadow()
        finally:
            temp.unlink(missing_ok=True)
        common.health("shadow")
        common.controls_closed()
        rows, unresolved, _ = common.snapshot()
        if unresolved or any(not common.healthy(c) for c in rows if c["coverage_key"].split("|")[0] in EQUITIES):
            raise RuntimeError("unsafe final equity checkpoint state")
        if next(c for c in rows if c["coverage_key"] == BTC) != baseline_btc or \
           btc_attempt_count() != baseline_attempts:
            raise RuntimeError("excluded BTCUSD changed at safe close")
        print(f"safeClose={common.utc()} accepted={accepted}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyboardInterrupt) as error:
        print(f"PB-10 EQUITY STOP: {error}", file=sys.stderr)
        sys.exit(1)
