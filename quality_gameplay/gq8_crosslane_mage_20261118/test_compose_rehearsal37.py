#!/usr/bin/env python3
"""Synthetic structural and mutation probes; CI also uses authentic V3 31/36/32."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from compose_rehearsal37 import compose,flatten,HOST,MAGE,REALM,REGEN,ORIG_REQUIRE,REG_REQUIRE,MAGE_REQUIRE

BASE=[HOST[-1],"EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_SwarmCombat"]+[
 "V3_Source_%02d"%i for i in range(28)]
HOST_TEXT='''local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))
local function a(session,p,role)
 SevenRoleCombat.equip(session,p,role)
 task.defer(function()
  SevenRoleCombat.equip(session,p,role)
 end)
end
'''
def with_host_hooks(source,require,method):
 source=source.replace(ORIG_REQUIRE,ORIG_REQUIRE+"\n"+require)
 import re
 source,n=re.subn(r"(?m)^([ \t]*)SevenRoleCombat\.equip\(session,p,role\)$",
  lambda m:m.group(0)+"\n"+m.group(1)+method+".attach(session,p,role)",source)
 assert n==2
 return source

def generate(root):
 projects={}
 for variant in ("baseline","combined36","mage32"):
  d=root/variant;d.mkdir()
  server={}
  for name in BASE:
   data=HOST_TEXT if name==HOST[-1] else "--!strict\nreturn {}\n"
   if name==HOST[-1] and variant=="combined36":
    data=with_host_hooks(data,REG_REQUIRE,"NaturalRegen")
   if name==HOST[-1] and variant=="mage32":
    data=with_host_hooks(data,MAGE_REQUIRE,"MageRevive")
   f=d/(name+".server.luau");f.write_text(data)
   server[name]={"$path":f.name}
  tree={"ServerScriptService":server}
  if variant=="combined36":
   for route in REALM|REGEN:
    f=d/(route[-1]+(".client.luau" if len(route)>2 else ".server.luau"))
    f.write_text("--!strict\nreturn {}\n")
    node=tree
    for k in route[:-1]:node=node.setdefault(k,{})
    node[route[-1]]={"$path":f.name}
  elif variant=="mage32":
   f=d/(MAGE[-1]+".luau");f.write_text("--!strict\nreturn {}\n")
   server[MAGE[-1]]={"$path":f.name}
  project=d/"v3.project.json"
  project.write_text(json.dumps({"name":variant,"tree":tree}))
  projects[variant]=project
 return projects["baseline"],projects["combined36"],projects["mage32"]

class Gate(unittest.TestCase):
 def test_exact37_and_reversible_hosts(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);base,c36,m32=generate(root)
   target=root/"output"/"REAL37.project.json"
   compose(base,c36,m32,target)
   _,b=flatten(base);_,p=flatten(target);_,c=flatten(c36)
   self.assertEqual((len(b),len(c),len(p)),(31,36,37))
   for k,v in b.items():
    if k!=HOST:self.assertEqual(v.read_bytes(),p[k].read_bytes())
   for k in set(c)-{HOST}:
    self.assertEqual(c[k].read_bytes(),p[k].read_bytes())
   host=p[HOST].read_text()
   self.assertEqual(host.count("NaturalRegen.attach(session,p,role)"),2)
   self.assertEqual(host.count("MageRevive.attach(session,p,role)"),2)
   self.assertEqual(host.count(MAGE_REQUIRE),1)
   self.assertEqual(p[MAGE].read_bytes(),flatten(m32)[1][MAGE].read_bytes())
   receipt=json.loads(target.with_suffix(".receipt.json").read_text())
   self.assertFalse(receipt["official_rc_written"])
   self.assertEqual(receipt["actual_sources"],37)
 def test_reject_stale_mage_host(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);b,c,m=generate(root)
   host=m.parent/(HOST[-1]+".server.luau")
   host.write_text(host.read_text()+"\nMageRevive.attach(session,p,role)\n")
   with self.assertRaisesRegex(ValueError,"RED_AUTHOR_HOST_HOOK_SIGNATURE"):
    compose(b,c,m,root/"out"/"bad.project.json")
 def test_reject_parallel_original_mutation(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);b,c,m=generate(root)
   (c.parent/"V3_Source_00.server.luau").write_text("-- hijacked Game\n")
   with self.assertRaisesRegex(ValueError,"RED_MUTATED_ORIGINAL"):
    compose(b,c,m,root/"out"/"bad.project.json")
 def test_reject_duplicate_mage_route(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);b,c,m=generate(root)
   doc=json.loads(c.read_text())
   doc["tree"]["ServerScriptService"][MAGE[-1]]={"$path":"EGGRUMBLE_NaturalRegen.server.luau"}
   c.write_text(json.dumps(doc))
   with self.assertRaisesRegex(ValueError,"RED_BAD_SOURCE_COUNT"):
    compose(b,c,m,root/"out"/"bad.project.json")
 def test_reject_mage_altered_old_combat(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);b,c,m=generate(root)
   (m.parent/"EGGRUMBLE_SevenRoleCombat.server.luau").write_text("-- wrong combat\n")
   with self.assertRaisesRegex(ValueError,"RED_MUTATED_ORIGINAL"):
    compose(b,c,m,root/"out"/"bad.project.json")
if __name__=="__main__":unittest.main()
