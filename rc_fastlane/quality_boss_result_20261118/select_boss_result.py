#!/usr/bin/env python3
"""GQ8 Boss result: truthful server-owned Stone Giant credit in EXISTING ResultService.
One source of canonical 31 changes; exact OFF, no new Game/HUD/Remote/Store.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality_decor732_rc31"))
from select_current import mapping

FEATURE="GQ8_BOSS_RESULT_TRUE_CREDIT_20261118"
TARGET=("ServerScriptService","EGGRUMBLE_MatchResultService")
SELECTED_NAME="GQ8_BOSS_RESULT_SELECTED_SOURCE.luau"
RECEIPT="GQ8_BOSS_RESULT_RC31_RECEIPT.json"
ANCHOR=(
 ' if mode=="TEAM" then\n'
 '  return status.."・"..specialty,string.format("%d位 %d点｜KO%d 奪%d(帰%d) 納%d 城%d 団%d",\n'
 '   place,points,kos,stolen,secured,eggs,fallen,teamSiege)\n'
 ' end\n'
 ' return status.."・"..specialty,string.format("%d位 %d点｜KO%d 奪%d(帰%d) 納%d 城%d",\n'
 '  place,points,kos,stolen,secured,eggs,fallen)\n'
)
MARKER="-- GQ8_BOSS_RESULT_TRUE_CREDIT_20261118"
BOSS_BLOCK=(
 MARKER+"\n"
 ' local rawBoss=player:GetAttribute("EGGRUMBLE_BossDefeats")\n'
 ' local boss=if type(rawBoss)=="number" and rawBoss==rawBoss\n'
 '  and rawBoss>=1 and rawBoss<math.huge then math.min(99,math.floor(rawBoss)) else 0\n'
 ' local bossSuffix=if boss>0 then " 巨"..tostring(boss) else ""\n'
)
REPLACEMENT=BOSS_BLOCK + ANCHOR.replace(
 '   place,points,kos,stolen,secured,eggs,fallen,teamSiege)\n',
 '   place,points,kos,stolen,secured,eggs,fallen,teamSiege)..bossSuffix\n'
).replace(
 '  place,points,kos,stolen,secured,eggs,fallen)\n',
 '  place,points,kos,stolen,secured,eggs,fallen)..bossSuffix\n'
)

def digest(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def patch(s:str)->str:
    if s.count(ANCHOR)!=1 or MARKER in s or s.count("GQ_DRAW_LABEL_RESULT")!=1 or "ScoreBalance.build(" not in s:
        raise ValueError("RED_GQ8_BOSS_RESULT_ORIGINAL_DRIFT_OR_REAPPLY")
    if s.count("local function resultText(")!=1 or s.count("function ResultService.showIfFinished(")!=1:
        raise ValueError("RED_GQ8_BOSS_RESULT_AUTHORITY")
    out=s.replace(ANCHOR,REPLACEMENT,1)
    if unpatch(out)!=s:
        raise ValueError("RED_GQ8_BOSS_RESULT_ROLLBACK")
    return out

def unpatch(s:str)->str:
    if s.count(REPLACEMENT)!=1:
        raise ValueError("RED_GQ8_BOSS_RESULT_OFF_DRIFT")
    return s.replace(REPLACEMENT,ANCHOR,1)

def validate(base:Path,out:Path):
    _,before=mapping(base)
    _,after=mapping(out)
    if len(before)!=31 or set(before)!=set(after) or TARGET not in before:
        raise ValueError("RED_GQ8_BOSS_RESULT_SOURCE_SET")
    changed=[k for k in before if before[k].read_bytes()!=after[k].read_bytes()]
    if changed!=[TARGET]:
        raise ValueError("RED_GQ8_BOSS_RESULT_MORE_THAN_ONE_SOURCE")
    a=before[TARGET].read_text(encoding="utf-8")
    b=after[TARGET].read_text(encoding="utf-8")
    if patch(a)!=b or unpatch(b)!=a:
        raise ValueError("RED_GQ8_BOSS_RESULT_BYTE_EXACT_OFF")
    return before,after,a,b

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or base.parent!=out.parent or (out.parent/SELECTED_NAME).exists():
        raise ValueError("RED_GQ8_BOSS_RESULT_OUTPUT_COLLISION")
    project,before=mapping(base)
    a=before[TARGET].read_text(encoding="utf-8")
    b=patch(a)
    (out.parent/SELECTED_NAME).write_text(b,encoding="utf-8")
    obj=copy.deepcopy(project)
    obj["name"]="EGGRUMBLE_V3_GQ8_BOSS_RESULT_31"
    obj["tree"][TARGET[0]][TARGET[1]]["$path"]=SELECTED_NAME
    out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    validate(base,out)
    rec={"feature_id":FEATURE,"source_count":31,"one_existing_result_module":True,
         "changed_script":TARGET[1],"other30_byte_exact":True,
         "off_previous_rc_byte_exact":True,"new_game_hud_remote_store":0,
         "boss_source":"server-owned EGGRUMBLE_BossDefeats Attribute; reset by GQ514",
         "zero_boss_retains_old_result_string":True,"same_gui_dimensions":True,
         "old_sha256":digest(a.encode()),"new_sha256":digest(b.encode()),
         "native":"PENDING","rojo":"PENDING","studio_android_fun":"NOT_TESTED",
         "official_adoption":False}
    (out.parent/RECEIPT).write_text(json.dumps(rec,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ8_BOSS_RESULT_ONE_EXISTING_MODULE_OTHER30_EXACT_OFF_PASS")

def native(base:Path,out:Path,mutant:Path):
    _,files=mapping(base)
    s=files[TARGET].read_text(encoding="utf-8")
    if MARKER not in s or "GQ_DRAW_LABEL_RESULT" not in s:
        raise ValueError("RED_GQ8_BOSS_RESULT_NATIVE_MISSING_FEATURE")
    start=s.index("local function castleEliminations(")
    end=s.index("local function makeResultGui(",start)
    prefix=s[start:end]
    fixture='''\
local p={UserId=101,attributes={EGGRUMBLE_BossDefeats=2}}
function p:GetAttribute(name) return self.attributes[name] end
local session={rules={winner="RED",castles={["101"]={team="RED",alive=true,depositedEggs=3}},
 events={{type="CASTLE_FALL",attacker="101"}}},swarm={kills={["101"]=44}}}
local ranking={rows={{id="101",score=500,stolen=2,securedSteals=1,
 teamCastleSupport=4,specialty="攻城"}}}
local title,stats=resultText(session,p,"TEAM",ranking)
assert(title=="勝利！・攻城","RED_GQ8_BOSS_RESULT_WIN_LOST")
assert(stats=="1位 500点｜KO44 奪2(帰1) 納3 城1 団4 巨2",
 "RED_GQ8_BOSS_RESULT_TRUE_CREDIT_MISSING")
p.attributes.EGGRUMBLE_BossDefeats=0
local _,zero=resultText(session,p,"TEAM",ranking)
assert(zero=="1位 500点｜KO44 奪2(帰1) 納3 城1 団4","RED_GQ8_BOSS_RESULT_ZERO_CHANGED")
p.attributes.EGGRUMBLE_BossDefeats=-1
local _,neg=resultText(session,p,"TEAM",ranking)
assert(neg==zero,"RED_GQ8_BOSS_RESULT_NEGATIVE")
p.attributes.EGGRUMBLE_BossDefeats=0/0
local _,nan=resultText(session,p,"TEAM",ranking)
assert(nan==zero,"RED_GQ8_BOSS_RESULT_NAN")
p.attributes.EGGRUMBLE_BossDefeats=math.huge
local _,infinity=resultText(session,p,"TEAM",ranking)
assert(infinity==zero,"RED_GQ8_BOSS_RESULT_INFINITY")
p.attributes.EGGRUMBLE_BossDefeats=1
session.rules.winner="DRAW"
local draw,_=resultText(session,p,"TEAM",ranking)
assert(draw=="引き分け・攻城","RED_GQ8_BOSS_RESULT_DRAW")
session.rules.winner="101"
local _,br=resultText(session,p,"BATTLE_ROYALE",ranking)
assert(br=="1位 500点｜KO44 奪2(帰1) 納3 城1 巨1","RED_GQ8_BOSS_RESULT_BR")
session.rules.castles["101"]=nil
local spectator,detail=resultText(session,p,"TEAM",ranking)
assert(spectator=="試合終了" and detail=="観戦をありがとう","RED_GQ8_BOSS_RESULT_SPECTATOR")
print("GQ8_BOSS_RESULT_REAL_RESULT_NATIVE_9_CASE_PASS")
'''
    out.write_text(prefix+fixture,encoding="utf-8")
    mutant.write_text(prefix.replace(' local rawBoss=player:GetAttribute("EGGRUMBLE_BossDefeats")',
                                      ' local rawBoss=0',1)+fixture,encoding="utf-8")
    print("GQ8_BOSS_RESULT_REAL_AND_MUTANT_NATIVE_CREATED")

def verify(base:Path,out:Path,place:Path):
    old,new,a,b=validate(base.resolve(strict=True),out.resolve(strict=True))
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ8_BOSS_RESULT_MISSING_PROPS")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or src is None or name in found:raise ValueError("RED_GQ8_BOSS_RESULT_DUPLICATE")
        found[name]=(klass,src.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={k[-1] for k in new}:
        raise ValueError("RED_GQ8_BOSS_RESULT_PLACE_COUNT")
    for key,path in new.items():
        cls="Script" if path.name.endswith(".server.luau") else (
            "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]]!=(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ8_BOSS_RESULT_SOURCE_CLASS_"+key[-1])
    receipt_path=out.parent/RECEIPT
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["old_sha256"]!=digest(a.encode()) or receipt["new_sha256"]!=digest(b.encode()):
        raise ValueError("RED_GQ8_BOSS_RESULT_SHA_MISMATCH")
    receipt.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
                   place_sha256=digest(place.read_bytes()))
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ8_BOSS_RESULT_REAL_ROJO31_SOURCE_CLASS_OFF_EXACT_PASS")

def selftest():
    a=('local function resultText(session:any,player:Player,mode:string,ranking:any):(string,string)\n'
       ' -- GQ_DRAW_LABEL_RESULT\n -- ScoreBalance.build(\n'
       +ANCHOR+'end\n'
       'function ResultService.showIfFinished() end\n')
    b=patch(a)
    assert unpatch(b)==a
    assert b.count("EGGRUMBLE_BossDefeats")==1 and "巨" in b
    for invalid in (a.replace(ANCHOR,""),a.replace(ANCHOR,ANCHOR+ANCHOR),
                    a.replace("GQ_DRAW_LABEL_RESULT","MISSING"),b):
        try:patch(invalid)
        except ValueError:pass
        else:raise AssertionError("RED_GQ8_BOSS_RESULT_MUTANT_ACCEPTED")
    try:unpatch(a)
    except ValueError:pass
    else:raise AssertionError("RED_GQ8_BOSS_RESULT_UNSAFE_OFF")
    print("GQ8_BOSS_RESULT_SELFTEST_6_CASE_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["selftest","prepare","native","verify"])
    p.add_argument("--base",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--mutant",type=Path)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.command=="selftest":selftest()
    elif a.command=="prepare":prepare(a.base,a.out)
    elif a.command=="native":native(a.base,a.out,a.mutant)
    elif a.command=="verify":verify(a.base,a.out,a.place)
