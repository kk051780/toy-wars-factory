#!/usr/bin/env python3
"""Build a PRIVATE 22-source Rojo Place from the author's exact 21 scripts.
Never edits author source, official RC, main, or Studio. Only two exact host anchors.
"""
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"EGGRUMBLE_FieldEggDropBounds.luau"
PROJECT="EGGRUMBLE_V3_STUDIO.project.json"
HOST="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
REQUIRE='local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))\n'
ORIGINAL='local landing=Vector3.new(at.X,session.groundY or at.Y,at.Z+17)'
INSERT='local DropBounds=require(script.Parent:WaitForChild("EGGRUMBLE_FieldEggDropBounds"))\n'
FIX='''local home=session.castleLocations[ownerId]
   local safe=DropBounds.recover(mode,root.X,root.Z,at.X,at.Z,
    home and home.X or nil,home and home.Z or nil)
   local landing=Vector3.new(safe.x,session.groundY or at.Y,safe.z+17)'''

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def compose(author:Path,out:Path):
    author=author.resolve(strict=True)
    if out.resolve()==author: raise ValueError("must not write to original author")
    project=json.loads((author/PROJECT).read_text(encoding="utf-8"))
    server=project["tree"]["ServerScriptService"]
    client=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    items=list(server.values())+list(client.values())
    names=[item["$path"] for item in items if "$path" in item]
    assert len(names)==21 and len(set(names))==21, "original Studio game source count changed"
    assert HOST in names and MODULE.is_file(), "missing exact host/module"
    out.mkdir(parents=True,exist_ok=True)
    dest=out/"src"
    dest.mkdir(exist_ok=True)
    receipt={"original_source_count":len(names),"candidate_source_count":22,
             "author_original":{},"candidate":{},"only_changed_original":[HOST]}
    for name in names:
        src=author/name
        data=src.read_bytes()
        receipt["author_original"][name]=sha(data)
        if name==HOST:
            text=data.decode("utf-8")
            assert text.count(REQUIRE)==1 and text.count(ORIGINAL)==1, "host hook drift"
            assert text.count("local function startSession(mode:string)")==1, "host changed"
            text=text.replace(REQUIRE,REQUIRE+INSERT,1).replace(ORIGINAL,FIX,1)
            data=text.encode("utf-8")
            assert data!=src.read_bytes(), "host patch ineffective"
        (dest/name).write_bytes(data)
        if name!=HOST:
            assert (dest/name).read_bytes()==src.read_bytes(), "author source drift"
        receipt["candidate"][name]=sha(data)
    module_data=MODULE.read_bytes()
    (dest/MODULE.name).write_bytes(module_data)
    server["EGGRUMBLE_FieldEggDropBounds"]={"$path":"src/"+MODULE.name}
    for node in items: node["$path"]="src/"+node["$path"]
    receipt["candidate"][MODULE.name]=sha(module_data)
    assert set(receipt["candidate"])==set(receipt["author_original"])|{MODULE.name}
    manifest=out/"EGGRUMBLE_FIELD_EGG_SAFE22.project.json"
    manifest.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"SOURCE22_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ_FIELD_EGG_PRIVATE22_COMPOSE_PASS unchanged_original=20/21 new_policy=1 host_overlay=1")
    return manifest

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--author",type=Path,required=True,help="pinned #482 handoffs/... source directory")
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    compose(args.author,args.out)
