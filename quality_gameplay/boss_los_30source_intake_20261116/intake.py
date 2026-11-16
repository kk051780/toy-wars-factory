#!/usr/bin/env python3
"""Read-only #518 canonical boss patch integration into existing #517 single-authority original30.

No new gameplay scripts: reuse #518 exact patch, #517 composer, #482/#484/#485/#487
and original #489/#512/#514. Generated project and private Place only.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

BOSS_NAME = "EGGRUMBLE_NeutralStoneGiant"
BOSS_BLOB = "2670618cba320c51936c750a10e43c194cada0f0"
EXPECTED_NAMES = 30
FIXED_REFS = {
    "game": "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
    "quality": "6b52eaf1f2725496277998fe0c5532b7a8fcaab5",
    "art": "e86702c906bdf9c71adcdf769ae48a206b26607b",
    "score": "438a406ccfda5563053d783d7561797ccd364361",
    "item": "03c51bf5c8d12484bd8dc4667b0d3d3841cb4ddd",
    "combo": "e232b9a8411879c2c1a945c0a8ed09233ca73fff",
    "boss_credit": "0d1be13be6d895bea460ba54aaa91ef346684d7f",
    "heal": "c8a324ad7bb40648d82a5828cbf54e217585fefd",
    "boss_los": "f31081d5cb2bea86d01c76c53bb60cd2f9a8355d",
}

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

def mapped(project: Path):
    data = json.loads(project.read_text(encoding="utf-8"))
    result = {}
    def walk(node, keys=()):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            assert set(node) == {"$path"}, "unexpected manifest authority"
            k = keys[-1]
            assert k not in result, ("duplicate script", k)
            p = (project.parent / node["$path"]).resolve(strict=True)
            assert p.is_file() and p.suffix == ".luau"
            cls = "Script" if p.name.endswith(".server.luau") else (
                "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
            result[k] = (keys, p, cls)
        else:
            for name, child in node.items():
                if not name.startswith("$"):
                    walk(child, keys+(name,))
    walk(data["tree"])
    return data, result

def slot(data: dict, path: tuple[str, ...]):
    node = data["tree"]
    for key in path:
        node = node[key]
    return node

def prepare(base: Path, output: Path, receipt: Path, boss: Path, author_tool: Path):
    data, manifest = mapped(base)
    assert len(manifest)==EXPECTED_NAMES
    assert set(("EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SevenRoleCombat",
                "EGGRUMBLE_BotActors","EGGRUMBLE_FieldItemPickups",
                "EGGRUMBLE_CastleMatchRules","EGGRUMBLE_RoundAttributeFence",
                "EGGRUMBLE_BossCreditPolicy","EGGRUMBLE_ScoreBalance")).issubset(manifest)
    original = manifest[BOSS_NAME][1]
    original_raw = original.read_bytes()
    assert git_blob(original_raw)==BOSS_BLOB,"original author boss drift, abort"
    assert author_tool.is_file() and author_tool.name == "compose_patch.py"
    assert original.resolve()!=boss.resolve()
    boss.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(author_tool),"--source",str(original),"--output",str(boss)],check=True)
    assert original.read_bytes()==original_raw,"original author content changed"
    chosen = boss.read_bytes()
    assert chosen != original_raw and chosen.count(b"h:TakeDamage(28)")==1
    # EXACT SINGLE source difference, no second Game/Boss/Remote.
    new = copy.deepcopy(data)
    bp = manifest[BOSS_NAME][0]
    assert bp == ("ServerScriptService",BOSS_NAME)
    slot(new,bp)["$path"] = os.path.relpath(boss.resolve(),output.parent.resolve()).replace(os.sep,"/")
    new["name"] = "EGGRUMBLE_GQ519_SELECTED_IN_GQ517_30_PRIVATE_NOT_RC"
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _, selected = mapped(output)
    assert set(selected)==set(manifest) and len(selected)==30
    changed=[]
    for name in sorted(manifest):
        before = manifest[name]
        after = selected[name]
        assert before[0]==after[0] and before[2]==after[2]
        if before[1].read_bytes()!=after[1].read_bytes():
            changed.append(name)
    assert changed==[BOSS_NAME],("multiple original script changes",changed)
    # No new server Game, client script, stat/egg authority or duplicate name.
    assert sum(x[2]=="Script" for x in selected.values()) == sum(x[2]=="Script" for x in manifest.values())
    assert sum(x[2]=="LocalScript" for x in selected.values()) == sum(x[2]=="LocalScript" for x in manifest.values())
    assert selected["EGGRUMBLE_LobbyCastleModesPreview"][1]==manifest["EGGRUMBLE_LobbyCastleModesPreview"][1]
    evidence={
        "feature":"GQ518_IN_EXISTING_GQ517_30_SOURCE_INTK_ONLY",
        "fixed_original_author_refs":FIXED_REFS,
        "baseline_source_count":30,
        "selected_source_count":30,
        "unchanged_sources":29,
        "changed_existing_source_only":[BOSS_NAME],
        "original_boss_blob":BOSS_BLOB,
        "source_exact_sha256":{k:sha(v[1].read_bytes()) for k,v in selected.items()},
        "baseline_sha256":{k:sha(v[1].read_bytes()) for k,v in manifest.items()},
        "original_author_scripts_overwritten":0,
        "official_rc_adopted":False,"studio":"NOT_RUN","android":"NOT_RUN",
        "claim_granted":False,"owner_accepted":False,
        "known_live_red":"#512 combo observer Studio-only; #482 original V3 host Studio-only; production live guard unresolved",
    }
    receipt.write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ518_PLUS_GQ517_PRIVATE30_SINGLE_BOSS_SOURCE_SELECT_PASS 29/30 unchanged")

def verify(project: Path, place: Path, receipt: Path):
    _, selected=mapped(project)
    assert len(selected)==30
    roots=ET.fromstring(place.read_bytes())
    observed={}
    for item in roots.iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("ModuleScript","LocalScript","Script"):
            continue
        props=item.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        body=props.findtext("ProtectedString[@name='Source']")
        if body is None:
            body=props.findtext("string[@name='Source']")
        assert name is not None and body is not None
        assert name not in observed,("duplicate actual runtime script",name)
        observed[name]=(cls,body.replace("\r\n","\n"))
    assert set(observed)==set(selected),(len(observed),set(selected)^set(observed))
    for name,(_,path,cls) in selected.items():
        assert observed[name]==(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")),("source/class drift",name)
    record=json.loads(receipt.read_text(encoding="utf-8"))
    assert record["changed_existing_source_only"]==[BOSS_NAME]
    assert record["source_exact_sha256"]=={k:sha(v[1].read_bytes()) for k,v in selected.items()}
    record["place_bytes"]=place.stat().st_size
    record["place_sha256"]=sha(place.read_bytes())
    record["rojo_exact_source_class"]="30/30"
    record["formal_rc_source_count_delta"]=0
    receipt.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ518_PLUS_517_REAL_PRIVATE30_SOURCE_CLASS_EXACT_PASS 30/30",record["place_bytes"],record["place_sha256"])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["prepare","verify"])
    for name in ("base","out","receipt","boss","author-tool","project","place"):
        parser.add_argument("--"+name,type=Path)
    opts=parser.parse_args()
    if opts.mode=="prepare":
        assert all((opts.base,opts.out,opts.receipt,opts.boss,opts.author_tool))
        prepare(opts.base,opts.out,opts.receipt,opts.boss,opts.author_tool)
    else:
        assert all((opts.project,opts.place,opts.receipt))
        verify(opts.project,opts.place,opts.receipt)

if __name__=="__main__":
    main()
