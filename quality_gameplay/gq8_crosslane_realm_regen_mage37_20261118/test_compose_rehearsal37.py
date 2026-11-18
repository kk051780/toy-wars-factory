#!/usr/bin/env python3
"""Isolated composer mutations. Uses the ORIGINAL immutable author Luau, not copies."""
import copy,json,tempfile,unittest
from pathlib import Path
from compose_rehearsal37 import compose,HOST,MAGE,REGEN,POLICY,REALM,COMBAT,COMBAT_IMPORT,MAGE_IMPORT,REGEN_IMPORT

ROOT=Path(__file__).resolve().parents[2]
MAGE_SRC=ROOT/"_mage777/handoffs/EGGRUMBLE-MAGE-REVIVE-20261118/EGGRUMBLE_MageRevive.luau"
REGEN_SRC=ROOT/"_regen775/handoffs/EGGRUMBLE-HP-REGEN-20261118/EGGRUMBLE_NaturalRegen.luau"
POLICY_SRC=ROOT/"_regen775/handoffs/EGGRUMBLE-HP-REGEN-20261118/EGGRUMBLE_PassiveRegenPolicy.luau"

def relfiles(project,files):
 model={"name":"fake source harness","tree":{"ServerScriptService":{},"StarterPlayer":{"StarterPlayerScripts":{}}}}
 for i,(route,text) in enumerate(sorted(files.items())):
  file=project.parent/("S"+str(i)+".luau")
  file.write_text(text,encoding="utf-8")
  cur=model["tree"]
  for node in route[:-1]:cur=cur.setdefault(node,{})
  cur[route[-1]]={"$path":file.name}
 project.write_text(json.dumps(model),encoding="utf-8")

class RealAuthorCompositionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.dir=Path(self.tmp.name)
  original=COMBAT_IMPORT+"\n"+"SevenRoleCombat.equip(session,p,role)\n"+"SevenRoleCombat.equip(session,p,role)\n"
  self.originalHost=original
  self.base={HOST:original,COMBAT:"return {}\n",("ServerScriptService","EGGRUMBLE_SwarmCombat"):"return {}\n"}
  for i in range(28):
   self.base[("ServerScriptService","PLACEHOLDER_"+str(i))]="return {}\n"
  assert len(self.base)==31
  self.stage=copy.deepcopy(self.base)
  self.stage[HOST]=original.replace(COMBAT_IMPORT,COMBAT_IMPORT+"\n"+REGEN_IMPORT)
  self.stage[HOST]=self.stage[HOST].replace("SevenRoleCombat.equip(session,p,role)","SevenRoleCombat.equip(session,p,role)\nNaturalRegen.attach(session,p,role)")
  self.stage[REGEN]=REGEN_SRC.read_text(encoding="utf-8")
  self.stage[POLICY]=POLICY_SRC.read_text(encoding="utf-8")
  for route in REALM:self.stage[route]="return {}\n"
  self.mage=copy.deepcopy(self.base)
  self.mage[HOST]=original.replace(COMBAT_IMPORT,COMBAT_IMPORT+"\n"+MAGE_IMPORT)
  self.mage[HOST]=self.mage[HOST].replace("SevenRoleCombat.equip(session,p,role)","SevenRoleCombat.equip(session,p,role)\nMageRevive.attach(session,p,role)")
  self.mage[MAGE]=MAGE_SRC.read_text(encoding="utf-8")
  self.basepath=self.dir/"original31.json"
  self.stagepath=self.dir/"combined36.json"
  self.magepath=self.dir/"mage32.json"
  self.out=self.dir/"result37.json"
  self.save()
 def save(self):
  for proj,files in ((self.basepath,self.base),(self.stagepath,self.stage),(self.magepath,self.mage)):
   relfiles(proj,files)
 def test_good_exact_reversible_37(self):
  result=compose(self.basepath,self.stagepath,self.magepath,self.out)
  data=json.loads(result.with_suffix(".receipt.json").read_text(encoding="utf-8"))
  self.assertEqual(data["source_count"],37)
  self.assertEqual(data["baseline_except_single_host_exact"],30)
  self.assertTrue(data["regen_downed_suppression_source_contract"])
  self.assertFalse(data["formal_rc_written"])
  self.assertEqual(len(data["selected_sha256"]),37)
 def must_reject(self,needle):
  with self.assertRaisesRegex(ValueError,needle):
   compose(self.basepath,self.stagepath,self.magepath,self.out)
 def test_mutant_downed_regen_switch(self):
  self.stage[REGEN]=self.stage[REGEN].replace('p:GetAttribute("EGGRUMBLE_Downed")==true',"false",1)
  self.save();self.must_reject("RED_REGEN_DOWNED_INTERFACE")
 def test_mutant_downed_mage_signal(self):
  self.mage[MAGE]=self.mage[MAGE].replace('e.player:SetAttribute("EGGRUMBLE_Downed",true)',"do end",1)
  self.save();self.must_reject("RED_AUTHOR_MAGE_BLOB")
 def test_mutant_author_host_second_writer(self):
  self.stage[HOST]+="\nNaturalRegen.attach(session,p,role)\n"
  self.save();self.must_reject("RED_REGEN_HOST_HOOKS")
 def test_mutant_author_mage_changed(self):
  self.mage[HOST]+="\nMageRevive.attach(session,p,role)\n"
  self.save();self.must_reject("RED_MAGE_AUTHOR_HOST_DRIFT")
 def test_mutant_old_combat_replaced(self):
  self.stage[COMBAT]="return {attack=function() end}\n"
  self.save();self.must_reject("RED_ORIGINAL_MUTATION")
 def test_mutant_new_revival_dupe(self):
  self.stage[MAGE]=MAGE_SRC.read_text(encoding="utf-8")
  self.save();self.must_reject("RED_SOURCE_COUNTS")
 def test_mutant_original31_combat_drift(self):
  self.mage[COMBAT]="return {extra=function() end}\n"
  self.save();self.must_reject("RED_ORIGINAL_MUTATION")
if __name__=="__main__":unittest.main()
