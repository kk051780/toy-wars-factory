#!/usr/bin/env python3
"""FB028 source-exact repair of the FB027 Studio castle bridge false obstacle.
Only one anchored Game source hunk changes; 81 other Lua source bodies stay exact.
Private Playtest .rbxlx is the input; do not publish the full Game/Place to GitHub.
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path
from lxml import etree

PARENT_SHA256 = "5987a2e0d59ddc703975c10c3e017ed62faf25d9b0d62131da0430bb550aace6"
OLD = '''    for _,part in ipairs(workspace:GetPartBoundsInBox(orient,Vector3.new(8,2.3,27))) do
        if part.Parent and part.Parent:FindFirstChildOfClass("Humanoid") then return false end
    end'''
NEW = '''    -- The bridge must begin at the builder's own feet. Ignoring the
    -- placing character here is essential, or the placement box overlaps
    -- the builder's legs and falsely rejects normal bridge placement.
    -- Still reject *other* avatars; no overlap with their Humanoid rigs.
    for _,part in ipairs(workspace:GetPartBoundsInBox(orient,Vector3.new(8,2.3,27))) do
        if not part:IsDescendantOf(player.Character)
            and part.Parent and part.Parent:FindFirstChildOfClass("Humanoid") then
            return false
        end
    end'''

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def blob(source: str) -> str:
    raw=source.encode("utf8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def inventory(root):
    out=[]
    for item in root.xpath("//Item"):
        props=item.find("Properties")
        if props is None: continue
        name=props.find('string[@name="Name"]')
        source=next((v for v in props if v.get("name")=="Source"),None)
        if name is not None and source is not None:
            out.append((name.text or "",source))
    if len(out)!=82 or len({name for name,_ in out})!=82:
        raise AssertionError("WRONG_SOURCE_INVENTORY")
    return out

def patch(parent: Path, output: Path):
    if output.exists(): raise FileExistsError("CANNOT_OVERWRITE")
    data=parent.read_bytes()
    if sha(data)!=PARENT_SHA256: raise AssertionError("WRONG_PARENT_SOURCE_SHA")
    parser=etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    root=etree.fromstring(data,parser)
    items=inventory(root)
    game=[src for name,src in items if name=="Game"]
    if len(game)!=1: raise AssertionError("GAME_AUTHORITY_NOT_UNIQUE")
    old_source=game[0].text or ""
    if old_source.count(OLD)!=1: raise AssertionError("SOURCE_ANCHOR_DRIFT")
    original={name:blob(src.text or "") for name,src in items}
    game[0].text=old_source.replace(OLD,NEW,1)
    new={name:blob(src.text or "") for name,src in inventory(root)}
    changed=[name for name in original if original[name]!=new[name]]
    if changed!=["Game"]: raise AssertionError("UNSAFE_SCRIPT_CHANGE")
    if game[0].text.count("remote.OnServerEvent:Connect(")!=1:
        raise AssertionError("DUPLICATED_REMOTE")
    output.write_bytes(etree.tostring(root,encoding="utf-8",pretty_print=True))
    roundtrip=etree.parse(str(output),parser)
    assert new=={name:blob(src.text or "") for name,src in inventory(roundtrip)}
    return {
        "schema":"FB028_BRIDGE_SELF_COLLISION_FIX",
        "parent_sha256":PARENT_SHA256,
        "place_sha256":sha(output.read_bytes()),
        "place_bytes":output.stat().st_size,
        "changed_sources":["Game"],"unchanged_scripts":81,
        "game_before_blob":original["Game"],
        "game_after_blob":new["Game"],
        "native_luau":"NOT_RUN","rojo":"NOT_RUN",
        "studio":"NOT_RUN","official_rc_adopted":False,
    }

if __name__=="__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: script.py FB027.rbxlx FB028.rbxlx")
    print(json.dumps(patch(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
