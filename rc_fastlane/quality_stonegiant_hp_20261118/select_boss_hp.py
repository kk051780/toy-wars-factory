#!/usr/bin/env python3
"""One existing StoneGiant ModuleScript: small server-owned HP world label.
Designed for current 57-flag official 31-source RC. Fail-closed OFF & Rojo proofs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_decor732_rc31"))
from select_current import mapping

FEATURE="GQ8_STONE_GIANT_NEARBY_TRUE_HP_20261118"
BOSS=("ServerScriptService","EGGRUMBLE_NeutralStoneGiant")
FILE="GQ8_STONE_GIANT_NEARBY_HP_SELECTED.luau"
RECEIPT="GQ8_STONE_GIANT_HP_RC31_RECEIPT.json"
MARKER="-- GQ8_STONE_GIANT_TRUE_HP_LABEL_20261118"
EYE=' eye.Material=Enum.Material.Neon\n'
HEALTH=' local health=900\n'
HIT='  model:SetAttribute("EGGRUMBLE_BossHealth",health)\n'
BOARD=(f" {MARKER}\n"
       ' local hpGui=Instance.new("BillboardGui")\n'
       ' hpGui.Name="EGGRUMBLE_StoneGiantLiveHP"\n'
       ' hpGui.Size=UDim2.fromOffset(174,32)\n'
       ' hpGui.StudsOffsetWorldSpace=Vector3.new(0,5,0)\n'
       ' hpGui.MaxDistance=55\n'
       ' hpGui.AlwaysOnTop=false\n'
       ' hpGui.Parent=eye\n'
       ' local hpText=Instance.new("TextLabel")\n'
       ' hpText.Name="VerifiedBossHP"\n'
       ' hpText.Size=UDim2.fromScale(1,1)\n'
       ' hpText.BackgroundColor3=Color3.fromRGB(25,31,43)\n'
       ' hpText.BackgroundTransparency=.2\n'
       ' hpText.TextColor3=Color3.fromRGB(238,241,250)\n'
       ' hpText.TextScaled=true\n'
       ' hpText.TextWrapped=false\n'
       ' hpText.Font=Enum.Font.GothamBold\n'
       ' hpText.Text="石巨人 900 / 900"\n'
       ' hpText.Parent=hpGui\n')
INIT=HEALTH+' model:SetAttribute("EGGRUMBLE_BossHealth",health)\n'
HIT_NEW=(HIT+
         '  hpText.Text="石巨人 "..tostring(math.floor(health)).." / 900"\n')

def digest(data:bytes)->str: return hashlib.sha256(data).hexdigest()

def unpatch(selected:str)->str:
    if selected.count(BOARD)!=1 or selected.count(INIT)!=1 or selected.count(HIT_NEW)!=1:
        raise ValueError("RED_GQ8_BOSS_HP_SELECTED_DRIFT")
    old=selected.replace(BOARD,"",1)
    old=old.replace(INIT,HEALTH,1)
    return old.replace(HIT_NEW,HIT,1)

def patch(before:str)->str:
    if MARKER in before or before.count(EYE)!=1 or before.count(HEALTH)!=1 or before.count(HIT)!=1:
        raise ValueError("RED_GQ8_BOSS_HP_OLD_SOURCE_DRIFT")
    if "local function shockwaveClear(" not in before or "local function damageFrom(" not in before:
        raise ValueError("RED_GQ8_BOSS_HP_ORIGINAL_GQ518_LOS_MISSING")
    if before.count('model:Destroy()')!=1 or before.count('local model=Instance.new("Model")')!=1:
        raise ValueError("RED_GQ8_BOSS_HP_SINGLE_BOSS_AUTHORITY")
    after=before.replace(EYE,EYE+BOARD,1)
    after=after.replace(HEALTH,INIT,1)
    after=after.replace(HIT,HIT_NEW,1)
    if unpatch(after)!=before:raise ValueError("RED_GQ8_BOSS_HP_NOT_INVERTIBLE")
    return after

def validate(base:Path,selected:Path):
    _,original=mapping(base)
    _,latest=mapping(selected)
    if len(original)!=31 or set(original)!=set(latest) or BOSS not in latest:
        raise ValueError("RED_GQ8_BOSS_HP_SOURCE_SET")
    changed=[x for x in original if original[x].read_bytes()!=latest[x].read_bytes()]
    if changed!=[BOSS]:raise ValueError("RED_GQ8_BOSS_HP_OTHER30_CHANGED")
    old=original[BOSS].read_text(encoding="utf-8")
    new=latest[BOSS].read_text(encoding="utf-8")
    if patch(old)!=new or unpatch(new)!=old:
        raise ValueError("RED_GQ8_BOSS_HP_OFF_NOT_BYTE_EXACT")
    return original,latest,old,new

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or base.parent!=out.parent or (out.parent/FILE).exists():
        raise ValueError("RED_GQ8_BOSS_HP_OUTPUT_COLLISION")
    project,old=mapping(base)
    before=old[BOSS].read_text(encoding="utf-8")
    after=patch(before)
    (out.parent/FILE).write_text(after,encoding="utf-8")
    doc=copy.deepcopy(project)
    doc["name"]="EGGRUMBLE_V3_GQ8_STONE_GIANT_HP_REAL31"
    doc["tree"][BOSS[0]][BOSS[1]]["$path"]=FILE
    out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    validate(base,out)
    receipt={
       "feature_id":FEATURE,"source_count":31,"changed_existing_script":BOSS[-1],
       "other30_byte_exact":True,"off_to_57flag_rc_byte_exact":True,
       "new_game_script_remote_store_score":0,"world_billboard_per_giant":1,
       "billboard_range_studs":55,"always_on_top":False,
       "numeric_hp_server_authority_only":True,"prior_sha256":digest(before.encode()),
       "selected_sha256":digest(after.encode()),"native":"PENDING",
       "rojo":"PENDING","studio_android_fun":"NOT_TESTED",
    }
    (out.parent/RECEIPT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ8_STONE_GIANT_HP_CURRENT31_ONE_BOSS_OTHER30_BYTE_EXACT_OFF_PASS")

def native(selected:Path,good:Path,mutant:Path):
    _,files=mapping(selected)
    s=files[BOSS].read_text(encoding="utf-8")
    if s.count(BOARD)!=1 or s.count(INIT)!=1 or s.count(HIT_NEW)!=1:
        raise ValueError("RED_GQ8_BOSS_HP_NATIVE_CURRENT_SOURCE")
    stub='''\
local created={}
local function new(class)
 local o={ClassName=class}
 function o:SetAttribute(k,v)
  self.attrs=self.attrs or {}
  self.attrs[k]=v
 end
 table.insert(created,o)
 return o
end
local Instance={new=new}
local Vector3={new=function(...) return {...} end}
local UDim2={fromOffset=function(...) return {...} end,fromScale=function(...) return {...} end}
local Color3={fromRGB=function(...) return {...} end}
local Enum={Font={GothamBold="GothamBold"}}
local model=new("Model")
local eye=new("Part")
'''
    middle='''\
local amount=50
health=math.max(0,health-amount)
'''
    # Copy real source snippets, including the exact server-side increment and UI update.
    check='''\
assert(#created==4,"RED_HP_INSTANCE_BUDGET")
assert(hpGui.Parent==eye and hpText.Parent==hpGui,"RED_HP_ANCHOR")
assert(hpGui.MaxDistance==55 and hpGui.AlwaysOnTop==false,"RED_HP_MOBILE_DISTANCE")
assert(hpText.Name=="VerifiedBossHP","RED_HP_OWNERSHIP")
assert(hpText.Text=="石巨人 850 / 900","RED_HP_SUCCESSFUL_HIT")
assert(model.attrs.EGGRUMBLE_BossHealth==850,"RED_HP_SERVER_ATTRIBUTE")
amount=950
health=math.max(0,health-amount)
'''
    finale='''\
assert(hpText.Text=="石巨人 0 / 900","RED_HP_ZERO")
assert(model.attrs.EGGRUMBLE_BossHealth==0,"RED_HP_ZERO_AUTHORITY")
assert(hpGui.AlwaysOnTop==false,"RED_HP_ALWAYS_ON_TOP")
print("GQ8_STONE_GIANT_REAL_SOURCE_NATIVE_8_PASS")
'''
    selected_source=(stub+BOARD+INIT+middle+HIT_NEW+check+HIT_NEW+finale)
    good.write_text(selected_source,encoding="utf-8")
    mutant.write_text(selected_source.replace(HIT_NEW,'',1),encoding="utf-8")
    print("GQ8_STONE_GIANT_REAL_AND_MUTANT_NATIVE_GENERATED")

def verify(base:Path,selected:Path,place:Path):
    original,latest,before,after=validate(base.resolve(strict=True),selected.resolve(strict=True))
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ8_HP_NO_PROPS")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or src is None or name in found:raise ValueError("RED_GQ8_HP_DUPLICATE_SCRIPT")
        found[name]=(kind,src.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={k[-1] for k in latest}:
        raise ValueError("RED_GQ8_HP_ROJO31_NAMES")
    for route,path in latest.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(kind,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ8_HP_ROJO_CLASS_SOURCE_"+route[-1])
    receipt_path=selected.parent/RECEIPT
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["prior_sha256"]!=digest(before.encode()) or receipt["selected_sha256"]!=digest(after.encode()):
        raise ValueError("RED_GQ8_HP_DIGEST")
    receipt.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
                   place_sha256=digest(place.read_bytes()))
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ8_STONE_GIANT_CURRENT31_REAL_ROJO_CLASS_SOURCE_OFF_EXACT_PASS")

def selftest():
    before=('local model=Instance.new("Model")\n'
            'local function damageFrom() end\n'
            +EYE+' local ring=Instance.new("Part")\n'
            +HEALTH+' local active=true\n'
            +HIT+'  eye.Color=Color3.fromRGB(1,2,3)\n'
            +'  model:Destroy()\n'
            +'local function shockwaveClear() end\n')
    changed=patch(before)
    assert unpatch(changed)==before
    for broken in (before.replace(EYE,""),before.replace(HEALTH,HEALTH+HEALTH),
                   before.replace("shockwaveClear","notShockwaveClear"),changed):
        try:patch(broken)
        except ValueError:pass
        else:raise AssertionError("RED_GQ8_HP_MUTANT_ACCEPTED")
    try:unpatch(before)
    except ValueError:pass
    else:raise AssertionError("RED_GQ8_HP_OFF_UNSELECTED")
    print("GQ8_STONE_GIANT_HP_SOURCE_SELFTEST_6_PASS")

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
