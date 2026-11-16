#!/usr/bin/env python3
"""Apply *only* GQ540's Assassin respawn-stealth fix to GQ530's existing
31-script canonical companion. Reuse all actual 31 author source files.
This is a SOURCE-ONLY downstream candidate, never an official RC write.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

HOST_KEY=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
BOT_KEY=("ServerScriptService","EGGRUMBLE_BotActors")
OLD='      if castle and castle.alive then SevenRoleCombat.equip(session,p,role) end'
NEW="""      if castle and castle.alive then
       -- New life must never inherit the previous avatar's Assassin stealth window.
       -- BotActors reads this Player attribute before its server-side damage.
       p:SetAttribute("EGGRUMBLE_StealthUntil",nil)
       SevenRoleCombat.equip(session,p,role)
      end"""

# The existing official RC31 is authored from #482's longer physical-return
# callback, whereas #484 has a condensed preview callback. Handle only these
# two pinned, explicitly known hosts; fail closed for any other source.
ALT_OLD="""       if rootPart and RoundReplay.returnToActiveCastle(session,p,character,home+Vector3.new(0,7,-45)) then
        SevenRoleCombat.equip(session,p,role)
       end"""
ALT_NEW="""       if rootPart and RoundReplay.returnToActiveCastle(session,p,character,home+Vector3.new(0,7,-45)) then
        -- Reset only the previous avatar's stealth, after valid physical return.
        p:SetAttribute("EGGRUMBLE_StealthUntil",nil)
        SevenRoleCombat.equip(session,p,role)
       end"""

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def scan(project:Path):
    doc=json.loads(project.read_text(encoding="utf-8"))
    roots=doc["tree"]
    found={}
    def descend(part,path=()):
        for n,v in part.items():
            if n.startswith("$"):
                continue
            k=path+(n,)
            if not isinstance(v,dict):
                raise ValueError("RED_INVALID_SCRIPT_MAPPING")
            if "$path" in v:
                if set(v)!={"$path"} or k in found:
                    raise ValueError("RED_DUPLICATE_SCRIPT_OR_MAP")
                found[k]=(project.parent / v["$path"]).resolve(strict=True)
            else:
                descend(v,k)
    descend(roots)
    if len(found)!=31 or len({k[-1] for k in found})!=31:
        raise ValueError("RED_NOT_EXACT_31_UNIQUE_SCRIPT_NAMES")
    if HOST_KEY not in found or BOT_KEY not in found:
        raise ValueError("RED_MISSING_AUTHOR_HOST_OR_BOT")
    return doc,found

def apply(host:str,bot:str)->str:
    # A valid Author31 may have either original #482 physical return or #484
    # shortened callback. Never change any unrecognized Host implementation.
    if host.count(NEW) or host.count(ALT_NEW):
        raise ValueError("RED_ALREADY_PATCHED")
    variant=(OLD,NEW) if host.count(OLD)==1 and ALT_OLD not in host else (
      (ALT_OLD,ALT_NEW) if host.count(ALT_OLD)==1 and OLD not in host else None)
    if variant is None:
        raise ValueError("RED_HOST_RESPAWN_ANCHOR_CHANGED_OR_ALREADY_PATCHED")
    old,new=variant
    if host.count("session.isCurrentHuman=function")!=1 or bot.count("session.isCurrentHuman(player)")!=1:
        raise ValueError("RED_GQ531_CURRENT_MATCH_AUTHORITY_MISSING")
    token='p.CharacterAdded:Connect(function(character)'
    if host.count(token)!=1:
        raise ValueError("RED_NOT_EXACTLY_ONE_CURRENT_CHARACTER_CALLBACK")
    start=host.index(token)
    block=host[start:start+1500]
    needles=['p.Character==character','session.rules.phase=="ACTIVE"']
    if old==ALT_OLD:
        needles+=['if castle and castle.alive and home then',
                  'if rootPart and RoundReplay.returnToActiveCastle(']
    else:
        needles+=['local castle=session.rules.castles[tostring(p.UserId)]']
    needles+=[old]
    pos=[block.find(x) for x in needles]
    if min(pos)<0 or pos!=sorted(pos):
        raise ValueError("RED_NOT_CURRENT_AVATAR_ACTIVE_LIVE_CASTLE")
    result=host.replace(old,new,1)
    if result.replace(new,old,1)!=host:
        raise ValueError("RED_ROLLBACK_NOT_EXACT")
    return result

def prepare(project:Path,receipt_path:Path,out:Path)->Path:
    project=project.resolve(strict=True)
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    original,files=scan(project)
    if receipt.get("source_count")!=31 or receipt.get("official_rc_adopted") is not False:
        raise ValueError("RED_NOT_PINNED_31_SOURCE_RECEIPT")
    for key,src in files.items():
        ident="/".join(key)
        if digest(src.read_bytes())!=receipt["source_sha256"][ident]:
            raise ValueError("RED_EXISTING_AUTHOR_SOURCE_DRIFT "+ident)
    host=files[HOST_KEY].read_text(encoding="utf-8")
    bot=files[BOT_KEY].read_text(encoding="utf-8")
    changed=apply(host,bot)
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    dest=out/"GQ540_RespawnStealth_AuthorHost.server.luau"
    if dest.resolve()==files[HOST_KEY] or dest.resolve()==project:
        raise ValueError("RED_AUTHOR_SOURCE_OVERWRITE")
    dest.write_text(changed,encoding="utf-8")
    relink=copy.deepcopy(original)
    def walk(node,prefix=()):
        for n,v in node.items():
            if n.startswith("$"): continue
            key=prefix+(n,)
            if "$path" in v:
                src=dest if key==HOST_KEY else files[key]
                v["$path"]=os.path.relpath(src,out).replace(os.sep,"/")
            else:walk(v,key)
    walk(relink["tree"])
    relink["name"]="GQ540_EXISTING_31_AUTHORS_RESPAWN_STEALTH_CANDIDATE"
    output=out/"GQ540_RC31_CANDIDATE.project.json"
    output.write_text(json.dumps(relink,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,mapped=scan(output)
    for key in set(files)-{HOST_KEY}:
        if files[key].read_bytes()!=mapped[key].read_bytes():
            raise ValueError("RED_OTHER_AUTHOR_CHANGED "+"/".join(key))
    if mapped[HOST_KEY].read_text(encoding="utf-8")!=changed:
        raise ValueError("RED_HOST_PATCH_LOST")
    manifest={
      "source_count":31,"source_owner_base31":digest(receipt_path.read_bytes()),
      "old_host_sha256":digest(host.encode()),"new_host_sha256":digest(changed.encode()),
      "changed_runtime_sources":["/".join(HOST_KEY)],
      "unchanged_runtime_source_count":30,
      "official_rc_integrated":False,"claim_granted":False,
      "studio_android_owner":"NOT_TESTED",
      "source_sha256":{"/".join(k):digest(v.read_bytes()) for k,v in mapped.items()}
    }
    (out/"GQ540_RC31_CANDIDATE_RECEIPT.json").write_text(
      json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ540_CURRENT_31_AUTHOR_SINGLE_HOST_SOURCE_EXACT_PASS",len(mapped))
    return output

def verify_place(project:Path,receipt_path:Path,place:Path):
    _,files=scan(project)
    m=json.loads(receipt_path.read_text(encoding="utf-8"))
    actual={}
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        kind=item.attrib.get("class")
        if kind not in {"Script","ModuleScript","LocalScript"}:
            continue
        props=item.find("Properties")
        if props is None: continue
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or name in actual or src is None:
            raise ValueError("RED_MISSING_OR_DUPLICATE_EMBEDDED_SOURCE")
        actual[name]=(kind,src.replace("\r\n","\n"))
    if {k[-1] for k in files}!=set(actual):
        raise ValueError("RED_31_SCRIPT_NAME_DIFFERENCE")
    for key,fp in files.items():
        kind=("Script" if fp.name.endswith(".server.luau") else
              "LocalScript" if fp.name.endswith(".client.luau") else "ModuleScript")
        src=fp.read_text(encoding="utf-8").replace("\r\n","\n")
        if actual[key[-1]]!=(kind,src) or m["source_sha256"]["/".join(key)]!=digest(fp.read_bytes()):
            raise ValueError("RED_EMBEDDED_SCRIPT_CLASS_OR_SOURCE_MISMATCH "+key[-1])
    print("GQ540_31_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",place.stat().st_size,digest(place.read_bytes()))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.place:
        verify_place(a.project,a.receipt,a.place)
    else:
        prepare(a.project,a.receipt,a.out)
if __name__=="__main__":main()
