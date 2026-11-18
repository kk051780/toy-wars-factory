#!/usr/bin/env python3
"""Negative/source-lock QA for singleton live-neutral conversion; requires real source artifact."""
from __future__ import annotations
import argparse, importlib.util, pathlib, unittest

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("gq800_real44",HERE/"compose_charm44.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RuntimeContract(unittest.TestCase):
 def test_exact_policy_author_is_immutable(self):
  self.assertEqual(module.CHARM_BLOB,"0bd81a807ff6a935642a660b9fe9e0fd05ef484c")
 def test_no_second_authority_or_remote(self):
  patch_src=(HERE/"compose_charm44.py").read_text(encoding="utf8")
  self.assertIn("local function releaseCharmed(model:Model)",patch_src)
  self.assertIn("CurseConversionPolicy.seal(state,os.clock()",patch_src)
  self.assertIn("local dealt=strike(ownerId,",patch_src)
  self.assertIn("if m.Parent and h.Health>0 and m.PrimaryPart and not charmedByModel[m]",patch_src)
  self.assertIn("local isCurseAttack=currentZombie(directUser) and directUser.Character==attacker",patch_src)
  self.assertIn("existingSummoned=if numSummoned then",patch_src)
  for bad in ("Instance.new(\"RemoteEvent\")","Instance.new(\"Humanoid\")","DataStoreService","ProcessReceipt"):
   self.assertNotIn(bad,patch_src)
 def test_identity_and_session_lifecycle(self):
  src=(HERE/"compose_charm44.py").read_text(encoding="utf8")
  for marker in ("EGGRUMBLE_NeutralInstanceId","neutralById[neutralId]=m",
                 "session.isCurrentHuman","CurseConversionPolicy.retire(state)",
                 "EGGRUMBLE_NeutralFriendlyOwnerId","lastCharmAttack[model]"):
   self.assertIn(marker,src)
 def test_no_second_humanoid_damage_authority(self):
  src=(HERE/"compose_charm44.py").read_text(encoding="utf8")
  self.assertIn('source.count(\'h:TakeDamage(effectiveDamage)\')!=1',src)
  self.assertNotIn("newNeutralController",src)

def check_actual(baseline:pathlib.Path,output:pathlib.Path,curse:pathlib.Path):
 original,old=module.flatten(baseline)
 selected,new=module.flatten(output)
 assert len(old)==43 and len(new)==44
 assert set(new)==set(old)|{module.CHARM}
 assert module.blob(curse.read_bytes())==module.CHARM_BLOB
 for route,path in old.items():
  if route!=module.SWARM:assert path.read_bytes()==new[route].read_bytes(),route
 src=new[module.SWARM].read_text(encoding="utf8")
 assert src.count("function Swarm.start(session:any)")==1
 assert src.count("local function strike(")==1
 assert src.count("CurseConversionPolicy.seal(")==1
 assert src.count("CurseConversionPolicy.step(")==1
 assert src.count("h:TakeDamage(effectiveDamage)")==1
 assert "session.isCurrentHuman" in src
 assert "CurseConversionPolicy.order" in src
 assert "and not charmedByModel[m]" in src
 assert "releaseCharmed(model)" in src
 assert "local dealt=strike(ownerId," in src
 assert "neutralById[neutralId]=nil" in src
 assert "model:SetAttribute(\"EGGRUMBLE_NeutralFriendlyOwnerId\",nil)" in src
 assert "RemoteEvent" not in src and "DataStoreService" not in src
 for bad in ("KoFence.mayCredit(session,id,m,all)","neutralBudget:acquire","SpawnPacing.step"):
  assert bad in src
 try:
  module.patch(src)
  raise AssertionError("RED_OVERLAY_SECOND_APPLICATION_NOT_REJECTED")
 except ValueError:
  pass
 try:
  module.compose(baseline,curse,output)
  raise AssertionError("RED_OUTPUT_OVERWRITE_NOT_REJECTED")
 except ValueError:
  pass
 print("GQ800_REAL44_MUTATION_AND_SINGLE_AUTHORITY_NEGATIVE_PASS")

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--original43",type=pathlib.Path)
 ap.add_argument("--real44",type=pathlib.Path)
 ap.add_argument("--curse",type=pathlib.Path)
 args=ap.parse_args()
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeContract))
 if not result.wasSuccessful():raise SystemExit(1)
 if args.original43 and args.real44 and args.curse:
  check_actual(args.original43,args.real44,args.curse)
