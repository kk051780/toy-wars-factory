"""Fail-closed reader contract regression (text source, NOT GitHub API attestation)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
 "AGENTS.md",
 "ops/CHATGPT_GAME_REPAIR_PROMPT.md",
 "ops/CHATGPT_INTEGRATION_REVIEW_PROMPT.md",
 "tools/build_handoff.py",
 "docs/CHAT_CONTINUITY_PROTOCOL.md",
 "ops/CHATGPT_SYSTEM_REVIEW_PROMPT.md",
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
    def test_continuity_and_system_review_know_immutable_snapshot_fallback(self):
        for path in ("docs/CHAT_CONTINUITY_PROTOCOL.md",
                     "ops/CHATGPT_SYSTEM_REVIEW_PROMPT.md"):
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                for item in ("同一不変", "歴史", "twf-repair-coordinator",
                             "100644", "prior-snapshot-tip", "UNTRUSTED_STALE"):
                    self.assertIn(item, source)
                self.assertNotIn("private GitHub", source)

    def test_continuity_snapshot_does_not_implicitly_authorize_anything(self):
        text = (ROOT / "docs/CHAT_CONTINUITY_PROTOCOL.md").read_text(encoding="utf-8")
        for required in ("schema=2", "canonical_repo=kk051780/toy-wars-factory",
                         "release_decision=HOLD_ENGINE_UNVERIFIED", "source_revision",
                         "GitHub compare", "承認", "公開許可"):
            self.assertIn(required, text)

    def test_scheduled_run_artifact_is_read_only_optional_handoff(self):
        for path in ("AGENTS.md", "docs/CHAT_CONTINUITY_PROTOCOL.md",
                     "tools/build_handoff.py", "docs/QA_HANDOFF_PRIVILEGE_SPLIT.md"):
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                for item in ("toy-wars-handoff", "UNTRUSTED_STALE",
                             "source_revision", "status/"):
                    self.assertIn(item, source)
        workflow = (ROOT / ".github/workflows/handoff-sync.yml").read_text(encoding="utf-8")
        self.assertIn("if: success()", workflow)
        self.assertIn("&& false", workflow)
        self.assertNotIn("if: always()", workflow)

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
