#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from compose_mage32 import compose,files,HOST,NEW

HERE=Path(__file__).resolve().parent
SAMPLE='''--!strict
local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))
local function startSession(session,p,role)
 SevenRoleCombat.equip(session,p,role)
 task.delay(.8,function()
  SevenRoleCombat.equip(session,p,role)
 end)
end
Players.PlayerRemoving:Connect(function(p)
  SevenRoleCombat.clear(p)
end)
'''
class Admission(unittest.TestCase):
 def baseline(self,at:Path):
  root=at/"baseline"
  root.mkdir(parents=True)
  server={}
  names=[HOST,"EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_SwarmCombat"]
  names+=["Other%02d"%i for i in range(28)]
  for name in names:
   file=root/(name+".server.luau")
   file.write_text(SAMPLE if name==HOST else ("print("+repr(name)+")\n"))
   server[name]={"$path":file.name}
  project=root/"CURRENT31.project.json"
  project.write_text(json.dumps({"name":"CANONICAL31","tree":{"ServerScriptService":server}}))
  return project
 def test_add32_and_inverse31_preserve_all_others(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   base=self.baseline(root)
   on=root/"artifacts"/"ON32.project.json"
   off=root/"artifacts"/"OFF31.project.json"
   compose(base,on)
   compose(base,off,True)
   _,before=files(base)
   _,after=files(on)
   _,rollback=files(off)
   self.assertEqual((len(before),len(after),len(rollback)),(31,32,31))
   self.assertEqual([key[-1] for key in after if key not in before],[NEW])
   for k,v in before.items():
    self.assertEqual(v.read_bytes(),rollback[k].read_bytes())
    if k[-1]!=HOST:self.assertEqual(v.read_bytes(),after[k].read_bytes())
   altered=next(src.read_text() for k,src in after.items() if k[-1]==HOST)
   self.assertEqual(altered.count("MageRevive.attach(session,p,role)"),2)
   self.assertIn("MageRevive.attach(session,p,role)",altered)
   self.assertEqual(altered.count("local MageRevive=require"),1)
   receipt=json.loads(on.with_suffix(".receipt.json").read_text())
   self.assertEqual(receipt["changed_existing_sources"],[HOST])
   self.assertEqual(receipt["added_sources"],[NEW])
   self.assertTrue(receipt["other30_original_byte_exact"])
   self.assertTrue(json.loads(off.with_suffix(".receipt.json").read_text())["off31_byte_exact"])
 def test_reject_bad_host_signature(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   base=self.baseline(root)
   f=root/"baseline"/(HOST+".server.luau")
   f.write_text("local X=0\n")
   with self.assertRaisesRegex(ValueError,"RED_HOST_COMBAT_REQUIRE_CHANGED"):
    compose(base,root/"output"/"ON32.project.json")
 def test_does_not_touch_original_role_combat_owner(self):
  src=(HERE/"EGGRUMBLE_MageRevive.luau").read_text()
  for key in ("DataStoreService","UpdateAsync","SetAsync","RemoteEvent",
              "EGGRUMBLE_Combo","EGGRUMBLE_NeutralKOs"):
   self.assertNotIn(key,src)
  for key in ("h.HealthChanged:Connect","h.Died:Connect","session.world.Destroying:Connect",
              "MAGE_COOLDOWN_SECONDS=40","DOWNED_SECONDS=60","PROMPT_HOLD_SECONDS=3"):
   self.assertIn(key,src)

if __name__=="__main__": unittest.main()
