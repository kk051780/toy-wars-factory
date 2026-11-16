#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import compose as c

class CastleBoardVisibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = c.SOURCE.read_text(encoding="utf-8")
        cls.after = c.patch(cls.original)

    def test_author_source_locked(self):
        self.assertEqual(c.git_blob(self.original.encode("utf-8")), c.ORIGINAL_BLOB)

    def test_reuses_exact_existing_world_gui(self):
        self.assertEqual(self.after.count('FindFirstChildOfClass("BillboardGui")'), self.original.count('FindFirstChildOfClass("BillboardGui")') + 2)
        self.assertEqual(self.after.count("Instance.new(\"BillboardGui\")"), self.original.count("Instance.new(\"BillboardGui\")"))
        self.assertIn("b.AlwaysOnTop=true", self.after)  # original generic board stays source-identical

    def test_castle_core_visibility(self):
        self.assertIn("coreBoard.AlwaysOnTop=false", self.after)
        self.assertIn("coreBoard.MaxDistance=65", self.after)
        self.assertIn("coreBoard.Size=UDim2.fromOffset(160,48)", self.after)
        self.assertEqual(self.after.count("coreBoard.MaxDistance"), 1)

    def test_egg_vault_visibility(self):
        self.assertIn("vaultBoard.AlwaysOnTop=false", self.after)
        self.assertIn("vaultBoard.MaxDistance=40", self.after)
        self.assertIn("vaultBoard.Size=UDim2.fromOffset(115,36)", self.after)
        self.assertEqual(self.after.count("vaultBoard.MaxDistance"), 1)

    def test_real_health_and_egg_refresh_preserved(self):
        self.assertIn('t.Text=(c.isAI and "AI " or "")..id', self.after)
        self.assertIn("session.refresh=function()", self.after)
        self.assertIn("Rules.depositEggs(", self.after)
        self.assertIn("Rules.takeEggs(", self.after)

    def test_match_roles_field_battles_neutral_items_lobby_unchanged(self):
        self.assertIn("SevenRoleCombat.equip(session,p,role)", self.after)
        self.assertIn("SwarmCombat.start(session)", self.after)
        self.assertIn("RaidItemIntake.start(session,root,FieldItems)", self.after)
        self.assertIn("BotActors.start(session,Rules)", self.after)
        self.assertIn('joinQueue("BATTLE_ROYALE",p)', self.after)
        self.assertIn('joinQueue("TEAM",p)', self.after)

    def test_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_LOCK"):
            c.patch(self.original.replace("HP1000", "HP1001"))

    def test_anchor_drop_fails_closed_even_with_new_pinned_blob(self):
        mutant = self.original.replace("board(vault,", "wrong(vault,")
        saved = c.ORIGINAL_BLOB
        try:
            c.ORIGINAL_BLOB = c.git_blob(mutant.encode("utf-8"))
            with self.assertRaisesRegex(ValueError, "vault board anchor"):
                c.patch(mutant)
        finally:
            c.ORIGINAL_BLOB = saved

    def test_exact_rollback_to_original_21_sources(self):
        # All original script contents are never mutated, and the original project is untouched.
        self.assertEqual(c.SOURCE.read_text(encoding="utf-8"), self.original)
        tree=json.loads(c.PROJECT.read_text(encoding="utf-8"))
        self.assertIn(c.HOST_NODE,tree["tree"]["ServerScriptService"])
        with tempfile.TemporaryDirectory() as td:
            receipt=c.compose(Path(td))
            self.assertEqual(receipt["source_count"],21)
            self.assertEqual(receipt["modified_original_script_count"],1)
            self.assertEqual(receipt["formal_rc"],"NOT_INTEGRATED")
            out=Path(td)
            project=json.loads((out/"private.project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["tree"]["ServerScriptService"][c.HOST_NODE]["$path"],"HostOverlay.server.luau")
            host=(out/"HostOverlay.server.luau").read_text(encoding="utf-8")
            self.assertEqual(host,self.after)
            self.assertEqual(c.git_blob(self.original.encode("utf-8")),c.ORIGINAL_BLOB)

if __name__ == "__main__":
    unittest.main()
