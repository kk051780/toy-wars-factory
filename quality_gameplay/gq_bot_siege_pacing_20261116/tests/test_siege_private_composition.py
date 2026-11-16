"""Exact author source protection + actual private 22-source staging regression."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "tools"))
from stage_private_v3 import stage, UPSTREAM, AUTHOR_BOT_BLOB, git_blob

class SiegeSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.temp.name)
        cls.manifest = stage(cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_author_blob_still_pinned(self):
        self.assertEqual(
            git_blob((UPSTREAM / "EGGRUMBLE_BotActors.luau").read_bytes()),
            AUTHOR_BOT_BLOB)

    def test_21_originals_plus_one_new(self):
        self.assertEqual(self.manifest["upstream_sources"], 21)
        self.assertEqual(self.manifest["staged_sources"], 22)
        self.assertEqual(len(self.manifest["original_sha256"]), 21)
        self.assertEqual(len(self.manifest["staged_sha256"]), 21)

    def test_exactly_one_author_source_changed(self):
        changed = [name for name, sha in self.manifest["original_sha256"].items()
                   if sha != self.manifest["staged_sha256"][name]]
        self.assertEqual(changed, ["EGGRUMBLE_BotActors.luau"])

    def test_one_surgical_gate_not_new_ai_or_damage(self):
        original = (UPSTREAM / "EGGRUMBLE_BotActors.luau").read_text()
        patched = (self.out / "src/EGGRUMBLE_BotActors.luau").read_text()
        self.assertEqual(original.count("Rules.damageCastle(session.rules,enemy.id,id,26)"), 1)
        self.assertEqual(patched.count("Rules.damageCastle(session.rules,enemy.id,id,26)"), 1)
        self.assertEqual(patched.count("SiegePacing.allow(session,enemy.id,id,now)"), 1)
        self.assertEqual(patched.count("SiegePacing.cancelFailed(session,enemy.id,id,now)"), 1)
        self.assertEqual(patched.count("if not ok then SiegePacing.cancelFailed"), 1)
        self.assertIn("if not ok then SiegePacing.cancelFailed(session,enemy.id,id,now) end\\n           if ok then", patched)
        self.assertNotIn("SiegePacing.cancelFailed", original)
        self.assertEqual(patched.count('WaitForChild("EGGRUMBLE_SiegePacing")'), 1)
        self.assertNotIn("SiegePacing.allow", original)

    def test_original_author_damage_call_is_not_duplicated_by_fault_guard(self):
        patched = (self.out / "src/EGGRUMBLE_BotActors.luau").read_text()
        self.assertEqual(patched.count("Rules.damageCastle(session.rules,enemy.id,id,26)"), 1)
        self.assertEqual(patched.count("SiegePacing.allow"), 1)
        self.assertEqual(patched.count("SiegePacing.cancelFailed"), 1)
        self.assertIn("if ok then", patched)
        self.assertIn("if result.fallen and session.releaseEggs then", patched)

    def test_rojo_map_remains_same_except_added_module(self):
        original = json.loads((UPSTREAM / "EGGRUMBLE_V3_STUDIO.project.json").read_text())
        private = json.loads((self.out / "private_v3.project.json").read_text())
        old = original["tree"]["ServerScriptService"]
        new = private["tree"]["ServerScriptService"]
        self.assertEqual(set(new), set(old) | {"EGGRUMBLE_SiegePacing"})
        self.assertEqual(
            new["EGGRUMBLE_SiegePacing"]["$path"],
            "src/EGGRUMBLE_SiegePacing.luau")
        self.assertEqual(private["tree"]["StarterPlayer"]["StarterPlayerScripts"].keys(),
                         original["tree"]["StarterPlayer"]["StarterPlayerScripts"].keys())

    def test_new_module_stays_server_only_and_rollbackable(self):
        source = (self.out / "src/EGGRUMBLE_SiegePacing.luau").read_text()
        self.assertIn("session.gqBotSiegePacingEnabled == false", source)
        self.assertIn("Pace.MIN_SECONDS_PER_CASTLE = 7.0", source)
        for banned in ["DataStoreService", "RemoteEvent", "MarketplaceService",
                       "TeleportService", "Players:GetPlayers"]:
            self.assertNotIn(banned, source)

    def test_private_receipt_never_calls_it_official(self):
        self.assertEqual(self.manifest["status"], "PRIVATE_SOURCE_CANDIDATE_NOT_RC")
        self.assertEqual(self.manifest["official_rc"], "NOT_INTEGRATED")
        self.assertEqual(self.manifest["studio"], "NOT_TESTED")

if __name__ == "__main__":
    unittest.main()
