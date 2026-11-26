#!/usr/bin/env python3
"""Synthetic route mutation gate. Real44 source, Source/Class native in CI separate."""
import json
import tempfile
import unittest
from pathlib import Path
from compose_real46 import compose,flatten,SITES,HOST,ORIG_REQUIRE,EQUIP,POLICY_NAME,RUNTIME_NAME,ROOT

def sample(tmp:Path):
 root=tmp/"old44";root.mkdir()
 server={}
 paths=[]
 for name,sites in SITES.items():
  source="--!strict\n"
  if name==HOST[-1]:
   source+=ORIG_REQUIRE+"\nlocal function begin(session,p,role)\n"
   source+=" "+EQUIP+"\n task.delay(0,function()\n  "+EQUIP+"\n end)\nend\n"
  for victim,amount,kind,attacker in sites:
   source+="-- original existing real damage call from audited 44\n"
   source+=f"local function apply_{len(paths)}() {victim}:TakeDamage({amount}) end\n"
   paths.append((name,victim,amount))
  path=root/(name+".luau" if name!=HOST[-1] else name+".server.luau")
  path.write_text(source)
  server[name]={"$path":path.name}
 for k in range(44-len(SITES)):
  n=f"OtherExistingSource_{k:02d}"
  path=root/(n+".luau")
  path.write_text("--!strict\nreturn {}\n")
  server[n]={"$path":path.name}
 project=root/"SOURCE44.project.json"
 project.write_text(json.dumps({"name":"REAL44_SYNTHETIC","tree":{"ServerScriptService":server}}))
 policy=tmp/"original_policy.luau"
 policy.write_text((ROOT.parent/"EGGRUMBLE-INVUL-20261119"/"InvulnerabilityPolicy.luau").read_text()
                   if (ROOT.parent/"EGGRUMBLE-INVUL-20261119"/"InvulnerabilityPolicy.luau").is_file()
                   else "--!strict\nM.FEATURE_ID=\"GQ8_INVUL_REACTIVE_COUNTER_AWAKENING_V2\"")
 return project,policy,paths
class Integration(unittest.TestCase):
 def test_full_46_13_hooks_off44(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);base,policy,names=sample(root)
   dest=root/"new46"/"LIVE46.project.json"
   compose(base,policy,dest)
   _,o=flatten(base);_,new=flatten(dest)
   self.assertEqual((len(o),len(new)),(44,46))
   self.assertEqual(len(names),13)
   changed=[r for r in o if o[r].read_bytes()!=new[r].read_bytes()]
   self.assertEqual(len(changed),7)
   for r in o:
    if r not in changed:self.assertEqual(o[r].read_bytes(),new[r].read_bytes())
   self.assertEqual(new[HOST].read_text().count("InvulRuntime.attach(session,p,role)"),2)
   self.assertIn(("ServerScriptService",POLICY_NAME),new)
   self.assertIn(("ServerScriptService",RUNTIME_NAME),new)
   receipt=json.loads(dest.with_suffix(".receipt.json").read_text())
   self.assertEqual(receipt["original_direct_hit_sites_guarded"],13)
   self.assertEqual(receipt["original_unmodified_source_count"],37)
   self.assertFalse(receipt["official_rc_adopted"])
 def test_missing_hit_red(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);base,policy,_=sample(root)
   f=base.parent/"EGGRUMBLE_SevenRoleCombat.luau"
   f.write_text(f.read_text().replace("enemyHum:TakeDamage(damage*duel*mark)","enemyHum.Health=0"))
   with self.assertRaisesRegex(ValueError,"RED_UNKNOWN_UNAUDITED_DIRECT_DAMAGE"):
    compose(base,policy,root/"out"/"candidate.project.json")
 def test_extra_damage_red(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);base,policy,_=sample(root)
   f=base.parent/"EGGRUMBLE_SevenRoleCombat.luau"
   f.write_text(f.read_text()+"\nh:TakeDamage(999)\n")
   with self.assertRaisesRegex(ValueError,"RED_UNKNOWN_UNAUDITED_DIRECT_DAMAGE"):
    compose(base,policy,root/"out"/"candidate.project.json")
 def test_unknown_host_red(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);base,policy,_=sample(root)
   f=base.parent/(HOST[-1]+".server.luau")
   f.write_text(f.read_text().replace(EQUIP,"NotTheOriginalCombat.equip(session,p,role)",1))
   with self.assertRaisesRegex(ValueError,"RED_UNEXPECTED_AUTHOR_HOST"):
    compose(base,policy,root/"out"/"candidate.project.json")
if __name__=="__main__":unittest.main()
