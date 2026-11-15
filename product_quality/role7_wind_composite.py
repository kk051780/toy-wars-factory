#!/usr/bin/env python3
"""#470 source-exact composition: original #297 selected READY repair + adaptive wind.

Quality stage only. No authorized RC deployment, engine claims or additional Game.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

GAME = "server/Game.server.luau"
WIND = "server/S1RaiderWindRules.luau"
HUD = "client/HUD.client.luau"
HEAD = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
AUTHOR_PLACE_SHA = "349f5258d1bf10829ace6a0b455acf1b646f89d20ac989a4c5d7ca57c34017ed"
AUTHOR_GAME_BLOB = "e897043c9e86184ed221d5af6db2546d8d15f377"
AUTHOR_HUD_BLOB = "22e41fe75e4a450e7d9ba7e511eaac02994840d7"
WIND_BASE_BLOB = "7d5706774b874759e7ab994dc0654c3ae9a46502"
EXPECTED_GAME_BLOB = "19a5a3a0f24255502f6956e114092d3b4273afcf"
EXPECTED_WIND_BLOB = "d66efccbf90028627cd65aa0fb33173506819c11"
EXPECTED_PLACE_SHA = "4f82548f1213675937fe6e8431cd29031fe37abc5c54ef0ceb02ab7d05e88d9a"

GAME_BEFORE = "    if not WindRules.canActivate({\n        phase = match.phase, team = team, role = roles[player] or \"RAIDER\",\n        alive = alive, carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil,\n        active = (windUntil[player] or 0) > now, now = now,\n        lastAt = lastWind[player] or -math.huge,\n        x = root.Position.X, y = root.Position.Y, z = root.Position.Z,\n    }) then return end"
GAME_AFTER = "    local windInput:any = {\n        phase = match.phase, team = team, role = roles[player] or \"RAIDER\",\n        alive = alive, carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil,\n        active = (windUntil[player] or 0) > now, now = now,\n        lastAt = lastWind[player] or -math.huge,\n        x = root.Position.X, y = root.Position.Y, z = root.Position.Z,\n    }\n    -- FB004 quality: exact live floor size. Default OFF keeps official behavior.\n    if ServerStorage:GetAttribute(\"P0D_ADAPTIVE_WIND_FIELD\") == true then\n        local grass=map.model:FindFirstChild(\"GrassArena\")\n        if not grass or not grass:IsA(\"BasePart\") or not grass.Anchored\n            or not grass.CanCollide or grass.Parent~=map.model then return end\n        local localPosition=grass.CFrame:PointToObjectSpace(root.Position)\n        windInput.adaptiveField=true\n        windInput.arenaX=localPosition.X\n        windInput.arenaZ=localPosition.Z\n        windInput.arenaMaxX=math.min(178,grass.Size.X*.5-5)\n        windInput.arenaMaxZ=math.min(140,grass.Size.Z*.5-6)\n    end\n    if not WindRules.canActivate(windInput) then return end"
WIND_BEFORE = "    -- Only ordinary walkable ground in current S1 arena; no sky-flight speed exploit.\n    if math.abs(s.x) > 120 or math.abs(s.z) > 65 or s.y < 1 or s.y > 12 then\n        return false\n    end"
WIND_AFTER = "    -- OFF: preserve old official default 120/65, no new permission in public.\n    -- ON: caller supplies ONLY server-derived GrassArena geometry, not client fields.\n    local limitX,limitZ=120,65\n    local xx,zz=s.x,s.z\n    if s.adaptiveField == true then\n        if not finite(s.arenaX) or not finite(s.arenaZ)\n            or not finite(s.arenaMaxX) or not finite(s.arenaMaxZ)\n            or s.arenaMaxX < 16 or s.arenaMaxZ < 16\n            or s.arenaMaxX > 178 or s.arenaMaxZ > 140 then return false end\n        limitX,limitZ=s.arenaMaxX,s.arenaMaxZ\n        xx,zz=s.arenaX,s.arenaZ\n        -- Hard ceiling inside original server ACTIVE out-of-bounds return (182/144).\n        if math.abs(s.x) > 178 or math.abs(s.z) > 140 then return false end\n    elseif s.adaptiveField ~= nil then\n        return false\n    end\n    if math.abs(xx) > limitX or math.abs(zz) > limitZ or s.y < 1 or s.y > 12 then\n        return false\n    end"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(source):
    data=source.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def get_sources(xml):
    root=ET.fromstring(xml)
    result={}
    items={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        source=props.find("string[@name='Source']")
        if name is None or source is None or source.text is None:raise ValueError("MISSING_SCRIPT_DATA")
        if name in result:raise ValueError("DUPLICATE_SCRIPT:"+name)
        result[name]=source.text
        items[name]=source
    return root,result,items

def assert_locked(xml,source_lock,feature_lock):
    root,sources,items=get_sources(xml)
    if (len(sources)!=82 or source_lock.get("total_scripts")!=82
        or feature_lock.get("total_sources")!=82):
        raise ValueError("SOURCE_COUNT_DRIFT")
    locks=source_lock.get("blobs")
    if not isinstance(locks,dict) or locks!=feature_lock.get("source_gitblobs"):
        raise ValueError("DUAL_LOCK_MISMATCH")
    if Counter(blob(s) for s in sources.values())!=Counter(locks.values()):
        raise ValueError("ACTUAL_PLACE_SOURCE_LOCK_MISMATCH")
    return root,sources,items

def compose(outer_zip):
    with ZipFile(io.BytesIO(outer_zip)) as outer:
        inner=outer.read("P0D_RC82_ROLE7_READY_PRIVATE_SOURCE_PATCH.zip")
    with ZipFile(io.BytesIO(inner)) as z:
        place=z.read("PRIVATE_ROLE7_READY_RC82.rbxlx")
        sl=json.loads(z.read("SOURCE_LOCK.json"))
        fl=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if sha(place)!=AUTHOR_PLACE_SHA or receipt.get("source_rc")!=HEAD:
        raise ValueError("WRONG_ORIGINAL_AUTHOR_ARTIFACT")
    root,sources,items=assert_locked(place,sl,fl)
    for key,wanted in ((GAME,AUTHOR_GAME_BLOB),(HUD,AUTHOR_HUD_BLOB),(WIND,WIND_BASE_BLOB)):
        if sl["blobs"].get(key)!=wanted:raise ValueError("ORIGINAL_AUTHOR_DRIFT:"+key)
    if sources["Game"].count(GAME_BEFORE)!=1 or sources["S1RaiderWindRules"].count(WIND_BEFORE)!=1:
        raise ValueError("AUTHOR_PATCH_CONFLICT_WITH_WIND")
    fixed_game=sources["Game"].replace(GAME_BEFORE,GAME_AFTER,1)
    fixed_wind=sources["S1RaiderWindRules"].replace(WIND_BEFORE,WIND_AFTER,1)
    if blob(fixed_game)!=EXPECTED_GAME_BLOB or blob(fixed_wind)!=EXPECTED_WIND_BLOB:
        raise ValueError("FIXED_SOURCE_REPRODUCIBILITY_FAILURE")
    items["Game"].text=fixed_game
    items["S1RaiderWindRules"].text=fixed_wind
    out=ET.tostring(root,encoding="utf-8")
    if sha(out)!=EXPECTED_PLACE_SHA:raise ValueError("COMPOSED_PLACE_REPRODUCIBILITY_FAILURE")
    _,after,_=get_sources(out)
    for name in sources:
        if name not in ("Game","S1RaiderWindRules") and sources[name]!=after[name]:
            raise ValueError("OTHER_AUTHOR_SOURCE_CHANGED:"+name)
    if sources["TrapRaidersHUD"]!=after["TrapRaidersHUD"]:raise ValueError("HUD_NOT_PRESERVED")
    if "sevenJobSelected[player]~=true" not in fixed_game or "broadcast() -- update all peers after job change" not in fixed_game:
        raise ValueError("ROLE7_AUTHOR_PATCH_REMOVED")
    sl["blobs"][GAME]=fl["source_gitblobs"][GAME]=EXPECTED_GAME_BLOB
    sl["blobs"][WIND]=fl["source_gitblobs"][WIND]=EXPECTED_WIND_BLOB
    assert_locked(out,sl,fl)
    return out,sl,fl,after

def build(outer_zip,output,extract_dir=None):
    place,sl,fl,sources=compose(outer_zip)
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr("COMPOSED_ROLE7_WIND_RC82.rbxlx",place)
        z.writestr("SOURCE_LOCK.json",json.dumps(sl,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(fl,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps({
          "schema":"PQ_AUTHOR297_WIND_COMPOSITE_V1","head":HEAD,
          "scripts":82,"unchanged_author":80,"place_bytes":len(place),
          "place_sha256":sha(place),"source_lock":True,
          "official_rc_write":False,"engine":"NOT_RUN","android":"NOT_RUN",
          "owner":False,"decision":"PRODUCT_NO_GO"},indent=2)+"\n")
    if extract_dir is not None:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for name,src in sources.items():
            (extract_dir/(name+".luau")).write_text(src,encoding="utf-8")
    return len(sources),sha(place)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--author-outer",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    args=p.parse_args()
    n,digest=build(args.author_outer.read_bytes(),args.out,args.extract)
    print("P0D_SOURCE_COMPOSITE_NO_GO",n,digest)
if __name__=="__main__":main()
