#!/usr/bin/env python3
import unittest,tempfile,json
from pathlib import Path
from compose_real42_guardians import compose,flatten,H,C,G,R,N
class TestGuard42(unittest.TestCase):
 def base(self,root:Path,broken:str=""):
  d=root/"source";d.mkdir()
  host='local SiegeBridge=require(script.Parent:WaitForChild("EGGRUMBLE_CastleSiegeBridge"))\n'
  host+='session.castleSiegeAttack=SiegeBridge.attach(session,Rules)\n'
  host+='session.refresh=function()\n'
  host+='if abandoned then session.rules.phase="ABANDONED" end\n'
  combat='count+=hitBotHeroes(session,p,root,char,at,range,damage,shape)\n'
  bridge='for id in pairs(session.rules.castles) do states[id]=Policy.new(epoch,id) end\n'
  if broken=="combat":combat*=2
  if broken=="bridge":bridge=""
  src={
   "EGGRUMBLE_LobbyCastleModesPreview":host,
   "EGGRUMBLE_SevenRoleCombat":combat,
   "EGGRUMBLE_CastleSiegeBridge":bridge,
   "EGGRUMBLE_CastleMatchRules":"return {}"}
  for i in range(37):src["GQ_FIXTURE_"+str(i)]="return {}"
  project={"tree":{"$className":"DataModel","ServerScriptService":{"$className":"ServerScriptService"}}}
  for name,text in src.items():
   file=d/(name+".luau");file.write_text(text)
   project["tree"]["ServerScriptService"][name]={"$path":"source/"+file.name}
  f=root/"original.project.json";f.write_text(json.dumps(project))
  return f
 def test_positive_and_anchor_mutants(self):
  with tempfile.TemporaryDirectory() as temp:
   r=Path(temp);source=self.base(r)
   out=r/"staged"/"source42.project.json"
   receipt=compose(source,out)
   self.assertEqual(receipt["source_count"],42)
   _,old=flatten(source);_,new=flatten(out)
   self.assertEqual(old[R].read_bytes(),new[R].read_bytes())
   self.assertIn(N,new)
  for flag in ("combat","bridge"):
   with tempfile.TemporaryDirectory() as temp:
    r=Path(temp);source=self.base(r,flag)
    with self.assertRaisesRegex(ValueError,"RED_(COMBAT_ACTUAL_SERVER_HIT|BRIDGE_SHARE_ORIGINAL_STATE)"):
     compose(source,r/"staged"/"source42.project.json")
if __name__=="__main__":unittest.main()
