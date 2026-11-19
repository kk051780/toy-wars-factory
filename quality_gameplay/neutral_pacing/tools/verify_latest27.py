#!/usr/bin/env python3
"""Verify compiled, actual 27-script Rojo Place preserves 25/26 original sources."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from compose_latest27 import flatten

def check(stage:Path,original26:Path,place:Path):
    stage=stage.resolve(strict=True)
    original26=original26.resolve(strict=True)
    place=place.resolve(strict=True)
    a=json.loads(original26.read_text(encoding="utf-8"))
    b=json.loads((stage/"EGGRUMBLE_GQ_NEUTRAL27.project.json").read_text(encoding="utf-8"))
    t=json.loads((stage/"SOURCE27_RECEIPT.json").read_text(encoding="utf-8"))
    amap=flatten(a["tree"])
    bmap=flatten(b["tree"])
    assert len(amap)==26 and len(bmap)==27
    assert set(bmap)==set(amap)|{("ServerScriptService","EGGRUMBLE_NeutralSpawnPacing")}
    assert t["unchanged_original_count"]==25
    def classify(path):
        return ("LocalScript" if path.name.endswith(".client.luau")
          else ("Script" if path.name.endswith(".server.luau") else "ModuleScript"))
    expected={}
    for key, rel in bmap.items():
        name=key[-1]
        source=(stage/rel).resolve(strict=True)
        assert source.is_file()
        assert name not in expected,("script with duplicate name",name)
        expected[name]=(classify(source),source.read_text(encoding="utf-8").replace("\r\n","\n"))
        if name in t["original26_sha256"] and name!="EGGRUMBLE_SwarmCombat":
            assert hashlib.sha256(source.read_bytes()).hexdigest()==t["original26_sha256"][name]
    assert len(expected)==27
    assert sum(v[0]=="LocalScript" for v in expected.values())==3
    assert sum(v[0]=="Script" for v in expected.values())==4
    assert sum(v[0]=="ModuleScript" for v in expected.values())==20
    swarm=expected["EGGRUMBLE_SwarmCombat"][1]
    assert swarm.count("SpawnPacing.step(")==1
    assert swarm.count("local function credit(")==1
    assert swarm.count("h.Died:Connect(")==1
    assert "local SPAWN_BATCH=5" not in swarm
    assert expected["EGGRUMBLE_NeutralSpawnPacing"][0]=="ModuleScript"
    actual={}
    tree=ET.fromstring(place.read_bytes())
    for elem in tree.iter("Item"):
        cls=elem.attrib.get("class")
        if cls not in {"Script","ModuleScript","LocalScript"}:continue
        node=elem.find("Properties")
        assert node is not None
        name=node.findtext("string[@name='Name']")
        text=node.findtext("ProtectedString[@name='Source']")
        if text is None:text=node.findtext("string[@name='Source']")
        assert name and text is not None
        assert name not in actual,("duplicate runtime script",name)
        actual[name]=(cls,text.replace("\r\n","\n"))
    assert actual==expected,{
        "missing":sorted(set(expected)-set(actual)),
        "extra":sorted(set(actual)-set(expected)),
        "mismatch":sorted(k for k in set(actual)&set(expected) if actual[k]!=expected[k])
    }
    receipt={
        "scope":"private-author26-plus-neutral-pacing-27",
        "source_exact":27,
        "old_script_byte_identical":25,
        "only_authored_swarm_modified":True,
        "unique_new_pacing_module":True,
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
        "artifact_type":"unpublished Roblox Studio rbxlx (XML)",
        "official_rc_adopted":False,
        "studio_play_not_tested":True,
        "android_not_tested":True,
        "owner_not_accepted":True
    }
    (stage/"PLACE27_RECEIPT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ_NEUTRAL_PACING_CURRENT27_SOURCE_EXACT_PASS 27/27")
    print("PRIVATE27_PLACE_BYTES",receipt["place_bytes"],"SHA256",receipt["place_sha256"])
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--stage",required=True,type=Path)
    p.add_argument("--original26",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    args=p.parse_args()
    check(args.stage,args.original26,args.place)
