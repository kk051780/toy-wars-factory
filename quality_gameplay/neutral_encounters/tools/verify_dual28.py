#!/usr/bin/env python3
"""Independent private 28-source Rojo XML trace: original 8 game areas, two neutral policies.
No API calls, Roblox writes, RC writes, or claims of live Studio/device tests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

FAIR="EGGRUMBLE_NeutralEncounterFairness"
PACE="EGGRUMBLE_NeutralSpawnPacing"
SWARM="EGGRUMBLE_SwarmCombat"

def flatten(project):
    document=json.loads(project.read_text(encoding="utf-8"))
    mapped={}
    def rec(node,path=()):
        if not isinstance(node,dict): return
        if "$path" in node:
            assert set(node)=={"$path"}
            assert path not in mapped
            mapped[path]=(project.parent/node["$path"]).resolve(strict=True)
        else:
            for k,v in node.items():
                if not k.startswith("$"):rec(v,path+(k,))
    rec(document["tree"])
    return mapped

def class_for(path):
    return ("Script" if path.name.endswith(".server.luau")
       else "LocalScript" if path.name.endswith(".client.luau")
       else "ModuleScript")

def verify(original_project,dual_project,place):
    original_project=original_project.resolve(strict=True)
    dual_project=dual_project.resolve(strict=True)
    place=place.resolve(strict=True)
    before=flatten(original_project)
    after=flatten(dual_project)
    assert len(before)==26 and len(after)==28
    for name in ("EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_LobbyCastleModesPreview",
         "EGGRUMBLE_CastleMatchRules","EGGRUMBLE_FieldItemPickups",
         "EGGRUMBLE_NeutralStoneGiant","EGGRUMBLE_BotActors",
         "EGGRUMBLE_ScoreBalance","EGGRUMBLE_EncounterReadabilityArt"):
        assert ("ServerScriptService",name) in before,("original source missing",name)
    for name in ("EGGRUMBLE_CombatFeel","EGGRUMBLE_ArtDistanceLOD"):
        assert ("StarterPlayer","StarterPlayerScripts",name) in before
    extras={("ServerScriptService",FAIR),("ServerScriptService",PACE)}
    assert set(after)==set(before)|extras,("source map mismatch",len(after))
    receipt_path=dual_project.parent/"DUAL28_SOURCE_RECEIPT.json"
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["unchanged_original26"]==25
    assert receipt["overlaid_original26"]==1
    for key in set(before)-{("ServerScriptService",SWARM)}:
        assert before[key].read_bytes()==after[key].read_bytes(),("ORIGINAL_SOURCE_MUTATED",key)
    original=before[("ServerScriptService",SWARM)].read_text(encoding="utf-8")
    compiled=after[("ServerScriptService",SWARM)].read_text(encoding="utf-8")
    assert original!=compiled
    assert compiled.count('SpawnPacing.step(')==1
    assert compiled.count('EncounterFair.chooseIndex(')==1
    assert compiled.count('SpawnPacing.new(')==1
    assert compiled.count('local function credit(')==1
    assert compiled.count('h.Died:Connect(')==1
    assert compiled.count('ImpactFeedback.ko(')==1
    assert compiled.count('local function addEnemy(')==1
    assert compiled.count('local function aliveTargets(')==1
    assert compiled.count('table.insert(kinds,"BOT")')==1
    assert compiled.count('table.insert(kinds,"HUMAN")')==1
    assert 'local SPAWN_BATCH=5' not in compiled
    assert 'MAX_LOS_RAYS_PER_ATTACK=48' in compiled
    assert 'EncounterFair.clear(encounterFairState)' in compiled
    assert receipt["total_mapped"]==len(after)
    expected={}
    for key,p in after.items():
        name=key[-1]
        assert name not in expected,"duplicate original source names"
        assert hashlib.sha256(p.read_bytes()).hexdigest()==receipt["mapped_sha256"]["/".join(key)],key
        expected[name]=(class_for(p),p.read_text(encoding="utf-8").replace("\r\n","\n"))
    assert sum(c=="LocalScript" for c,_ in expected.values())==3
    assert sum(c=="Script" for c,_ in expected.values())==4
    assert sum(c=="ModuleScript" for c,_ in expected.values())==21
    assert expected[PACE][0]=="ModuleScript" and expected[FAIR][0]=="ModuleScript"
    actual={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in {"Script","LocalScript","ModuleScript"}:continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        body=props.findtext("ProtectedString[@name='Source']")
        if body is None:body=props.findtext("string[@name='Source']")
        assert name and body is not None,("invalid code body",name)
        assert name not in actual,("duplicate Place script",name)
        actual[name]=(cls,body.replace("\r\n","\n"))
    assert expected==actual,{
      "missing":sorted(set(expected)-set(actual)),
      "extra":sorted(set(actual)-set(expected)),
      "mismatch":sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k]),
    }
    proof={
     "status":"PRIVATE_DUAL_NEUTRAL_28_SOURCE_EXACT_PASS_NOT_RC",
     "unchanged_original26":25,"sole_swarm_overlay":1,
     "new_original_policies":[PACE,FAIR],"total_luau":len(actual),
     "place_bytes":place.stat().st_size,
     "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
     "studio":"NOT_TESTED","android":"NOT_TESTED","owner_fun":"NOT_ACCEPTED",
     "official_rc":"NOT_ADOPTED"
    }
    (dual_project.parent/"DUAL28_PLACE_RECEIPT.json").write_text(
        json.dumps(proof,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ_TWO_NEUTRAL_FEATURES_SINGLE_SWARM_28_OF_28_SOURCE_EXACT_PASS")
    print("DUAL28_PRIVATE_PLACE_BYTES",proof["place_bytes"],"SHA256",proof["place_sha256"])
    return proof

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--dual",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    x=p.parse_args()
    verify(x.original,x.dual,x.place)
