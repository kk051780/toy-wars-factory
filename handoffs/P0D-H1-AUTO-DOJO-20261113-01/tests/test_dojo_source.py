#!/usr/bin/env python3
"""Prove exactly the intended source integration; native Luau checks behavior separately."""
from pathlib import Path
import hashlib,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
REPO=Path(__file__).resolve().parents[3]
UP=REPO/"handoffs/P0D-B42-V7-SKYCASTLE-SOLO-20261113-01"
NEW=ROOT/"dist/EGG_RAID_RUMBLE_B42_V7_SKY_SOLO_AUTO_DOJO_PRIVATE"
spec=importlib.util.spec_from_file_location("p0d_dojo_assembler",ROOT/"tools/assemble.py")
assembly=importlib.util.module_from_spec(spec);spec.loader.exec_module(assembly)
def blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
class AutoDojoSource(unittest.TestCase):
 def test_dojo_original_frozen(self):
  self.assertEqual(blob((ROOT/"inputs/DojoRules.luau").read_bytes()),
    "120bac439c979310c9ddeb2fcf2ffa002b6d1add")
 def test_dojo_no_network_or_store_or_payment(self):
  s="\n".join(line for line in (ROOT/"inputs/DojoRules.luau").read_text("utf8").splitlines() if not line.lstrip().startswith("--"))
  for item in ("Players","DataStoreService","RemoteEvent","FireServer",
               "MarketplaceService","PromptProductPurchase","SetAsync","UpdateAsync"):
   self.assertNotIn(item,s)
 def test_dojo_friend_bonus_and_limits(self):
  s=(ROOT/"inputs/DojoRules.luau").read_text("utf8")
  self.assertIn("Dojo.FRIEND_XP_MULTIPLIER = 1.5",s)
  self.assertIn("Dojo.MAX_LEVEL = 5",s)
  self.assertIn("Dojo.MAX_SECONDS_PER_SKILL = 180",s)
  self.assertIn("Dojo.PVE_BONUS_PER_LEVEL = 0.05",s)
 def test_patch_is_fail_closed(self):
  with self.assertRaises(AssertionError):
   assembly.patch_game("wrong version no original anchors")
  with self.assertRaises(AssertionError):
   assembly.patch_hud("wrong version HUD")
 def test_upstream_solo_source_and_sky_retained(self):
  self.assertEqual(blob((UP/"inputs/StudioSoloPreviewRules.luau").read_bytes()),
                   "22e7e22e8837dbf44c57fdfb30efd480457022fb")
  sky=REPO/"handoffs/P0D-B42-V7-SKYCASTLE-20261113-01/src/H1FunWorld_SKY_CASTLE_TEST.server.luau"
  self.assertEqual(blob(sky.read_bytes()),"0a6360392f4384dc2f0ab1e9afc1d840d66a22b8")
 def test_built_original_authority_and_no_pvp_changes(self):
  if not NEW.is_dir():self.skipTest("assembly runs in next CI stage")
  actual=assembly.sources(NEW)
  self.assertEqual(len(actual),44)
  self.assertEqual(len([p for p in actual if p.endswith("/Game.server.luau")]),1)
  self.assertEqual(len([p for p in actual if p.endswith(".server.luau")]),2)
  g=actual["server/Game.server.luau"].decode("utf8")
  h=actual["client/HUD.client.luau"].decode("utf8")
  self.assertEqual(g.count('remote.Name = "TrapRaidersS1Remote"'),1)
  self.assertEqual(g.count("remote.OnServerEvent:Connect("),1)
  self.assertEqual(g.count("Dojo.pveDamageMultiplier("),2)
  self.assertIn("hum:TakeDamage(Config.CombatDamage[roles[player] or \"RAIDER\"]\n                *earnedDamageMultiplier(player,\"PLAYER\"))",g)
  self.assertIn("Dojo.view(dojoStates[player])",g)
  self.assertIn("SessionAutoDojo",h)
  self.assertNotIn("PromptProductPurchase",actual["server/DojoRules.luau"].decode("utf8"))
 def test_no_drift_in_untouched_41(self):
  if not NEW.is_dir():self.skipTest("assembly runs in next CI stage")
  prev=UP/"dist/EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_STUDIO_SOLO_UNPUBLISHED"
  old=assembly.sources(prev);new=assembly.sources(NEW)
  self.assertEqual(len(old),43)
  self.assertEqual(sorted(p for p in old if old[p]!=new[p]),
     ["client/HUD.client.luau","server/Game.server.luau"])
  self.assertEqual(set(new)-set(old),{"server/DojoRules.luau"})
if __name__=="__main__":unittest.main(verbosity=2)
