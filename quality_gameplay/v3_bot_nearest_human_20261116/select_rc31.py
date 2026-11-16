#!/usr/bin/env python3
"""Source-select ONE BotActors in the REAL prior official V3 31-source Place.

Rebuild both ON and OFF using genuine pinned Rojo. Never writes to official RC.
The official HEAD and passed artifact receipt are immutable and must match.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
from patch_nearest import apply

OFFICIAL_HEAD = "cfe156734b708dc0b15abfadc217dbd15c02e200"
OFFICIAL_RUN = 43857293831
BOT = "EGGRUMBLE_BotActors"
EXPECTED_CLASSES = {"Script":4,"LocalScript":3,"ModuleScript":24}

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def scripts(place: Path) -> dict[str, tuple[str,str]]:
    found={}
    for item in ET.parse(place).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in EXPECTED_CLASSES: continue
        p=item.find("Properties")
        if p is None: raise ValueError("RED script missing properties")
        name=p.findtext("string[@name='Name']")
        text=p.findtext("ProtectedString[@name='Source']")
        if text is None: text=p.findtext("string[@name='Source']")
        if text is None or not name or not name.startswith("EGGRUMBLE_") or name in found:
            raise ValueError("RED missing/ambiguous real Script Name/Source")
        found[name]=(cls,text.replace("\r\n","\n"))
    if len(found)!=31 or dict(Counter(cls for cls,_ in found.values()))!=EXPECTED_CLASSES:
        raise ValueError("RED not exactly 31 genuine scripts and class distribution")
    for required in ("EGGRUMBLE_LobbyCastleModesPreview",BOT,"EGGRUMBLE_SwarmCombat",
                     "EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_MatchResultService"):
        if required not in found: raise ValueError("RED core game authority missing "+required)
    return found

def find_one(root:Path,name:str)->Path:
    found=list(root.rglob(name))
    if len(found)!=1: raise ValueError("RED official artifact ambiguous/missing "+name)
    return found[0]

def get_official(root:Path):
    place=find_one(root,"EGGRUMBLE_V3_RC31_CANONICAL_STUDIO.rbxlx")
    receipt=find_one(root,"EGGRUMBLE_V3_OFFICIAL_RC31_RECEIPT.json")
    m=json.loads(receipt.read_text())
    if m.get("github_commit_sha")!=OFFICIAL_HEAD:
        raise ValueError("RED official RC HEAD not the pinned same-HEAD success")
    if m.get("script_count")!=31 or m.get("script_source_and_class_exact")!="31/31":
        raise ValueError("RED original official source-exact acceptance missing")
    if m.get("place_sha256")!=sha(place.read_bytes()):
        raise ValueError("RED actual official artifact/place SHA mismatch")
    return place,m

def make_project(codes:dict[str,tuple[str,str]],out:Path)->None:
    out.mkdir(parents=True,exist_ok=True)
    tree={"$className":"DataModel",
          "ServerScriptService":{"$className":"ServerScriptService"},
          "StarterPlayer":{"$className":"StarterPlayer",
                           "StarterPlayerScripts":{"$className":"StarterPlayerScripts"}}}
    for name,(cls,source) in sorted(codes.items()):
        if "/" in name or "\\" in name or name.endswith("."):
            raise ValueError("RED script path not safe")
        suffix=(".server.luau" if cls=="Script" else
                (".client.luau" if cls=="LocalScript" else ".luau"))
        file=Path("src")/(name+suffix)
        disk=out/file
        disk.parent.mkdir(parents=True,exist_ok=True)
        disk.write_text(source,encoding="utf-8")
        parent=(tree["StarterPlayer"]["StarterPlayerScripts"] if cls=="LocalScript"
                else tree["ServerScriptService"])
        if name in parent: raise ValueError("RED duplicate source name")
        parent[name]={"$path":file.as_posix()}
    (out/"GQ_RC31.project.json").write_text(
        json.dumps({"name":"EGGRUMBLE_GQ555_SOURCE_SELECTED_PRIVATE31","tree":tree},
                   indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def assemble(artifact:Path,out:Path)->None:
    official,original_receipt=get_official(artifact)
    original=scripts(official)
    on_raw,off_raw=apply(original[BOT][1].encode("utf-8"))
    if off_raw!=original[BOT][1].encode("utf-8"):
        raise ValueError("RED bot OFF rollback mismatch")
    selected=dict(original)
    selected[BOT]=(original[BOT][0],on_raw.decode("utf-8"))
    changed={k for k in original if original[k]!=selected[k]}
    if changed!={BOT}:raise ValueError("RED changes outside one current BotActors")
    make_project(original,out/"OFF")
    make_project(selected,out/"ON")
    before={n:sha(s.encode()) for n,(_,s) in sorted(original.items())}
    after={n:sha(s.encode()) for n,(_,s) in sorted(selected.items())}
    meta={"parent_official_head":OFFICIAL_HEAD,"parent_official_run":OFFICIAL_RUN,
          "parent_official_place_bytes":official.stat().st_size,
          "parent_official_place_sha256":sha(official.read_bytes()),
          "source_count":31,"source_exact":"PENDING_ROJO",
          "original_sources_preserved":"30/31","changed_script":BOT,
          "before_sha256":before,"after_sha256":after,
          "official_rc_changed":False,"real_studio":"NOT_TESTED","android":"NOT_TESTED",
          "owner_accepted":False,"payment_or_publish":False}
    out.mkdir(parents=True,exist_ok=True)
    (out/"GQ555_RC31_SOURCE_RECEIPT.json").write_text(
        json.dumps(meta,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("GQ555_RC31_SOURCE_SELECTION_30_OF_31_PRESERVED",OFFICIAL_HEAD)

def verify(artifact:Path,out:Path,onplace:Path,offplace:Path)->None:
    official,_=get_official(artifact)
    original=scripts(official)
    on=scripts(onplace);off=scripts(offplace)
    if off!=original: raise ValueError("RED OFF31 does not restore source exact official Place")
    delta={name for name in on if on[name]!=original[name]}
    if delta!={BOT}: raise ValueError("RED ON31 alters more or less than one BotActors")
    expected,_=apply(original[BOT][1].encode("utf-8"))
    if on[BOT][1].encode("utf-8")!=expected:
        raise ValueError("RED actual new BotActor mismatch")
    meta=json.loads((out/"GQ555_RC31_SOURCE_RECEIPT.json").read_text())
    for n,(c,s) in on.items():
        if sha(s.encode())!=meta["after_sha256"][n]:
            raise ValueError("RED mismatched expected author source "+n)
    meta.update({"source_exact":"31/31 ON and 31/31 OFF",
                 "on_private_place_bytes":onplace.stat().st_size,
                 "on_private_place_sha256":sha(onplace.read_bytes()),
                 "off_private_place_bytes":offplace.stat().st_size,
                 "off_private_place_sha256":sha(offplace.read_bytes())})
    (out/"GQ555_RC31_SOURCE_RECEIPT.json").write_text(
        json.dumps(meta,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("GQ555_RC31_TRUE_ROJO_ON_OFF_SOURCE_CLASS_EXACT_31_PASS",onplace.stat().st_size)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("assemble","verify"))
    p.add_argument("--official-artifact",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--on-place",type=Path)
    p.add_argument("--off-place",type=Path)
    a=p.parse_args()
    if a.action=="assemble":assemble(a.official_artifact,a.out)
    else:
        if not a.on_place or not a.off_place:p.error("verify requires ON/OFF places")
        verify(a.official_artifact,a.out,a.on_place,a.off_place)

if __name__=="__main__":
    main()
