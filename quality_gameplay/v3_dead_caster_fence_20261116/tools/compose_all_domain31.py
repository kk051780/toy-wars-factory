#!/usr/bin/env python3
"""Preserve existing #533 30-source eight-domain admission; select #530/#535
into exactly ONE Combat, append original #516 StatusFence => PRIVATE31.

#528 neutral budget, #531 Host/membership, #484 bot AI, #494/#501/#533
one Swarm, #485 art, #487 score, #482 characters/lobby/castle/items remain
byte-exact as existing author source selections, not reimplemented.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from compose_six_author import source_union, import_author, MEMBER, MEMBER_BLOB, REPLACEMENT, ENTRY, sha256, ORIGINAL_529_FOUR_SHA256, ROOT, four_author_module

BASE30_RECEIPT="GQ_ADMISSION30_SOURCE_RECEIPT.json"
COMBAT_KEY=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
STATUS_KEY=("ServerScriptService","EGGRUMBLE_StatusTickFence")
SWARM_KEY=("ServerScriptService","EGGRUMBLE_SwarmCombat")
HOST_KEY=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
BOT_KEY=("ServerScriptService","EGGRUMBLE_BotActors")
ALL_REQUIRED={
 "EGGRUMBLE_BotPathRouter","EGGRUMBLE_BotActors",
 "EGGRUMBLE_CastleMatchRules","EGGRUMBLE_SwarmCombat",
 "EGGRUMBLE_FieldItemPickups","EGGRUMBLE_RaidItemIntake",
 "EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SevenRoleCombat",
 "EGGRUMBLE_CombatBalance","EGGRUMBLE_MatchResultService",
 "EGGRUMBLE_WeaponSilhouettes","EGGRUMBLE_NeutralMeleePolicy",
 "EGGRUMBLE_DualModeNeutralBudget",
}

def digest(path:Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def flat(project:Path):
    data=json.loads(project.read_text(encoding="utf-8"))
    seen={}
    def visit(node,prefix=()):
        for name,v in node.items():
            if name.startswith("$"): continue
            key=prefix+(name,)
            if not isinstance(v,dict): raise ValueError("RED_NONDICT_SOURCE_ENTRY")
            if "$path" in v:
                if set(v)!={"$path"}: raise ValueError("RED_NON_UNIQUE_SOURCE_MAPPING")
                path=(project.parent/v["$path"]).resolve(strict=True)
                if key in seen: raise ValueError("RED_DUPLICATE_SCRIPT")
                seen[key]=path
            else:visit(v,key)
    visit(data["tree"])
    if len(set(k[-1] for k in seen))!=len(seen): raise ValueError("RED_DUPLICATE_NAME")
    return data,seen

def build(base30:Path,out_dir:Path,enabled:bool):
    base30=base30.resolve(strict=True)
    base,original=flat(base30)
    receipt=json.loads((base30.parent/BASE30_RECEIPT).read_text(encoding="utf-8"))
    if len(original)!=receipt["source_count"] or len(original)!=30 or receipt["rc_adopted"]:
        raise ValueError("RED_NEUTRAL_ORIGINAL_AUTHOR30_RECEIPT")
    assert receipt["original_author_heads"]["membership531"]=="e78bff41e70564d0b26578e3c3a85f4698e6110e"
    assert receipt["original_author_heads"]["budget528"]=="6b29c50b6cc0b25192a121b2957497ede8b07f37"
    for key,path in original.items():
        if digest(path)!=receipt["mapped_sha256"]["/".join(key)]:
            raise ValueError("RED_BASE30_SOURCE_DRIFT "+"/".join(key))
    if not ALL_REQUIRED<=set(k[-1] for k in original):
        raise ValueError("RED_DOMAIN_AUTHORS_MISSING")
    if STATUS_KEY in original or COMBAT_KEY not in original:
        raise ValueError("RED_COMBAT_OR_STATUS_SOURCE_DUPLICATE")
    four=four_author_module()
    blob=four.git_blob(original[COMBAT_KEY].read_bytes())
    if blob!="66e666418b7c23d41f87faa5d61eb6e2770a463e":
        raise ValueError("RED_30_COMBAT_WAS_ALREADY_OWNED_OR_CHANGED: "+blob)
    # Neither #530 nor #535 own Host or Bot; preserve original 30 exactly.
    host=original[HOST_KEY].read_text(encoding="utf-8")
    bot=original[BOT_KEY].read_text(encoding="utf-8")
    swarm=original[SWARM_KEY].read_text(encoding="utf-8")
    for must in ("session.isCurrentHuman=function","gqDualBudget=GQDualBudget.new("):
        if host.count(must)!=1:raise ValueError("RED_HOST_528_531_AUTHORITY_MISSING "+must)
    for must in ("session.isCurrentHuman(player)","targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)"):
        if bot.count(must)!=1:raise ValueError("RED_BOT_484_531_AUTHORITY_MISSING "+must)
    for must in ("nearest.humanoid:TakeDamage(Melee.DAMAGE)","SpawnPacing.step(",
                 "EncounterFair.chooseIndex(","session.neutralBudget:acquire("):
        if swarm.count(must)!=1:raise ValueError("RED_NEUTRAL_494_501_528_533_AUTHORITY_MISSING "+must)
    combat,_=source_union(enabled)
    # Source-select exact #535 membership 4 gates and #530 single 2-line add.
    member=import_author(MEMBER,"member_535_for_admission31",MEMBER_BLOB)
    on,_=source_union(True)
    off,_=source_union(False)
    if on.replace(REPLACEMENT,ENTRY,1)!=off:
        raise ValueError("RED_31_ON_OFF_CHANGED_OTHER_AUTHORS")
    assert member.undo(off).encode("utf-8")!=original[COMBAT_KEY].read_bytes()
    assert member.undo(off)==four.build_union()[0]
    if combat!=(on if enabled else off):
        raise ValueError("RED_UNEXPECTED_COMBAT_COMPOSITION")
    dot=Path("_gq_dot/quality_gameplay/v3_status_tick_fence_20261116/EGGRUMBLE_StatusTickFence.luau")
    if four.git_blob(dot.read_bytes())!="40bb3bc47c07fe27f82a28c97f82529d10788a8a":
        raise ValueError("RED_ORIGINAL_516_STATUS_FENCE_CHANGED")
    out_dir.mkdir(parents=True,exist_ok=True)
    stem="ON" if enabled else "OFF"
    fixed=out_dir/("GQ31_SINGLE_COMBAT_"+stem+".luau")
    fixed.write_text(combat,encoding="utf-8")
    project=copy.deepcopy(base)
    project["name"]="GQ_31_EXISTING_EIGHT_DOMAIN_AUTHORS_PRIVATE_NOT_OFFICIAL_RC"
    def relink(node,prefix=()):
        for name,v in node.items():
            if name.startswith("$"):continue
            key=prefix+(name,)
            if "$path" in v:
                v["$path"]=os.path.relpath(original[key],out_dir).replace(os.sep,"/")
            else:relink(v,key)
    relink(project["tree"])
    project["tree"]["ServerScriptService"][COMBAT_KEY[-1]]={
        "$path":fixed.name
    }
    project["tree"]["ServerScriptService"][STATUS_KEY[-1]]={
        "$path":os.path.relpath(dot.resolve(),out_dir.resolve()).replace(os.sep,"/")
    }
    target=out_dir/("GQ31_"+stem+".project.json")
    target.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,mapped=flat(target)
    if len(mapped)!=31 or set(mapped)!=set(original)|{STATUS_KEY}:
        raise ValueError("RED_NOT_31_SOURCES")
    for key in set(original)-{COMBAT_KEY}:
        if mapped[key].read_bytes()!=original[key].read_bytes():
            raise ValueError("RED_UNAUTHORIZED_DOMAIN_OVERWRITE "+"/".join(key))
    if mapped[COMBAT_KEY].read_text()!=combat or mapped[STATUS_KEY].read_bytes()!=dot.read_bytes():
        raise ValueError("RED_NEW_COMBAT_STATUS_CONTENT_WRONG")
    if sum(k[0]=="ServerScriptService" for k in mapped)!=28 or sum(k[0]=="StarterPlayer" for k in mapped)!=3:
        raise ValueError("RED_SERVER_CLIENT_COUNT")
    manifest={
        "source_count":31,
        "previous_owner30_count":30,
        "previous_owner30_unchanged_sources":29,
        "single_current_seven_role_combat":True,
        "single_current_host":True,
        "single_current_bot":True,
        "single_current_swarm":True,
        "new_existing_author_516_status_module_only":True,
        "dead_530_enabled":enabled,
        "member_535_enabled":True,
        "current_484_ai_duel_preserved":True,
        "neutral_494_501_528_533_preserved":True,
        "art_485_score_487_preserved":True,
        "source_owner30_receipt_sha256":digest(base30.parent/BASE30_RECEIPT),
        "combat_sha256":sha256(combat),
        "status":"PRIVATE_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "official_rc_adopted":False,
        "claim_granted":False,
        "owner_accepted":False,
        "studio_android": "NOT_TESTED",
        "source_sha256":{"/".join(k):digest(v) for k,v in sorted(mapped.items())},
    }
    (out_dir/("GQ31_"+stem+"_RECEIPT.json")).write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ31_ALL_8_DOMAIN_ORIGINAL_AUTHOR_SOURCE_SELECT_PASS",stem,len(mapped))
    return target

def verify(project:Path,place:Path):
    import xml.etree.ElementTree as ET
    stem="ON" if "_ON." in project.name else "OFF"
    manifest=json.loads((project.parent/("GQ31_"+stem+"_RECEIPT.json")).read_text())
    _,expected=flat(project)
    if len(expected)!=31:raise ValueError("RED_SOURCE_COUNT_31")
    actual={}
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        typ=item.attrib.get("class")
        if typ not in {"Script","ModuleScript","LocalScript"}:continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or name in actual or source is None:
            raise ValueError("RED_DUPLICATE_OR_MISSING_SCRIPT")
        actual[name]=(typ,source.replace("\r\n","\n"))
    if {k[-1] for k in expected}!=set(actual):
        raise ValueError("RED_PLACE_SCRIPT_NAMES")
    for key,src in expected.items():
        name=key[-1]
        kind="Script" if src.name.endswith(".server.luau") else ("LocalScript" if src.name.endswith(".client.luau") else "ModuleScript")
        if actual[name]!=(kind,src.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_SCRIPT_CLASS_OR_SOURCE_MISMATCH "+name)
        if manifest["source_sha256"]["/".join(key)]!=digest(src):
            raise ValueError("RED_SOURCE_CHANGED_SINCE_MANIFEST "+name)
    manifest["private_place_bytes"]=place.stat().st_size
    manifest["private_place_sha256"]=digest(place)
    manifest["real_rojo_source_class_exact_31"]=True
    (project.parent/("GQ31_"+stem+"_RECEIPT.json")).write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ31_ALL_DOMAIN_PRIVATE_ROJO_SOURCE_CLASS_EXACT_PASS",stem,place.stat().st_size)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base30",type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--off",action="store_true")
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.place:
        stem="OFF" if a.off else "ON"
        verify(a.out/("GQ31_"+stem+".project.json"),a.place)
    else:
        if a.base30 is None:p.error("--base30 required for build")
        build(a.base30,a.out,not a.off)
if __name__=="__main__":main()
