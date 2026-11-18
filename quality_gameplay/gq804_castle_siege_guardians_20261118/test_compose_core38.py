#!/usr/bin/env python3
import unittest,tempfile,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compose_core38 import compose,flatten,H,B,RULE
class Tests(unittest.TestCase):
 def make(self,r,broken=False):
  d=r/"sources";d.mkdir()
  host='local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))\n'
  host+='Rules.damageCastle(state,entry.id,from,120)\n'
  host+='for idx,entry in ipairs(roster) do createWorldCastle(session,entry,idx) end\n'
  bot='Rules.damageCastle(session.rules,enemy.id,id,26)\n'
  if broken:bot+=bot
  scripts={"EGGRUMBLE_LobbyCastleModesPreview":host,"EGGRUMBLE_BotActors":bot,
   "EGGRUMBLE_CastleMatchRules":"return {}"}
  scripts.update({f"T_{i}":"return {}" for i in range(33)})
  tree={"$className":"DataModel","ServerScriptService":{"$className":"ServerScriptService"}}
  for name,content in scripts.items():
   (d/(name+".luau")).write_text(content)
   tree["ServerScriptService"][name]={"$path":"sources/"+name+".luau"}
  pr=r/"original.project.json";pr.write_text(json.dumps({"tree":tree}))
  return pr
 def test_single_writer_and_mutant(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);p=self.make(r)
   out=compose(p,r/"out"/"core38.project.json")
   _,files=flatten(out)
   self.assertEqual(len(files),38)
   self.assertIn("SiegeBridge.attach",files[H].read_text())
   self.assertIn("session.castleSiegeAttack",files[B].read_text())
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);p=self.make(r,True)
   with self.assertRaisesRegex(ValueError,"RED_BOT_SIEGE"):
    compose(p,r/"out"/"core38.project.json")
if __name__=="__main__":unittest.main()
