"""Non-engine source ownership/contract smoke. Native Luau harness separately required."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EGGRUMBLE_DeadlinePolicy.luau"

class DeadlineSourceTest(unittest.TestCase):
    def test_one_existing_state_and_no_secondary_authority(self):
        code = SOURCE.read_text(encoding="utf-8")
        self.assertIn('state.phase="FINISHED"', code)
        self.assertIn('state.winner="DRAW"', code)
        self.assertIn('state.winner~=nil', code)
        self.assertIn('matchId~=lease.matchId', code)
        self.assertIn('lease.consumed=true', code)
        self.assertIn('survivingSides(state)<2', code)
        self.assertIn('table.insert(state.events', code)
        for forbidden in ['DataStoreService','RemoteEvent','Instance.new','game:GetService','http://','require(script.Parent']:
            self.assertNotIn(forbidden, code)

    def test_native_harness_compose_uses_real_source(self):
        with tempfile.TemporaryDirectory() as d:
            target = pathlib.Path(d) / "test.luau"
            subprocess.run([sys.executable, str(ROOT / "tools/make_native_deadline_harness.py"),
                            "--out", str(target)], check=True)
            combined = target.read_text(encoding="utf-8")
            self.assertIn("local P=Deadline", combined)
            self.assertIn("EGGRUMBLE_V3_DEADLINE_NATIVE_ASSERTIONS_PASS", combined)
            self.assertIn('state.phase="FINISHED"', combined)
            self.assertNotIn('return Deadline\nlocal P', combined)

if __name__ == "__main__":
    unittest.main()
