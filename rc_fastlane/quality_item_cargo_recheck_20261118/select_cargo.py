#!/usr/bin/env python3
"""GQ8: continue watching an egg carrier until an earlier SLOW releases DASH.

The prior one-shot undo can fire while the humanoid is slowed (speed != DASH),
then exit permanently; a later SLOW expiry may restore the boosted 27 speed.
Reuse the only existing Item server script; do not introduce a second effect system.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_decor732_rc31"))
from select_current import mapping

FEATURE="GQ8_ITEM_CARGO_SLOW_RECHECK_20261118"
ITEM=("ServerScriptService","EGGRUMBLE_FieldItemPickups")
OUT_FILE="GQ8_ITEM_CARGO_SLOW_RECHECK_SELECTED.luau"
RECEIPT="GQ8_ITEM_CARGO_SLOW_RECHECK_RECEIPT.json"
MARKER="GQ8_ITEM_CARGO_SLOW_RECHECK_20261118"
OLD='''    if not matchActive() or carryingEnemyEggs(player,session) then
     undo()
     return
    end'''
NEW='''    if not matchActive() then
     undo()
     return
    end
    if carryingEnemyEggs(player,session) then
     -- GQ8_ITEM_CARGO_SLOW_RECHECK_20261118: SLOW may hide 27 speed.
     -- Recheck after its expiry; shield cleanup remains idempotent.
     undo()
    end'''
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def patch(src:str)->str:
    if src.count(OLD)!=1 or MARKER in src:
        raise ValueError("RED_GQ8_ITEM_CARGO_OLD_ANCHOR_DRIFT")
    for a in ('local function restoreSpeed()', 'if not matchActive() or player.Character~=buffCharacter then return end',
              'if kind~="HEAL" and carryingEnemyEggs(player,session) then return end',
              "cancelBuffIfCarrier(player,5,restoreSpeed)",
              'session.canCollectWorldItem', "if not healUseful(kind,hum.Health,hum.MaxHealth) then return end"):
        if a not in src:raise ValueError("RED_GQ8_ITEM_CARGO_PRIOR_FEATURE_LOST_"+a)
    selected=src.replace(OLD,NEW,1)
    if unpatch(selected)!=src:raise ValueError("RED_GQ8_ITEM_CARGO_NON_INVERSE")
    return selected

def unpatch(src:str)->str:
    if src.count(NEW)!=1 or src.count(MARKER)!=1:
        raise ValueError("RED_GQ8_ITEM_CARGO_SELECTED_ANCHOR_DRIFT")
    return src.replace(NEW,OLD,1)

def check(base:Path,out:Path):
    _,old=mapping(base)
    _,new=mapping(out)
    if len(old)!=31 or set(old)!=set(new) or ITEM not in old:
        raise ValueError("RED_GQ8_ITEM_CARGO_SCRIPT_SET")
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if changed!=[ITEM]:raise ValueError("RED_GQ8_ITEM_CARGO_OTHER30_CHANGED_"+str(changed))
    before=old[ITEM].read_text(encoding="utf-8")
    after=new[ITEM].read_text(encoding="utf-8")
    if patch(before)!=after or unpatch(after)!=before:
        raise ValueError("RED_GQ8_ITEM_CARGO_OFF_NOT_BYTE_EXACT")
    return before,after,new

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/OUT_FILE).exists():
        raise ValueError("RED_GQ8_ITEM_CARGO_OUTPUT_COLLISION")
    original,sources=mapping(base)
    before=sources[ITEM].read_text(encoding="utf-8")
    after=patch(before)
    (out.parent/OUT_FILE).write_text(after,encoding="utf-8",newline="")
    pr=copy.deepcopy(original)
    pr["name"]="EGGRUMBLE_V3_GQ8_ITEM_CARGO_RECHECK_31"
    pr["tree"][ITEM[0]][ITEM[1]]["$path"]=OUT_FILE
    out.write_text(json.dumps(pr,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    check(base,out)
    receipt={
      "feature_id":FEATURE,"script_count":31,"only_changed_existing":ITEM[-1],
      "other30_byte_exact":True,"off_exact":True,"adds_game_remote_store_authority":0,
      "one_shot_carrier_return_removed":True,"bounded_check_seconds":5,
      "old_source_sha256":sha(before.encode()),"new_source_sha256":sha(after.encode()),
      "native":"PENDING","rojo":"PENDING","studio_android_fun":"NOT_TESTED",
      "rollback":"flag OFF: remove only this one Item source-selection stage"
    }
    (out.parent/RECEIPT).write_text(json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ8_ITEM_CARGO_ONE_SOURCE_OFF_EXACT_30_UNCHANGED_PASS")

def helper(src:str)->str:
    a=src.index(" local function cancelBuffIfCarrier(")
    b=src.index("\n local serial=0",a)
    return src[a:b]

def harness(src:str)->str:
    # The helper itself is extracted byte-for-byte from the selected real ITEM.
    return '''local speed=12
local ticks=0
local restorations=0
local inMatch=true
local hasEgg=true
local task={}
function task.wait(dt)
 assert(dt==.25)
 ticks+=1
 if ticks==3 then speed=27 end -- a prior combat SLOW expires
end
function task.spawn(fn) fn() end
local function matchActive():boolean return inMatch end
local function carryingEnemyEggs(_player:any,_session:any):boolean return hasEgg end
local session={}
''' + helper(src) + '''
local function restore()
 restorations+=1
 if speed==27 then speed=16 end
end
cancelBuffIfCarrier({},5,restore)
assert(ticks>=3,"RED_GQ8_CARGO_CANCEL_QUIT_BEFORE_SLOW_EXPIRED")
assert(speed==16,"RED_GQ8_CARGO_BOOST_RESTORED_WITH_EGG")
assert(restorations>=3,"RED_GQ8_CARGO_NOT_POLLED")
ticks=0;restorations=0;hasEgg=false;speed=27
cancelBuffIfCarrier({},5,restore)
assert(ticks==20 and restorations==0 and speed==27,"RED_GQ8_NONCARRIER_CHANGED")
ticks=0;restorations=0;inMatch=false;hasEgg=true
cancelBuffIfCarrier({},5,restore)
assert(ticks==1 and restorations==1,"RED_GQ8_INACTIVE_NOT_BOUNDED")
print("GQ8_ITEM_CARGO_SLOW_EXPIRY_NATIVE_3_SCENARIOS_PASS")
'''

def native(selected:Path,good:Path,mutant:Path):
    _,ss=mapping(selected)
    updated=ss[ITEM].read_text(encoding="utf-8")
    previous=unpatch(updated)
    good.write_text(harness(updated),encoding="utf-8")
    mutant.write_text(harness(previous),encoding="utf-8")
    print("GQ8_ITEM_CARGO_LIVE_ITEM_NATIVE_AND_OLD_MUTANT_GENERATED")

def verify(base:Path,out:Path,place:Path):
    before,after,sources=check(base.resolve(strict=True),out.resolve(strict=True))
    seen={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        p=item.find("Properties")
        if p is None:raise ValueError("RED_GQ8_ITEM_XML_PROPS")
        name=p.findtext("string[@name='Name']")
        source=p.findtext("ProtectedString[@name='Source']")
        if source is None:source=p.findtext("string[@name='Source']")
        if not name or source is None or name in seen:raise ValueError("RED_GQ8_ITEM_DUPLICATE")
        seen[name]=(kind,source.replace("\r\n","\n"))
    if len(seen)!=31 or set(seen)!={r[-1] for r in sources}:
        raise ValueError("RED_GQ8_ITEM_PLACE_SET")
    for k,p in sources.items():
        cls=("Script" if p.name.endswith(".server.luau") else "LocalScript"
             if p.name.endswith(".client.luau") else "ModuleScript")
        if seen[k[-1]]!=(cls,p.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ8_ITEM_ROJO_SOURCE_CLASS_"+k[-1])
    rec=out.parent/RECEIPT
    obj=json.loads(rec.read_text(encoding="utf-8"))
    if obj["old_source_sha256"]!=sha(before.encode()) or obj["new_source_sha256"]!=sha(after.encode()):
        raise ValueError("RED_GQ8_ITEM_RECEIPT")
    obj.update(native="31/31",rojo="31/31",place_sha256=sha(place.read_bytes()),place_bytes=place.stat().st_size)
    rec.write_text(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ8_ITEM_CARGO_LIVE31_ROJO_CLASS_SOURCE_EXACT_PASS")

def selftest():
    fake='''--!strict
local function restoreSpeed() end
if not matchActive() or player.Character~=buffCharacter then return end
if kind~="HEAL" and carryingEnemyEggs(player,session) then return end
cancelBuffIfCarrier(player,5,restoreSpeed)
session.canCollectWorldItem
if not healUseful(kind,hum.Health,hum.MaxHealth) then return end
''' + OLD + "\n"
    result=patch(fake)
    assert unpatch(result)==fake
    try:patch(result)
    except ValueError:pass
    else:raise AssertionError("RED_GQ8_ITEM_DUPLICATE_PATCH")
    print("GQ8_ITEM_CARGO_STATIC_INVERSE_SELFTEST_PASS")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("action",choices=("prepare","verify","native","selftest"))
    a.add_argument("--base",type=Path)
    a.add_argument("--out",type=Path)
    a.add_argument("--selected",type=Path)
    a.add_argument("--place",type=Path)
    a.add_argument("--good",type=Path)
    a.add_argument("--mutant",type=Path)
    x=a.parse_args()
    if x.action=="selftest":selftest()
    elif x.action=="prepare":prepare(x.base,x.out)
    elif x.action=="native":native(x.selected,x.good,x.mutant)
    else:verify(x.base,x.out,x.place)
