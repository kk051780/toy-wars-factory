#!/usr/bin/env python3
"""Deterministic source contracts. Real Luau VM and Rojo checked in CI separately."""
import hashlib,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=Path(__file__).resolve().parents[3]
V6=REPO/"handoffs/P0D-FIRST90-MUSOUV6-BRIDGE-20261113-01"
def blob(p):
    s=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(s)).encode()+b"\0"+s).hexdigest()
class UpgradeContract(unittest.TestCase):
    def test_v7_exact_original_author(self):
        self.assertEqual(blob(ROOT/"inputs/MusouHorde.luau"),
                         "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38")
    def test_v6_original_author(self):
        self.assertEqual(blob(V6/"inputs/MusouHorde.luau"),
                         "e67b186f08a0e9ca20d5f09a7c5b22205e2b7240")
    def test_b42_same_server_game(self):
        self.assertEqual(blob(REPO/"handoffs/P0D-FIRST90-GUIDED-H1-20261113-01/inputs/Game.server.luau"),
                         "21b866e801a53ba7ebd66132ae55fe28608750d6")
    def test_b42_same_client_hud(self):
        self.assertEqual(blob(REPO/"handoffs/P0D-FIRST90-GUIDED-H1-20261113-01/inputs/HUD.client.luau"),
                         "ce6707dc1f833600e1c6913504d30911b24cb2a4")
    def test_module_public_api(self):
        def api(p):return set(re.findall(r"function Horde[.:](\w+)\s*\(",p.read_text("utf8")))
        self.assertEqual(api(ROOT/"inputs/MusouHorde.luau"),api(V6/"inputs/MusouHorde.luau"))
        self.assertEqual(api(ROOT/"inputs/MusouHorde.luau"),{"new","clear","reset","livingCount","eliteWarningSeconds","hit","tick"})
    def test_v7_visual_and_true_damage(self):
        s=(ROOT/"inputs/MusouHorde.luau").read_text("utf8")
        for x in ('Instance.new("BillboardGui")',"m.popup", "beforeHp", "m.hp", "m.deadUntil", ".72", "m.arms[1].Orientation"):
            self.assertIn(x,s)
    def test_single_game_no_new_owner(self):
        s=(ROOT/"inputs/MusouHorde.luau").read_text("utf8")
        self.assertNotIn('Instance.new("RemoteEvent")',s)
        self.assertNotIn("DataStoreService",s)
        self.assertNotIn("MarketplaceService",s)
    def test_combat_source_unchanged(self):
        self.assertEqual(blob(ROOT/"inputs/MusouCombatRules.luau"),
                         "7865af9fb057a368e146941ac5bd7bf89cddc88b")
if __name__=="__main__":unittest.main(verbosity=2)
