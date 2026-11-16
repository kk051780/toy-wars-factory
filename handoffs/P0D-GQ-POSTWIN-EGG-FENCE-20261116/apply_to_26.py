#!/usr/bin/env python3
"""Read-only 26-source original-author composite overlay: ONE rules module replaced.

Existing PR #484 compositor builds the base; this module NEVER copies/reimplements
Game/ART/SCORE/AI and never writes a protected RC. Verify actual Rojo .rbxlx bytes.
"""
import argparse
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

TARGET="EGGRUMBLE_CastleMatchRules"
BEFORE_BLOB="27da5ca1e9e6d9a7afe0674030e387f094ee7492"
AFTER_BLOB="ed87d70e7df94279af737871e8e439b9fc108d4f"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git_blob(path):
    return subprocess.check_output(["git","hash-object",str(path)],text=True).strip()

def all_scripts(project):
    root=project.parent
    tree=json.loads(project.read_text(encoding="utf-8"))["tree"]
    scripts={}
    def walk(node,chain=()):
        if not isinstance(node,dict):return
        if "$path" in node:
            name=chain[-1]
            assert name not in scripts,(name,"duplicate")
            path=(root/node["$path"]).resolve(strict=True)
            kind="Script" if path.name.endswith(".server.luau") else ("LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
            scripts[name]=(kind,path)
        else:
            for k,v in node.items():
                if not k.startswith("$"):walk(v,chain+(k,))
    walk(tree)
    assert len(scripts)==26,len(scripts)
    return scripts

def overlay(args):
    before=Path(args.input).resolve(strict=True)
    after=Path(args.out).resolve()
    patch=Path(args.patched).resolve(strict=True)
    assert before!=after and before.parent==after.parent
    assert git_blob(patch)==AFTER_BLOB,"single-function patch SOURCE_LOCK failed"
    inp=json.loads(before.read_text(encoding="utf-8"))
    selected=inp["tree"]["ServerScriptService"][TARGET]
    assert set(selected)=={"$path"},"Rules script path unexpected"
    original=(before.parent/selected["$path"]).resolve(strict=True)
    assert git_blob(original)==BEFORE_BLOB,"not original #482 egg module"
    original_sources=all_scripts(before)
    receipt_path=before.parent/"SOURCE_RECEIPT.json"
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    assert original_sources[TARGET][1]==original
    assert receipt["source_sha256"][TARGET]==sha(original)
    inp["name"]="EGGRUMBLE_V3_POSTWIN_EGG_26_PRIVATE_NO_RC"
    inp["tree"]["ServerScriptService"][TARGET]={"$path":os.path.relpath(patch,after.parent).replace(os.sep,"/")}
    after.write_text(json.dumps(inp,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    patched_scripts=all_scripts(after)
    assert sum(1 for k,v in patched_scripts.items() if original_sources[k][1]!=v[1])==1
    assert patched_scripts[TARGET][1]==patch
    expected={n:sha(p) for n,(_,p) in patched_scripts.items()}
    assert all(expected[n]==receipt["source_sha256"][n] for n in expected if n!=TARGET)
    assert expected[TARGET]!=receipt["source_sha256"][TARGET]
    receipt["feature_ids"]=["GQ-V3-EGG-TERMINAL-FREEZE-001"]
    receipt["source_status"]="SOURCE_ONLY_STUDIO_NOT_TESTED_NO_RC"
    receipt["source_sha256"]=expected
    receipt["selected_author_original_blob"]=BEFORE_BLOB
    receipt["selected_patch_blob"]=AFTER_BLOB
    receipt["source_script_diff_count"]=1
    targetreceipt=after.parent/"POSTWIN_SOURCE_RECEIPT.json"
    targetreceipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("POSTWIN_26_SOURCE_SELECTIVE_PASS 25 unchanged / 1 patched",TARGET)

def verify(args):
    project=Path(args.project).resolve(strict=True)
    place=Path(args.place).resolve(strict=True)
    selected=all_scripts(project)
    receipt=json.loads((project.parent/"POSTWIN_SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
    expected={n:(kind,p.read_text(encoding="utf-8").replace("\r\n","\n")) for n,(kind,p) in selected.items()}
    assert all(receipt["source_sha256"][n]==sha(path) for n,(_,path) in selected.items())
    actual={}
    for node in ET.fromstring(place.read_bytes()).iter("Item"):
        cl=node.attrib.get("class")
        if cl not in ("ModuleScript","Script","LocalScript"):continue
        props=node.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        assert name and source is not None,("invalid Roblox Script",name)
        assert name not in actual,("duplicate compiled Script",name)
        actual[name]=(cl,source.replace("\r\n","\n"))
    assert expected==actual,{"missing":sorted(set(expected)-set(actual)),"extra":sorted(set(actual)-set(expected)),
                             "mismatch":[n for n in expected.keys()&actual.keys() if expected[n]!=actual[n]]}
    receipt["place_sha256"]=sha(place)
    receipt["place_bytes"]=place.stat().st_size
    (project.parent/"POSTWIN_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("POSTWIN_ROJO_EXACT_26_OF_26_PASS",receipt["place_bytes"],receipt["place_sha256"])

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    o=sp.add_parser("overlay");o.add_argument("--input",required=True);o.add_argument("--out",required=True);o.add_argument("--patched",required=True)
    v=sp.add_parser("verify");v.add_argument("--project",required=True);v.add_argument("--place",required=True)
    args=ap.parse_args()
    (overlay if args.cmd=="overlay" else verify)(args)
