#!/usr/bin/env python3
"""Source-contract guard for real one-Game B42 + native V6 enemy appearance."""
from pathlib import Path
import unittest,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
BASE=REPO/"handoffs/P0D-FIRST90-GUIDED-H1-20261113-01"
def blob(p):
    raw=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
class TestBridge(unittest.TestCase):
 def test_v6_original_blob(self):
    self.assertEqual(blob(ROOT/"inputs/MusouHorde.luau"),"e67b186f08a0e9ca20d5f09a7c5b22205e2b7240")
 def test_original_b42_game_preserved(self):
    self.assertEqual(blob(BASE/"inputs/Game.server.luau"),"21b866e801a53ba7ebd66132ae55fe28608750d6")
 def test_original_b42_hud_preserved(self):
    self.assertEqual(blob(BASE/"inputs/HUD.client.luau"),"ce6707dc1f833600e1c6913504d30911b24cb2a4")
 def test_single_original_first90_server_authority(self):
    src=(BASE/"inputs/Game.server.luau").read_text("utf8")
    self.assertEqual(src.count('remote.Name = "TrapRaidersS1Remote"'),1)
    self.assertEqual(src.count("remote.OnServerEvent:Connect("),1)
    self.assertIn("First90WaypointRules",src)
    self.assertIn("First90GuideRules",src)
 def test_horde_drop_in_public_api(self):
    v6=(ROOT/"inputs/MusouHorde.luau").read_text("utf8")
    prev=(BASE/"inputs/MusouHorde.luau").read_text("utf8")
    sig=lambda s: set(re.findall(r'function Horde[.:](\w+)\s*\(',s))
    self.assertEqual(sig(v6),sig(prev))
    self.assertEqual(sig(v6),{"new","clear","reset","livingCount","eliteWarningSeconds","hit","tick"})
 def test_horde_v6_visual_source_and_no_new_authority(self):
    h=(ROOT/"inputs/MusouHorde.luau").read_text("utf8")
    self.assertIn("m.arms[1].Orientation",h)
    self.assertIn("m.eyes",h)
    self.assertIn("MUSOU_SOURCE_MAP_ARENA_REQUIRED",h)
    self.assertIn("ELITE_SWEEP_DANGER_RADIUS",h)
    self.assertNotIn("OnServerEvent:Connect",h)
    self.assertNotIn("DataStoreService",h)
    self.assertNotIn("RemoteEvent",h)
 def test_immutable_combat_policy(self):
    self.assertEqual(blob(ROOT/"inputs/MusouCombatRules.luau"),
                     "7865af9fb057a368e146941ac5bd7bf89cddc88b")
 def test_no_paid_content(self):
    h=(ROOT/"inputs/MusouHorde.luau").read_text("utf8")
    self.assertNotIn("PromptProductPurchase",h)
    self.assertNotIn("MarketplaceService",h)
if __name__=="__main__":unittest.main(verbosity=2)
