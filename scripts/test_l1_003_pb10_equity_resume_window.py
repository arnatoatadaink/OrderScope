import importlib.util
from datetime import timedelta
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "equity", Path(__file__).with_name("l1_003_pb10_equity_resume_window.py"))
EQUITY = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(Path(__file__).resolve().parent))
SPEC.loader.exec_module(EQUITY)


class EquityResumeGuard(unittest.TestCase):
    def test_dry_run_performs_no_remote_call(self):
        with patch.object(sys, "argv", ["equity"]), patch.object(EQUITY.common, "run") as command:
            EQUITY.main()
        command.assert_not_called()

    def test_btc_baseline_must_be_exact_and_equities_healthy(self):
        rows = []
        for symbol in ("AMD", "NVDA", "QQQ", "SPY"):
            rows.append(dict(coverage_key=f"{symbol}|1Min|REGULAR|stock:iex:raw",
                version=17, complete_through=EQUITY.GAP["startInclusive"],
                source_observed_through=EQUITY.GAP["startInclusive"], state="COMPLETE",
                missing_ranges_json="[]", blocker_json=None, retry_not_before=None))
        btc = dict(coverage_key=EQUITY.BTC, version=59, state="PARTIAL",
            complete_through="2026-09-27T17:41:00.000Z",
            source_observed_through="2026-09-27T18:38:00.000Z",
            missing_ranges_json=json.dumps([dict(startInclusive=t,
                endExclusive=(EQUITY.common.dt(t) + timedelta(minutes=1)).isoformat(
                    timespec="milliseconds").replace("+00:00", "Z")) for t in EQUITY.ABSENT]),
            blocker_json=None, retry_not_before="2026-09-28T14:09:19.000Z")
        self.assertEqual(EQUITY.require_baseline(rows + [btc], 0), btc)
        with self.assertRaisesRegex(RuntimeError, "unhealthy equity"):
            EQUITY.require_baseline([dict(rows[0], state="PARTIAL")] + rows[1:] + [btc], 0)
        with self.assertRaisesRegex(RuntimeError, "BTCUSD baseline"):
            EQUITY.require_baseline(rows + [dict(btc, version=60)], 0)
        with self.assertRaisesRegex(RuntimeError, "unresolved"):
            EQUITY.require_baseline(rows + [btc], 1)


if __name__ == "__main__":
    unittest.main()
