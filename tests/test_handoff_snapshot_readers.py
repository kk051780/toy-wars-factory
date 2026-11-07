"""Fail-closed reader contract regression (text source, NOT GitHub API attestation)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
 "AGENTS.md",
 "ops/CHATGPT_GAME_REPAIR_PROMPT.md",
 "ops/CHATGPT_INTEGRATION_REVIEW_PROMPT.md",
 "tools/build_handoff.py",
]

class SnapshotReaderContract(unittest.TestCase):
    def test_reader_sources_agree_on_snapshot_ref_and_stale_hold(self):
        for path in FILES:
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("twf-handoff-snapshots", source)
                self.assertIn("status/LATEST_STATE.json", source)
                self.assertIn("source_revision", source)
                self.assertIn("UNTRUSTED_STALE", source)
                self.assertIn("HOLD_ENGINE_UNVERIFIED", source)
                self.assertIn("main", source)
    def test_reader_protocol_never_downgrades_main_or_approval_hold(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        docs = (ROOT / "docs/QA_HANDOFF_PRIVILEGE_SPLIT.md").read_text(encoding="utf-8")
        self.assertIn("Main is the authoritative source", agents)
        self.assertIn("only status/", agents)
        self.assertIn("only status/", docs)
        self.assertIn("does NOT mean active saved ChatGPT Automations", docs)
        self.assertIn("not certify independent code security review", docs)
    def test_producer_is_passive_data_branch_only(self):
        workflow = (ROOT / ".github/workflows/handoff-sync.yml").read_text(encoding="utf-8")
        self.assertIn("snapshot_ref='refs/heads/twf-handoff-snapshots'", workflow)
        self.assertNotIn("git push origin HEAD:main", workflow)
        self.assertIn("    permissions:\n      contents: read", workflow)

if __name__ == "__main__":
    unittest.main()
