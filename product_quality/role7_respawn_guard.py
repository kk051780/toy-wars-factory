#!/usr/bin/env python3
"""FB004 source-exact: stop delayed 7-job PvE hits after avatar respawn/team migration.

Read only latest frozen author/quality stage artifact. No official RC or main edits.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from collections import Counter
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET

PARENT_SHA="4f7161e48898b486edc52a2555594994b9876448f79d9954435034bfe02a98ef"
PARENT_GAME="981af6a5f56ef78e0850bf0393e03031d9b85837"
EXPECTED_PLACE_SHA="f6cc936a17b10d7cbfb1eb31718025a6fe21346160cacea8d58e8e52d93eb542"
EXPECTED_GAME="00fab56c721145688a34ba2825babd7bac351fbb"
RC="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
SOURCE="COMPOSED_ROLE7_WIND_RC82.rbxlx"
NEW="COMPOSED_ROLE7_WIND_BUILDERQ_DELAYED_SAFE_RC82.rbxlx"
GAME="server/Game.server.luau"

def sha(b): return hashlib.sha256(b).hexdigest()
def blob(s):
    b=s.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def extract(data):
    root=ET.fromstring(data)
    scripts={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"): continue
        props=item.find("Properties")
        if props is None: continue
        name=props.findtext("string[@name='Name']")
        src=props.find("string[@name='Source']")
        if not name or src is None or src.text is None or name in scripts:
            raise ValueError("MALFORMED_OR_DUPLICATE_SCRIPT")
        scripts[name]=src
    return root,scripts
def verify(place,source_lock,feature_lock):
    _,scripts=extract(place)
    if len(scripts)!=82 or source_lock.get("total_scripts")!=82 or feature_lock.get("total_sources")!=82:
        raise ValueError("SOURCE_COUNT_DRIFT")
    if source_lock.get("blobs")!=feature_lock.get("source_gitblobs"):
        raise ValueError("SOURCE_DUAL_LOCK_DRIFT")
    if Counter(blob(s.text) for s in scripts.values())!=Counter(source_lock["blobs"].values()):
        raise ValueError("PLACE_SOURCE_DRIFT")
    return scripts

def build(source_path,target_path,extract_dir=None):
    with ZipFile(source_path) as z:
        if len(z.namelist())!=len(set(z.namelist())):
            raise ValueError("REPEATED_ZIP_MEMBER")
        place=z.read(SOURCE)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if sha(place)!=PARENT_SHA or receipt.get("head")!=RC or lock["blobs"].get(GAME)!=PARENT_GAME:
        raise ValueError("UNPINNED_OR_STALE_BASE")
    before=verify(place,lock,feature)
    root,files=extract(place)
    old=before["Game"].text
    marker="local function sevenJobDelayedStrike("
    start=old.find(marker)
    end=old.find("\nlocal function useSevenJob(",start)
    if start<0 or end<0 or old.count(marker)!=1:
        raise ValueError("ORIGINAL_SKILL_DISPATCH_DRIFT")
    previous=old[start:end]
    if previous.count("    local selectedAck=sevenJobPickAckSeq[player]\n")!=1 or "local castCharacter" in previous:
        raise ValueError("ACK_OR_RESPAWN_GUARD_CONFLICT")
    new=previous.replace(
      "    local selectedAck=sevenJobPickAckSeq[player]\n",
      "    local selectedAck=sevenJobPickAckSeq[player]\n"
      "    -- FB004: only the original character and team own this deferred cast.\n"
      "    local castCharacter=player.Character\n"
      "    local castTeam=getTeamName(player)\n"
      '    if not castCharacter or (castTeam~="RED" and castTeam~="BLUE") then return end\n',1)
    anchor="            or player.Parent~=Players or sevenJobs[player]~=job\n"
    if new.count(anchor)!=1:raise ValueError("DEFERRED_ROLE_ANCHOR_DRIFT")
    new=new.replace(anchor,
      "            or player.Parent~=Players or player.Character~=castCharacter\n"
      "            or getTeamName(player)~=castTeam or sevenJobs[player]~=job\n",1)
    anchor2="if not alive or not root or (root.Position-origin).Magnitude>28 then return end"
    if new.count(anchor2)!=1:raise ValueError("DEFERRED_AVATAR_ANCHOR_DRIFT")
    new=new.replace(anchor2,
      "if not alive or not root or root.Parent~=castCharacter\n"
      "            or (root.Position-origin).Magnitude>28 then return end",1)
    updated=old[:start]+new+old[end:]
    if blob(updated)!=EXPECTED_GAME: raise ValueError("NEW_GAME_BLOB_MISMATCH")
    files["Game"].text=updated
    data=ET.tostring(root,encoding="utf-8")
    if sha(data)!=EXPECTED_PLACE_SHA or len(data)!=778612:
        raise ValueError("NEW_PLACE_BYTES_OR_SHA_MISMATCH")
    after=extract(data)[1]
    if any(after[n].text!=before[n].text for n in before if n!="Game"):
        raise ValueError("UNRELATED_AUTHOR_SOURCE_CHANGED")
    lock["blobs"][GAME]=feature["source_gitblobs"][GAME]=EXPECTED_GAME
    verify(data,lock,feature)
    meta={"schema":"P0D_FB004_EXACT_ACK_COMBO_DEFERRED_RESPAWN_SAFE_V2",
          "official_rc_head":RC,"parent_place_sha256":PARENT_SHA,
          "place_sha256":sha(data),"place_bytes":len(data),
          "scripts":82,"unchanged_parent_scripts":81,
          "new_game_blob":EXPECTED_GAME,"changed":[GAME],
          "native":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN",
          "owner":False,"official_rc_write":False,"product":"NO_GO"}
    with ZipFile(target_path,"w",ZIP_DEFLATED) as z:
        z.writestr(NEW,data)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    if extract_dir is not None:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for name,s in after.items():
            (extract_dir/(name+".luau")).write_text(s.text,encoding="utf-8")
    return meta

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--extract",type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.input,args.output,args.extract),ensure_ascii=False,indent=2))
