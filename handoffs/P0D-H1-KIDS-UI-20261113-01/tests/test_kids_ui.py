"""Check real #251 carrier/role/cooldown HUD adoption against full #255 H1.
Source contracts only: does not run Roblox Studio GUI or physical touch UI.
"""
import hashlib
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import assemble as A

def gitblob(content: bytes):
    return hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()

class P0DH1RealHudAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current=(ROOT/"inputs/HUD.client.luau").read_text(encoding="utf-8")
        cls.old=(A.SRC/"client/HUD.client.luau").read_text(encoding="utf-8")

    def test_exact_immutable_original_source_hud(self):
        self.assertEqual(gitblob(self.old.encode("utf-8")),"6d273404800e1d25fb1405bc52249b3ab47c1b41")

    def test_exact_original_author_new_ui_blob(self):
        self.assertEqual(gitblob(self.current.encode("utf-8")),"313484a69eb10ce01bbdb4872afee215133b01d4")

    def test_unchanged_original_server_game_and_wind_rules(self):
        for rel,sha in A.BASE.items():
            self.assertEqual(gitblob((A.SRC/rel).read_bytes()),sha,rel)
        game=(A.SRC/"server/Game.server.luau").read_text(encoding="utf-8")
        self.assertEqual(game.count('remote.Name = "TrapRaidersS1Remote"'),1)
        self.assertIn('elseif data.action == "WIND_BURST"',game)

    def test_new_hud_carrier_cooldown_tell_and_single_remote(self):
        result=A.check_ui()
        self.assertEqual(result["ux_source_blob"],"313484a69eb10ce01bbdb4872afee215133b01d4")
        self.assertNotEqual(result["ux_source_blob"],result["original_HUD_blob"])
        self.assertEqual(self.current.count('remote:FireServer({action = kind, role = role, seq = seq})'),1)
        self.assertEqual(self.current.count('local carryingEgg ='),1)

    def test_threat_mutation_cases_rejected(self):
        mutations={
            "egg carrying wind unblocked":("and not carryingEgg and windCooldown == 0 and s.windActive ~= true","and windCooldown == 0 and s.windActive ~= true"),
            "egg carrying trap unblocked":("and not carryingEgg and trapCooldown == 0","and trapCooldown == 0"),
            "wind cooldown ignored":("and not carryingEgg and windCooldown == 0 and s.windActive ~= true","and not carryingEgg and s.windActive ~= true"),
            "trap cooldown ignored":("and not carryingEgg and trapCooldown == 0","and not carryingEgg"),
            "wind active state ignored":("and not carryingEgg and windCooldown == 0 and s.windActive ~= true","and not carryingEgg and windCooldown == 0"),
            "wind active false always":("windButton.Active = s.phase == \"ACTIVE\" and s.role == \"RAIDER\"","windButton.Active = false"),
            "trap active false always":("trapButton.Active = s.phase == \"ACTIVE\" and s.role == \"GUARDIAN\"","trapButton.Active = false"),
            "disabled button visual removed":("windButton.AutoButtonColor = windButton.Active","windButton.AutoButtonColor = true"),
            "carrier instruction removed":(r'🥚 卵運搬中\n風走り不可',"迷ったら押して"),
            "guardian instruction removed":(r'🥚 卵運搬中\n罠は使えない',"迷ったら押して"),
        }
        for name,(needle,replacement) in mutations.items():
            self.assertEqual(self.current.count(needle),1,name)
            bad=self.current.replace(needle,replacement,1)
            with tempfile.TemporaryDirectory() as folder:
                pathlib.Path(folder,"HUD.client.luau").write_text(bad,encoding="utf-8")
                with patch.object(A,"IN",pathlib.Path(folder)):
                    with self.subTest(name=name),self.assertRaises(AssertionError):
                        A.check_ui()

    def test_same_game_source_tree_has_single_game(self):
        self.assertEqual(len(list(A.SRC.rglob("Game.server.luau"))),1)
        self.assertEqual(len(list(A.SRC.rglob("H1FunWorld.server.luau"))),1)
        self.assertEqual(len(list(A.SRC.rglob("*.luau"))),25)
        self.assertEqual(len(A.INPUTS),5) # one original world + three D18 + new HUD

if __name__=="__main__":
    unittest.main()
