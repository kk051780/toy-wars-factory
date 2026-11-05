"""PR12: preserve on-change QA while reducing only the non-coding watchdog cadence.

Pure repository-level checks. These do not prove provider cron delivery,
GitHub billing, unattended code writing, or independent review.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / ".github/workflows/loop-watchdog.yml"


class IdleWatchdogCadenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WATCHDOG.read_text(encoding="utf-8")

    def test_exactly_one_six_hour_watchdog_schedule(self):
        crons = re.findall(r"(?m)^\s*-\s*cron:\s*(.+?)\s*$", self.source)
        self.assertEqual(crons, ['"7 0,6,12,18 * * *"'])
        self.assertNotIn("7,27,47 * * * *", self.source)

    def test_read_only_manual_audit_still_available(self):
        self.assertRegex(self.source, r"(?m)^  workflow_dispatch:\s*$")
        self.assertRegex(self.source, r"(?m)^permissions:\s*\n  contents: read\s*$")
        self.assertNotIn("contents: write", self.source)
        self.assertNotIn("pull-requests: write", self.source)
        self.assertNotIn("id-token: write", self.source)

    def test_original_canonical_checks_are_not_disabled(self):
        self.assertIn("lua5.4 -e", self.source)
        self.assertIn("python3 tools/repository_gate.py", self.source)
        self.assertIn("QA heartbeat only.", self.source)
        self.assertIn("does NOT edit the game or run an AI coding agent", self.source)
        self.assertNotIn("continue-on-error: true", self.source)


if __name__ == "__main__":
    unittest.main()
