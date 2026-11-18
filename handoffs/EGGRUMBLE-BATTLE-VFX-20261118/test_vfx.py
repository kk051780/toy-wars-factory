#!/usr/bin/env python3
"""Source-derived real Luau good / mutation RED and small local composer's tests."""
from pathlib import Path
import argparse
import tempfile
import unittest
import json
from compose_vfx33 import compose,files

HERE=Path(__file__).resolve().parent
POLICY=HERE/"EGGRUMBLE_ElementCueSpec.luau"
CLIENT=HERE/"EGGRUMBLE_ElementCueView.client.luau"
TESTS=r'''
local seen={}
for _,name in ipairs({"FIRE","WATER","LIGHTNING","WIND","EARTH","ICE","DIVINE","CURSE"}) do
 local a=M.resolve(name,"ADVANTAGE",false)
 assert(a and a.label~="" and a.mark~="" and a.parts==4 and a.range<=76 and a.lifetime<=.45,"RED_ELEMENT_MISSING")
 assert(not seen[a.shape],"RED_COLOR_ONLY_SHAPE_DUPLICATE")
 seen[a.shape]=true
 local low=M.resolve(name,"IMMUNE",true)
 assert(low and low.parts<=2 and low.range<=48,"RED_LOW_ANDROID_BUDGET")
 assert(low.outcomeLabel=="無効" and low.outcomeSymbol=="×","RED_IMMUNE_NOT_VISIBLE")
end
for _,o in ipairs({"NEUTRAL","ADVANTAGE","RESISTED","IMMUNE","WEAKNESS"}) do
 local x=M.resolve("EARTH",o,true)
 assert(x and #x.outcomeLabel>0 and #x.outcomeSymbol>0,"RED_OUTCOME_NOT_READABLE")
end
assert(M.parse("FIRE|ADVANTAGE|17",true).sequence==17,"RED_VALID_PACKET")
assert(M.parse("DIVINE|WEAKNESS|2147483647",true).element=="DIVINE","RED_BOUNDARY")
for _,raw in ipairs({"", "FIRE|ADVANTAGE|0", "FIRE|ADVANTAGE|2147483648",
 "FIRE|NA|1", "fire|ADVANTAGE|1", "FIRE|ADVANTAGE|1|2",
 "A|ADVANTAGE|1", string.rep("X",70)}) do
 assert(M.parse(raw,true)==nil,"RED_UNTRUSTED_PACKET")
end
print("GQ8_ATTR_VFX_EIGHT_SHAPES_FIVE_RESULTS_LOD_MUTATION_PASS")
'''
def make(out):
    src=POLICY.read_text(encoding="utf-8")
    marker="parts=low and 2 or 4,"
    if not src.rstrip().endswith("return M") or src.count(marker)!=1:
        raise ValueError("RED_POLICY_CHANGED")
    body=src.rstrip()[:-len("return M")]
    p=Path(out)
    p.mkdir(parents=True,exist_ok=True)
    (p/"good.luau").write_text(body+TESTS,encoding="utf-8")
    (p/"mutant.luau").write_text(body.replace(marker,"parts=low and 99 or 4,")+TESTS,encoding="utf-8")
class QA(unittest.TestCase):
    def test_no_server_authority(self):
        c=CLIENT.read_text(encoding="utf-8")
        for forbidden in ("FireServer(","RemoteEvent","TakeDamage(","DataStoreService",
                          "MaxHealth=","Humanoid.Health="):
            self.assertNotIn(forbidden,c)
    def test_source_and_mutant(self):
        with tempfile.TemporaryDirectory() as d:
            make(d)
            self.assertIn("parts=low and 99 or 4", (Path(d)/"mutant.luau").read_text())
    def test_rollback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            s=p/"fake.server.luau";s.write_text("return 42",encoding="utf-8")
            template={"name":"fake","tree":{"$className":"DataModel",
             "ServerScriptService":{"$className":"ServerScriptService"},
             "StarterPlayer":{"$className":"StarterPlayer","StarterPlayerScripts":{
             "$className":"StarterPlayerScripts"}}}}
            for i in range(30):
                template["tree"]["ServerScriptService"][f"F{i}"]={"$path":"fake.server.luau"}
            template["tree"]["StarterPlayer"]["StarterPlayerScripts"]["L"]={"$path":"fake.server.luau"}
            base=p/"31.project.json";base.write_text(json.dumps(template),encoding="utf-8")
            on=p/"on.project.json";off=p/"off.project.json"
            compose(base,on);compose(base,off,True)
            self.assertEqual(len(files(on)[1]),33)
            self.assertEqual(len(files(off)[1]),31)
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--generate");v=a.parse_args()
    if v.generate:make(v.generate)
    else:unittest.main(argv=["test"],verbosity=2)
