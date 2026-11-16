#!/usr/bin/env python3
"""Unpublished original-#482 21-script source-exact build. One generated host source diff."""
from __future__ import annotations
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

HOST="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
DOMAINS={
    "characters":"EGGRUMBLE_SevenRoleCombat.luau",
    "field":"EGGRUMBLE_LobbyCastleModesPreview.server.luau",
    "battle":"EGGRUMBLE_AttackGeometry.luau",
    "castles_eggs":"EGGRUMBLE_CastleMatchRules.luau",
    "neutrals":"EGGRUMBLE_SwarmCombat.luau",
    "items":"EGGRUMBLE_FieldItemPickups.luau",
    "lobby":"EGGRUMBLE_RoundReplay.luau",
    "balance":"EGGRUMBLE_CombatBalance.luau",
}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def scripts(project:dict)->dict:
    out={}
    def visit(node:dict,name:str=""):
        if not isinstance(node,dict):return
        if "$path" in node:
            assert name not in out and name
            path=node["$path"]
            assert "/" not in path and ".." not in path
            out[name]=(path,"Script" if path.endswith(".server.luau") else
                              "LocalScript" if path.endswith(".client.luau") else "ModuleScript")
        else:
            for k,v in node.items():
                if not k.startswith("$"):visit(v,k)
    visit(project["tree"])
    assert len(out)==21 and len({p for p,c in out.values()})==21
    paths={p for p,c in out.values()}
    assert set(DOMAINS.values()).issubset(paths)
    assert HOST in paths
    return out

def prepare(base:Path,patched:Path,out:Path):
    config=base/"EGGRUMBLE_V3_STUDIO.project.json"
    obj=json.loads(config.read_text(encoding="utf-8"))
    names=scripts(obj)
    out.mkdir(parents=True,exist_ok=True)
    receipt={}
    for script,(path,cls) in names.items():
        raw=(base/path).read_bytes()
        content=patched.read_bytes() if path==HOST else raw
        (out/path).write_bytes(content)
        receipt[script]={"file":path,"class":cls,"baseline_sha256":sha(raw),
                         "candidate_sha256":sha(content),"changed":raw!=content}
    altered=[n for n,v in receipt.items() if v["changed"]]
    assert altered==["EGGRUMBLE_LobbyCastleModesPreview"],str(altered)
    (out/config.name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    record={"sources":receipt,"source_count":21,"original_byte_unchanged":20,
            "modified_only":[HOST],"eight_domain_source_presence":list(DOMAINS),
            "formal_rc_adopted":False,"studio_android_owner_tested":False}
    (out/"SOURCE_RECEIPT.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
    print("GQ_FIELD_EGG_ORIGINAL21_ONE_HOST_20_UNCHANGED_PASS")

def verify(place:Path,package:Path):
    assert place.exists() and place.stat().st_size>0
    receipt=json.loads((package/"SOURCE_RECEIPT.json").read_text())
    observed={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("ModuleScript","Script","LocalScript"):continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        if not name:continue
        code=props.findtext("ProtectedString[@name='Source']")
        if code is None:code=props.findtext("string[@name='Source']")
        assert code is not None, "missing true source "+name
        assert name not in observed, "duplicate script "+name
        observed[name]=(cls,code.replace(chr(13)+chr(10),chr(10)).encode("utf-8"))
    assert set(observed)==set(receipt["sources"]),(set(observed),set(receipt["sources"]))
    for name,meta in receipt["sources"].items():
        cls,actual=observed[name]
        expect=(package/meta["file"]).read_bytes()
        assert cls==meta["class"], "Rojo Class mismatch "+name
        assert sha(actual)==sha(expect)==meta["candidate_sha256"],"source byte mismatch "+name
    report={"private_place_bytes":place.stat().st_size,"private_place_sha256":sha(place.read_bytes()),
            "real_rojo_source_exact":"21/21","unchanged_original_author":"20/21",
            "eight_domain_source_exact":"8/8","official_rc_adopted":False}
    (package/"PLACE_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("GQ_FIELD_EGG_PRIVATE21_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",report["private_place_bytes"],report["private_place_sha256"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("op",choices=["prepare","verify"])
    ap.add_argument("--base",type=Path)
    ap.add_argument("--patched",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--place",type=Path)
    ap.add_argument("--package",type=Path)
    a=ap.parse_args()
    if a.op=="prepare":
        assert a.base and a.patched and a.out
        prepare(a.base,a.patched,a.out)
    else:
        assert a.place and a.package
        verify(a.place,a.package)

if __name__=="__main__":
    main()
