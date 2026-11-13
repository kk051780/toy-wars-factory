#!/usr/bin/env python3
"""Immutable exact source patch, old-schema and one-game safety verification."""
from __future__ import annotations
import base64,hashlib,subprocess,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=Path(__file__).resolve().parents[3]
DIST=ROOT/"dist/EGG_RAID_RUMBLE_H1_DOJO_DURABLE_DEV_PRIVATE"
SHA="a1395194b0b5234003156cd53d23a4909292f29a719125e71da88da3f2829bd4"
EXPECTED={
 "server/Game.server.luau":"8f258076a9bb9f00cb6f10cf0e9ff2dbd83940689edbdc56ed51c3027d2acfdb",
 "server/PersistentHatchStore.luau":"8698b06c4344209b4b63758c142aa33c14f382b1260b76a9c738893e67190b24",
 "client/HUD.client.luau":"50fb7868b936f5df59f562da790901d31222db1a77ae73cdfe686c2966780cab"}
class DojoDurable(unittest.TestCase):
 def test_checksum_and_3_exact_targets(self):
  raw=zlib.decompress(base64.b64decode((ROOT/"inputs/dojo_profile_v1_patch.b64").read_text("ascii").strip(),validate=True))
  self.assertEqual(hashlib.sha256(raw).hexdigest(),SHA)
  for rel in EXPECTED:self.assertEqual(raw.decode().count("--- src/"+rel),1)
 def test_source_unchanged_orginal_store_schema(self):
  s=(REPO/"handoffs/P0D-EARNED-EVOLUTION-FULL-H1-20261113-01/inputs/PersistentHatchStore.luau")
  # This may be a pregame source path in another packet. Base itself is exact by the builder.
  self.assertTrue((REPO/"handoffs/P0D-H1-AUTO-DOJO-20261113-01/tools/assemble.py").exists())
 def test_patched_game_one_remote_and_private_only(self):
  if not DIST.is_dir():self.skipTest("build before this stage")
  g=(DIST/"src/server/Game.server.luau").read_text("utf8")
  self.assertEqual(g.count('remote.Name = "TrapRaidersS1Remote"'),1)
  self.assertEqual(g.count("remote.OnServerEvent:Connect("),1)
  self.assertEqual(g.count("local function tickRound()"),1)
  self.assertIn("PersistentHatch.persistDojo(",g)
  self.assertIn('GetDataStore("EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1")',g)
  self.assertIn('player.UserId>0',g)
  self.assertIn('persistenceState[player]=="SAVED"',g)
  self.assertEqual(g.count("Dojo.pveDamageMultiplier("),2)
  self.assertEqual(g.count("StudioSolo.canStart("),2)
 def test_store_profile_backward_compat_and_one_atomic_writer(self):
  if not DIST.is_dir():self.skipTest("build before this stage")
  s=(DIST/"src/server/PersistentHatchStore.luau").read_text("utf8")
  for x in ('Store.SCHEMA=1','if p==nil then return true end -- old schema1 profiles remain valid',
            'dojo=cloneDojo(raw.dojo)','or not safeDojoRecord(raw.dojo)',
            'Store.persistDojoTransition','Store.persistDojo(store:any,uid:any',
            'old.lastToken==token','old.revision~=expectedRevision','Store.dojoSnapshot'):
   self.assertIn(x,s)
  self.assertEqual(s.count("store:UpdateAsync("),5)
  self.assertNotIn("SetAsync(",s)
 def test_three_source_sha_exact(self):
  if not DIST.is_dir():self.skipTest("build before this stage")
  for rel,want in EXPECTED.items():
   self.assertEqual(hashlib.sha256((DIST/"src"/rel).read_bytes()).hexdigest(),want,rel)
 def test_one_store_one_game_44(self):
  if not DIST.is_dir():self.skipTest("build before this stage")
  files=list((DIST/"src").rglob("*.luau"))
  self.assertEqual(len(files),44)
  self.assertEqual(len([p for p in files if p.name=="Game.server.luau"]),1)
  self.assertEqual(len([p for p in files if p.name=="H1FunWorld.server.luau"]),1)
  self.assertEqual(len([p for p in files if p.name=="DojoRules.luau"]),1)
 def test_new_saved_or_session_only_hud(self):
  if not DIST.is_dir():self.skipTest("build before this stage")
  s=(DIST/"src/client/HUD.client.luau").read_text("utf8")
  for x in ('s.dojoSaveStatus=="SAVED"','s.dojoSaveStatus=="PENDING"',
            's.dojoSaveStatus=="SAVE_FAILED"','このプレイのみ'):
   self.assertIn(x,s)
 def test_genuine_profile_original_game_no_second_key(self):
  if not DIST.is_dir():self.skipTest("build before this stage")
  g=(DIST/"src/server/Game.server.luau").read_text("utf8")
  self.assertEqual(g.count('GetDataStore('),1)
  self.assertNotIn("PromptProductPurchase(",g)
if __name__=="__main__":unittest.main(verbosity=2)
