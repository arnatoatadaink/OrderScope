import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "pb10", Path(__file__).with_name("l1_003_pb10_combined_window.py"))
PB10 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PB10)


class CombinedWindowAcceptance(unittest.TestCase):
    def setUp(self):
        os.environ["PATH"] = "/home/y/.nvm/versions/node/v24.21.0/bin:" + os.environ["PATH"]
        self.gap = dict(startInclusive="2026-09-28T14:00:00.000Z",
                        endExclusive="2026-09-28T14:03:00.000Z", expectedFreshMinutes=3)
        self.payload = dict(jobPlans=[dict(jobId="job-1", requestedRange=dict(
            startInclusive="2026-09-28T14:00:00.000Z",
            endExclusive="2026-09-28T14:04:00.000Z"))],
            summaries=[dict(jobId="job-1", outcome="SUCCEEDED")])
        self.attempt = dict(job_id="job-1", outcome="SUCCEEDED",
                            diagnostic_json='{"pages":1,"inserted":4,"matched":0,"conflicts":0,"rejected":0,"missing":0}')
        self.bars = [dict(bar_start_utc=f"2026-09-28T14:0{i}:00.000Z",
                          job_id="job-1", outcome="INSERTED") for i in range(4)]

    def test_candidate_uses_phase_b_frontier_rule(self):
        session = dict(sessionKind="REGULAR", opensAt="2026-09-28T13:30:00.000Z",
                       closesAt="2026-09-28T20:00:00.000Z")
        cp = dict(coverage_key="NVDA|1Min|REGULAR|stock:iex:raw", version=70,
                  complete_through="2026-09-28T14:00:00.000Z",
                  source_observed_through="2026-09-28T14:00:00.000Z", state="COMPLETE",
                  missing_ranges_json="[]", blocker_json=None, retry_not_before=None)
        self.assertEqual(PB10.candidate([cp], session, "2026-09-28T14:01:19.000Z"), cp)
        self.assertIsNone(PB10.candidate([cp], session, "2026-09-28T14:02:19.000Z"))

    def test_exact_gap_and_additional_progress_require_accepted_target_records(self):
        with patch.object(PB10, "d1", return_value=([self.attempt], self.bars)):
            ok, receipt = PB10.accepted_gap("NVDA|1Min|REGULAR|stock:iex:raw", self.gap,
                "2026-09-28T14:03:10.000Z", "2026-09-28T14:04:00.000Z", [self.payload])
        self.assertTrue(ok)
        self.assertEqual(len(receipt["required"]), 4)
        with patch.object(PB10, "d1", return_value=([self.attempt], self.bars[:-1])):
            ok, _ = PB10.accepted_gap("NVDA|1Min|REGULAR|stock:iex:raw", self.gap,
                "2026-09-28T14:03:10.000Z", "2026-09-28T14:04:00.000Z", [self.payload])
        self.assertFalse(ok)

    def test_unexplained_or_failed_attempt_stops(self):
        with patch.object(PB10, "d1", return_value=([self.attempt], self.bars)):
            with self.assertRaisesRegex(RuntimeError, "job plan"):
                PB10.accepted_gap("NVDA|1Min|REGULAR|stock:iex:raw", self.gap,
                    "2026-09-28T14:03:10.000Z", self.gap["endExclusive"], [])
        with patch.object(PB10, "d1", return_value=([dict(self.attempt, outcome="PARTIAL")], self.bars)):
            with self.assertRaisesRegex(RuntimeError, "unclean"):
                PB10.accepted_gap("NVDA|1Min|REGULAR|stock:iex:raw", self.gap,
                    "2026-09-28T14:03:10.000Z", self.gap["endExclusive"], [self.payload])

    def test_no_execute_performs_no_remote_call(self):
        with patch.object(sys, "argv", ["pb10"]), patch.object(PB10, "run") as command:
            PB10.main()
        command.assert_not_called()

    def test_shadow_restore_retries_and_checks_health(self):
        with patch.object(PB10, "deploy", side_effect=[RuntimeError("transient"), None]) as deploy, \
             patch.object(PB10, "health") as health, \
             patch.object(PB10, "controls_closed") as controls, \
             patch.object(PB10.time, "sleep"):
            PB10.restore_shadow()
        self.assertEqual(deploy.call_count, 2)
        health.assert_called_once_with("shadow")
        controls.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
