"""GQ8 LSS: keep the real31->32 bridge current with each formal V3 source update."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0d-gq8-lss-real31-bridge.yml"

class TestAutoFollowCurrentRc(unittest.TestCase):
    def test_formal_rc_source_and_builder_update_trigger_bridge(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        push, rest = text.split("  pull_request:", 1)
        self.assertIn("      - rc/p0d-s1-kids-rc01", push)
        self.assertIn("      - 'rc_fastlane/**'", push)
        self.assertIn("      - '.github/workflows/p0d-rc-eggrumble-v3-31.yml'", push)
        self.assertIn("      - 'rc_fastlane/EGGRUMBLE_V3_LSS_OPTIONAL32.json'", push)
        self.assertIn("      - 'quality_gameplay/gq8_lss_real31_20261117/**'", push)
        self.assertIn("    branches: [rc/p0d-s1-kids-rc01]", rest)

    def test_same_head_strict_and_actual_source_not_fake_pass(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('gh api "repos/${GITHUB_REPOSITORY}/git/ref/heads/rc/p0d-s1-kids-rc01"', text)
        self.assertIn('headSha==$h and .status=="completed" and .conclusion=="success"', text)
        self.assertIn('test "$H" = "${{ steps.official.outputs.sha }}"', text)
        self.assertIn("CURRENT31_REAL_SOURCE.project.json", text)
        self.assertIn("LSS_REAL32_STUDIO.rbxlx", text)
        self.assertIn("LSS_OFF31_STUDIO.rbxlx", text)
        self.assertIn("test_rc_auto_follow.py", text)

if __name__ == "__main__":
    unittest.main()
