"""GQ8 LSS: only a frozen historical 31->32 optional source-build, never current RC."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/p0d-gq8-lss-real31-bridge.yml"

class TestAutoFollowCurrentRc(unittest.TestCase):
    def test_formal_rc_source_and_builder_update_trigger_bridge(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        push, rest = text.split("  pull_request:", 1)
        self.assertIn("      - rc/p0d-s1-kids-rc01", push)
        self.assertNotIn("      - 'rc_fastlane/**'", push)
        self.assertIn("      - '.github/workflows/p0d-rc-eggrumble-v3-31.yml'", push)
        self.assertIn("      - 'rc_fastlane/EGGRUMBLE_V3_LSS_OPTIONAL32.json'", push)
        self.assertIn("      - 'quality_gameplay/gq8_lss_real31_20261117/**'", push)
        self.assertIn("    branches: [rc/p0d-s1-kids-rc01]", rest)

    def test_same_head_strict_and_actual_source_not_fake_pass(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('gh api "repos/${GITHUB_REPOSITORY}/git/ref/heads/rc/p0d-s1-kids-rc01"', text)
        self.assertIn("BASE31_SHA=f77b4d4393d9e9b19b65566413432a7a9f13962b", text)
        self.assertIn("BASE31_RUN=44232589258", text)
        self.assertIn("LSS32_NOT_CURRENT_RC_ACCEPTANCE", text)
        self.assertIn('--head "${{ steps.official.outputs.source_sha }}"', text)
        self.assertIn('test "$H" = "${{ steps.official.outputs.sha }}"', text)
        self.assertIn("CURRENT31_REAL_SOURCE.project.json", text)
        self.assertIn("LSS_REAL32_STUDIO.rbxlx", text)
        self.assertIn("LSS_OFF31_STUDIO.rbxlx", text)
        self.assertIn("test_rc_auto_follow.py", text)

if __name__ == "__main__":
    unittest.main()
