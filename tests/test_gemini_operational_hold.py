"""Incident hold checks. No provider credential or live transport is used."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gemini_patch_gate as gate
from verify_gemini_hold import verify_hold

GOOD = "diff --git a/src/a.lua b/src/a.lua\n--- a/src/a.lua\n+++ b/src/a.lua\n@@ -1 +1 @@\n-old\n+new\n"


class GeminiOperationalHoldTests(unittest.TestCase):
    def invoke(self, directory, *flags):
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["gate", "--patch-dir", str(directory), *flags]), contextlib.redirect_stdout(output):
            result = gate.main()
        return result, output.getvalue()

    def test_direct_call_cannot_select_any_transport(self):
        transport = mock.Mock(side_effect=AssertionError("transport must not run"))
        with self.assertRaisesRegex(RuntimeError, gate.ONLINE_HOLD):
            gate.scan_online(GOOD, "synthetic-key", transport)
        transport.assert_not_called()

    def test_online_stops_before_patch_or_environment_access(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(gate, "os", object()), mock.patch.object(Path, "read_text", side_effect=AssertionError("patch must not be read")), mock.patch.object(gate, "scan_online", side_effect=AssertionError("scanner must not run")):
            code, output = self.invoke(directory, "--online")
        self.assertEqual(code, 2)
        self.assertIn(gate.ONLINE_HOLD, output)

    def test_online_invalidates_both_stale_verdict_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("detection_result.json", "detection_result.json.tmp"):
                (root / name).write_text('{"malicious_patch":false}')
            code, _ = self.invoke(root, "--online")
            self.assertEqual(code, 2)
            self.assertFalse(any(root.glob("detection_result*")))

    def test_offline_static_pass_does_not_preserve_or_emit_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "aw.patch").write_text(GOOD)
            (root / "detection_result.json").write_text('{"malicious_patch":false}')
            code, output = self.invoke(root)
            self.assertEqual(code, 0)
            self.assertIn("static test alone is insufficient", output)
            self.assertFalse((root / "detection_result.json").exists())

    def test_missing_patch_also_invalidates_old_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "detection_result.json").write_text("stale")
            code, _ = self.invoke(root)
            self.assertEqual(code, 1)
            self.assertFalse((root / "detection_result.json").exists())

    def test_unremovable_old_verdict_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "detection_result.json").mkdir()
            code, output = self.invoke(root, "--online")
            self.assertEqual(code, 1)
            self.assertIn("cannot invalidate", output)

    def test_real_cli_remains_held_with_key_and_unlock_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "GEMINI_API_KEY": "synthetic-not-a-key", "TWF_LIVE_APPROVED": "true", "TWF_INPUT_BOUND_VERIFIED": "true"}
            result = subprocess.run([sys.executable, str(ROOT / "tools/gemini_patch_gate.py"), "--online", "--patch-dir", directory], env=env, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn(gate.ONLINE_HOLD, result.stdout)
            self.assertNotIn(env["GEMINI_API_KEY"], result.stdout + result.stderr)
            self.assertFalse((Path(directory) / "detection_result.json").exists())

    def test_authored_and_compiled_workflow_are_literally_held(self):
        self.assertEqual(verify_hold(ROOT)["status"], "PASS_OFFLINE_HOLD_ONLY")

    def test_marker_presence_does_not_release_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github/workflows").mkdir(parents=True)
            for name in ("twf-gemini-free-trial.md", "twf-gemini-free-trial.lock.yml"):
                (root / ".github/workflows" / name).write_bytes((ROOT / ".github/workflows" / name).read_bytes())
            (root / "ops").mkdir()
            (root / "ops/GEMINI_TRIAL_APPROVED_FUTURE.json").write_text('{"approved":true,"fresh":true}')
            self.assertEqual(verify_hold(root)["status"], "PASS_OFFLINE_HOLD_ONLY")

    def test_hold_verifier_rejects_removed_compiled_condition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github/workflows").mkdir(parents=True)
            for name in ("twf-gemini-free-trial.md", "twf-gemini-free-trial.lock.yml"):
                source = (ROOT / ".github/workflows" / name).read_text()
                if name.endswith(".yml"):
                    source = source.replace("    if: false\n", "")
                (root / ".github/workflows" / name).write_text(source)
            with self.assertRaisesRegex(ValueError, "pre_activation"):
                verify_hold(root)


if __name__ == "__main__":
    unittest.main()
