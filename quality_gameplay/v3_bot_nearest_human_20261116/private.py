#!/usr/bin/env python3
"""Private 21-source real Rojo candidate; uses original 482 + 484 + 531 only."""
import argparse, hashlib, json, os, xml.etree.ElementTree as ET
from pathlib import Path
from patch_nearest import apply, git_blob, ORIGINAL_AI_GIT_BLOB

OWNER_PROJECT="EGGRUMBLE_V3_STUDIO.project.json"
OWNER_PROJECT_GIT_BLOB="1d3e5bdc9ac2ac3fb6e70110ff3c6636d70fc714"
OWNER_HOST_GIT_BLOB="7162b209bf67b74a71553217f3f744e072a0365d"
HOST="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
BOT="EGGRUMBLE_BotActors.luau"

def paths(project):
    m={}
    def walk(node):
        for key,v in node.items():
            if key.startswith("$"): continue
            if "$path" in v:
                assert set(v)=={"$path"}
                file=v["$path"]
                assert Path(file).name==file and file.endswith(".luau")
                assert key not in m, "duplicate script name"
                cls="Script" if file.endswith(".server.luau") else ("LocalScript" if file.endswith(".client.luau") else "ModuleScript")
                m[key]=(file,cls)
            else: walk(v)
    walk(project["tree"])
    if len(m)!=21 or sum(cls=="Script" for _,cls in m.values())!=1 or len({f for f,_ in m.values()})!=21:
        raise ValueError("RED original 21-script source/class manifest")
    return m

def assemble(author:Path, member:Path, out:Path):
    raw=(author/OWNER_PROJECT).read_bytes()
    if git_blob(raw)!=OWNER_PROJECT_GIT_BLOB:raise ValueError("RED original project changed")
    manifest=json.loads(raw)
    source_map=paths(manifest)
    bot_raw=(member/BOT).read_bytes()
    on,off=apply(bot_raw)
    host=(member/HOST).read_bytes()
    if host.count(b"session.isCurrentHuman=function")!=1 or host.count(b"and session.rules.castles[tostring(player.UserId)].isAI~=true")!=1:
        raise ValueError("RED actual #531 Host membership lost")
    out.mkdir(parents=True,exist_ok=True)
    source_hashes={}
    for name,(filename,cls) in source_map.items():
        data=on if filename==BOT else (host if filename==HOST else (author/filename).read_bytes())
        (out/filename).write_bytes(data)
        source_hashes[name]=hashlib.sha256(data).hexdigest()
    (out/OWNER_PROJECT).write_bytes(raw)
    (out/"GQ_BOT_NEAREST_OFF.luau").write_bytes(off)
    report={"profile":"PRIVATE_21_GQ_BOT_NEAREST","official_rc_adopted":False,
       "source_count":21,"source_exact":False,"author_game_head":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
       "author_ai_head":"6b52eaf1f2725496277998fe0c5532b7a8fcaab5",
       "member531_author_head":"4a8fd3823b8ebd4a9867a6f54a16d4db0a423a6e",
       "original_ai_git_blob":ORIGINAL_AI_GIT_BLOB,
       "script_sha256":source_hashes,
       "owner_studio":"NOT_TESTED","android_15min":"NOT_TESTED"}
    (out/"GQ_PRIVATE21_RECEIPT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("GQ_PRIVATE21_PREP source exact 19 original + Host membership + one nearest BotActor")

def verify(out:Path,place:Path):
    source_map=paths(json.loads((out/OWNER_PROJECT).read_text()))
    actual={}
    for item in ET.parse(place).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in {"Script","LocalScript","ModuleScript"}:continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        txt=props.findtext("ProtectedString[@name='Source']")
        if txt is None:txt=props.findtext("string[@name='Source']")
        if txt is None or name in actual:raise ValueError("RED duplicate/missing script Source")
        actual[name]=(cls,txt.replace("\r\n","\n"))
    if len(actual)!=21:raise ValueError("RED actual real Place source count="+str(len(actual)))
    for name,(file,cls) in source_map.items():
        if name not in actual or actual[name][0]!=cls:
            raise ValueError("RED wrong source class/name "+name)
        expected=(out/file).read_text().replace("\r\n","\n")
        if actual[name][1]!=expected:
            raise ValueError("RED actual Rojo embedded source mismatch "+name)
    receipt=json.loads((out/"GQ_PRIVATE21_RECEIPT.json").read_text())
    receipt.update({"source_exact":True,"actual_source_count":len(actual),
                    "private_place_bytes":place.stat().st_size,
                    "private_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()})
    (out/"GQ_PRIVATE21_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ_BOT_NEAREST_TRUE_ROJO_SOURCE_CLASS_EXACT_21_PASS",place.stat().st_size)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("assemble","verify"))
    ap.add_argument("--author",type=Path)
    ap.add_argument("--member",type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--place",type=Path)
    a=ap.parse_args()
    if a.action=="assemble":
        if not a.author or not a.member:ap.error("assemble requires --author and --member")
        assemble(a.author,a.member,a.out)
    else:
        if not a.place:ap.error("verify requires --place")
        verify(a.out,a.place)
if __name__=="__main__":
    main()
