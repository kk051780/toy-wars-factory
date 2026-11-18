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
  self.assertIn("if not state or not state.active then",patch_src)
  self.assertIn("lastCharmAttack[model]=now",patch_src)
  self.assertNotIn("if dealt>0 then lastCharmAttack[model]=now end",patch_src)
  self.assertIn('model:SetAttribute("EGGRUMBLE_NeutralCharmUntil",nil)',patch_src)
  self.assertIn('model:SetAttribute("EGGRUMBLE_NeutralSeals",nil)',patch_src)
  # Safety applies to generated runtime, not the composer's rejected-token strings.
  self.assertIn('if any(x in source for x in',patch_src)
 def test_identity_and_session_lifecycle(self):
  src=(HERE/"compose_charm44.py").read_text(encoding="utf8")
  for marker in ("EGGRUMBLE_NeutralInstanceId","neutralById[neutralId]=",
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
 # These are needed on the ACTUAL selected Real44 script, not just composer text.
 assert "if not state or not state.active then" in src, "RED_REENTRY_LOCKED_OUT_AFTER_RETIRE"
 assert "if dealt>0 then lastCharmAttack[model]=now end" not in src, "RED_IDLE_AI_UNBOUNDED_ATTACKS"
 assert "lastCharmAttack[model]=now" in src, "RED_IDLE_ALLY_ATTACK_BUDGET"
 for marker in ('model:SetAttribute("EGGRUMBLE_NeutralCharmUntil",nil)',
                'model:SetAttribute("EGGRUMBLE_NeutralSeals",nil)'):
  assert marker in src, "RED_CHARM_EXPIRED_VISUAL_LEAK"
 def contract_valid(candidate:str):
  return (candidate.count("if not state or not state.active then")==1
          and candidate.count("lastCharmAttack[model]=now")==1
          and 'if dealt>0 then lastCharmAttack[model]=now end' not in candidate
          and 'model:SetAttribute("EGGRUMBLE_NeutralCharmUntil",nil)' in candidate
          and 'model:SetAttribute("EGGRUMBLE_NeutralSeals",nil)' in candidate)
 assert contract_valid(src)
 for broken in (
  src.replace("if not state or not state.active then","if not state then",1),
  src.replace("lastCharmAttack[model]=now","if dealt>0 then lastCharmAttack[model]=now end",1),
  src.replace('model:SetAttribute("EGGRUMBLE_NeutralCharmUntil",nil)',"-- REMOVED",1),
  src.replace('model:SetAttribute("EGGRUMBLE_NeutralSeals",nil)',"-- REMOVED",1)):
  assert not contract_valid(broken), "RED_MUTANT_NOT_REJECTED"
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
