#!/usr/bin/env python3
"""Source integration and route connectivity contracts, not Roblox engine movement proof."""
from __future__ import annotations
import hashlib,importlib.util,math,re,unittest
from pathlib import Path
HERE=Path(__file__).resolve();ROOT=HERE.parents[1];REPO=HERE.parents[3]
BASE=REPO/"handoffs/P0D-FIRST90-GUIDED-H1-20261113-01/inputs/Game.server.luau"
SOLO=ROOT/"inputs/StudioSoloPreviewRules.luau"
SKY=REPO/"handoffs/P0D-B42-V7-SKYCASTLE-20261113-01/src/H1FunWorld_SKY_CASTLE_TEST.server.luau"
def gitblob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
spec=importlib.util.spec_from_file_location("p0d_solo_assembler",ROOT/"tools/assemble.py")
assembly=importlib.util.module_from_spec(spec);spec.loader.exec_module(assembly)
PAT=re.compile(r'path\("([^"]+)",Vector3.new\(([^)]*)\),Vector3.new\(([^)]*)\),([0-9.]+),')
def vec(a):return tuple(float(t) for t in a.split(","))
def links():
 return {name:(vec(a),vec(b),float(width)) for name,a,b,width in PAT.findall(SKY.read_text("utf8"))}
class IsolatedStudioSolo(unittest.TestCase):
 def test_policy_original_source(self):
  self.assertEqual(gitblob(SOLO.read_bytes()),"22e7e22e8837dbf44c57fdfb30efd480457022fb")
 def test_original_b42_game_not_rewritten(self):
  self.assertEqual(gitblob(BASE.read_bytes()),"21b866e801a53ba7ebd66132ae55fe28608750d6")
 def test_original_unchanged_sky(self):
  self.assertEqual(gitblob(SKY.read_bytes()),"0a6360392f4384dc2f0ab1e9afc1d840d66a22b8")
 def test_patch_original_one_game(self):
  before=BASE.read_text("utf8");after=assembly.upgrade_game(before)
  self.assertEqual(after.count("StudioSolo.canStart("),2)
  self.assertEqual(after.count("StudioSolo.emptyWinner("),1)
  self.assertEqual(after.count('remote.Name = "TrapRaidersS1Remote"'),1)
  self.assertEqual(after.count("remote.OnServerEvent:Connect("),1)
  self.assertEqual(after.count("local function resetRound()"),1)
  self.assertEqual(after.count("local function tickRound()"),1)
  self.assertEqual(after.count("horde:hit("),before.count("horde:hit("))
 def test_patch_idempotence_fails_closed(self):
  patched=assembly.upgrade_game(BASE.read_text("utf8"))
  with self.assertRaises(AssertionError):assembly.upgrade_game(patched)
 def test_public_starts_two_teams_only(self):
  s=SOLO.read_text("utf8")
  self.assertIn("if count >= minPlayers and red > 0 and blue > 0 then",s)
  self.assertIn("isStudio == true and count == 1",s)
  self.assertIn("red + blue == 1",s)
  self.assertIn("return nil -- don't auto-end private 1-client",s)
  for api in ('Instance.new("RemoteEvent")',"DataStoreService","MarketplaceService"):
   self.assertNotIn(api,s)
 def test_route_joins_original_sky_walkway(self):
  q=links()
  for p in ["SKY_RAMP_RED","SKY_WALKWAY","SKY_RAMP_BLUE",
            "SKY_FORT_ENTRY_RED","SKY_FORT_ENTRY_BLUE",
            "SKY_FORT_ESCAPE_RED","SKY_FORT_ESCAPE_BLUE"]:
   self.assertIn(p,q)
  self.assertEqual(q["SKY_RAMP_RED"][1],q["SKY_WALKWAY"][0])
  self.assertEqual(q["SKY_WALKWAY"][1],q["SKY_RAMP_BLUE"][0])
  self.assertEqual(q["SKY_FORT_ENTRY_RED"][0],q["SKY_WALKWAY"][0])
  self.assertEqual(q["SKY_FORT_ENTRY_BLUE"][0],q["SKY_WALKWAY"][1])
 def test_platform_edges_and_return_pad_vicinity(self):
  q=links()
  for team,s in (("RED",-1),("BLUE",1)):
   entry=q["SKY_FORT_ENTRY_"+team];escape=q["SKY_FORT_ESCAPE_"+team]
   x,y,z=entry[1]
   self.assertLessEqual(abs(x),25);self.assertEqual(y,32);self.assertGreaterEqual(z,39)
   x,y,z=escape[0]
   self.assertLessEqual(abs(x),25);self.assertEqual(y,32);self.assertTrue(39<=z<=59)
   x,y,z=escape[1]
   self.assertEqual((x,y,z),(s*82,0,22))
   self.assertLessEqual(math.dist((x,z),(s*82,20)),12)
 def test_source_slope_policy_and_symmetry(self):
  q=links()
  for key,(a,b,w) in q.items():
   horizontal=math.hypot(b[0]-a[0],b[2]-a[2])
   self.assertGreater(horizontal,0)
   self.assertLessEqual(abs(b[1]-a[1])/horizontal,0.55+1e-9,key)
  for suffix in ("ENTRY","ESCAPE"):
   red=q["SKY_FORT_"+suffix+"_RED"]
   blue=q["SKY_FORT_"+suffix+"_BLUE"]
   self.assertEqual(red[2],blue[2])
   for t in (0,1):
    self.assertEqual(red[t][0],-blue[t][0])
    self.assertEqual(red[t][1:],blue[t][1:])
 def test_original_world_one_scene_only(self):
  s=SKY.read_text("utf8")
  self.assertEqual(s.count('local world=Instance.new("Folder")'),1)
  self.assertIn('assert(not arena:FindFirstChild("H1_FUN_WORLD")',s)
  self.assertIn('if not RunService:IsStudio() then',s)
  self.assertIn('fort:SetAttribute("FreeToAllRoles",true)',s)
if __name__=="__main__":unittest.main(verbosity=2)
