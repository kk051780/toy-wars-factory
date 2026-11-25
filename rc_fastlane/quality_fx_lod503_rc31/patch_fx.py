#!/usr/bin/env python3
"""GQ503 source-original client FX secondary culling, inline in only existing CombatFeel.
Author #503 policy and actual #482 seven unique FX names, never cull HIT/FLASH/RING/ULTIMATE.
No new LocalScript or event authority; 31 source mappings remain identical.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_castle_prompt_session_20261117"))
from select_castle import mapping

TARGET=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFeel")
FEATURE="GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117"
SOURCE="GQ503_COMBATFEEL_FX_LOD.client.luau"
RECEIPT="GQ503_CLIENT_FX_LOD_RECEIPT.json"
MARKER="GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117"
PURE_START="local function fxShouldHide("
PURE_END="local fxSecondaryNames="
PURE=\
'''local function fxShouldHide(kind:string,distance:number,touch:boolean,reduced:boolean,active:number,wasHidden:boolean?):boolean
 if kind~="SECONDARY" then return false end
 if type(distance)~="number" or distance~=distance or distance==math.huge or distance<0 then return false end
 if distance<=40 then return false end
 local far=if touch then 85 else 130
 if reduced then
  far=if touch then 48 else 70
 elseif active>=96 then
  far*=if touch then .68 else .8
 elseif active>=60 then
  far*=if touch then .84 else .9
 end
 local threshold=if wasHidden then far-9 else far+9
 return distance>math.max(40,threshold)
end
'''
ADDITION=\
'''
do -- GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117: original #503 budget inline in CombatFeel
 local fxInput=game:GetService("UserInputService")
 local fxTracked=0
 local fxElapsed=0
 local fxRecords:{[BasePart]:{original:number,hidden:boolean}}={}
 -- Exact original #482 secondary names; NEVER include FX_*_FLASH, *_RING or ULTIMATE_*.
''' + PURE + '''
local fxSecondaryNames={
 WarGod_FlyingSlash=true, Mage_CrystalStorm=true, Assassin_ShadowAfterimage=true,
 Esper_PsiOrbit=true, MadScientist_RailShot=true, Beast_FangClaw=true,
 CurseMaster_SoulFlame=true,
}
 local function fxOriginalArena(part:BasePart):boolean
  local current:Instance?=part.Parent
  while current and current~=workspace do
   if (current.Name=="TEAM_Arena" or current.Name=="BATTLE_ROYALE_Arena")
     and current.Parent and current.Parent.Name=="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW" then
    return true
   end
   current=current.Parent
  end
  return false
 end
 local function fxForget(part:BasePart)
  local record=fxRecords[part]
  if not record then return end
  if part.Parent then part.LocalTransparencyModifier=record.original end
  fxRecords[part]=nil
  fxTracked=math.max(0,fxTracked-1)
 end
 local function fxWatch(inst:Instance)
  if fxTracked>=128 or not inst:IsA("BasePart") then return end
  if fxRecords[inst]~=nil or not fxSecondaryNames[inst.Name] then return end
  if not fxOriginalArena(inst) then return end
  fxRecords[inst]={original=inst.LocalTransparencyModifier,hidden=false}
  fxTracked+=1
 end
 local fxAdded=workspace.DescendantAdded:Connect(fxWatch)
 local fxRemoved=workspace.DescendantRemoving:Connect(function(inst)
  if inst:IsA("BasePart") then fxForget(inst) end
 end)
 local fxHeartbeat=RunService.Heartbeat:Connect(function(dt:number)
  fxElapsed+=math.min(dt,.5)
  if fxElapsed<.22 then return end
  fxElapsed=0
  local camera=workspace.CurrentCamera
  if not camera then return end
  local origin=camera.CFrame.Position
  local touch=fxInput.TouchEnabled
  local reduced=player:GetAttribute("EGGRUMBLE_ReducedEffects")==true
  for part,record in pairs(fxRecords) do
   if not part.Parent or not fxOriginalArena(part) then
    fxForget(part)
   else
    local distance=(part.Position-origin).Magnitude
    local hidden=fxShouldHide("SECONDARY",distance,touch,reduced,fxTracked,record.hidden)
    if record.hidden~=hidden then
     record.hidden=hidden
     part.LocalTransparencyModifier=if hidden then 1 else record.original
    end
   end
  end
 end)
 player.AncestryChanged:Connect(function(_,parent)
  if parent~=nil then return end
  fxAdded:Disconnect();fxRemoved:Disconnect();fxHeartbeat:Disconnect()
  for part in pairs(fxRecords) do fxForget(part) end
 end)
end
'''
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def patch(src:str)->str:
    for required in (
      'local Players=game:GetService("Players")',
      'local RunService=game:GetService("RunService")',
      'local player=Players.LocalPlayer',
      'if not RunService:IsStudio() then return end',
      'RunService:BindToRenderStep("EGGRUMBLE_RealHitFeedback"',
      'ConfirmedHit042',
      'EGGRUMBLE_ImpactSequence',
    ):
        if required not in src:raise ValueError("RED_ORIGINAL_COMBATFEEL_ANCHOR_"+required)
    if MARKER in src or not src.endswith("\n"):raise ValueError("RED_FX_LOD_DOUBLE_OR_SOURCE_END")
    new=src+ADDITION
    if unpatch(new)!=src:raise ValueError("RED_FX_INVERSE")
    return new
def unpatch(src:str)->str:
    if src.count(ADDITION)!=1 or not src.endswith(ADDITION):raise ValueError("RED_FX_LOD_ROLLBACK")
    return src[:-len(ADDITION)]
def inspect(base:Path,chosen:Path):
    _,old=mapping(base)
    _,new=mapping(chosen)
    if set(old)!=set(new) or len(old)!=31 or TARGET not in old:raise ValueError("RED_31_OR_COMBATFEEL_MISSING")
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if changed!=[TARGET]:raise ValueError("RED_ONLY_COMBATFEEL")
    a=old[TARGET].read_text(encoding="utf8");b=new[TARGET].read_text(encoding="utf8")
    if patch(a)!=b or unpatch(b)!=a:raise ValueError("RED_BYTE_EXACT_ROLLBACK")
    if not new[TARGET].name.endswith(".client.luau"):raise ValueError("RED_LOD_MUST_BE_LOCALSCRIPT")
    return a,b,new
def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/SOURCE).exists():
        raise ValueError("RED_OUTPUT_COLLISION")
    obj,paths=mapping(base)
    before=paths[TARGET].read_text(encoding="utf8")
    after=patch(before)
    (out.parent/SOURCE).write_text(after,encoding="utf8")
    result=copy.deepcopy(obj)
    result["tree"][TARGET[0]][TARGET[1]][TARGET[2]]["$path"]=SOURCE
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    inspect(base,out)
    (out.parent/RECEIPT).write_text(json.dumps({
      "feature_id":FEATURE,"author_original_pr":503,"gameplay_sources":31,
      "only_changed_script":TARGET[-1],"other30_byte_exact":True,
      "off_rollback_exact":True,"script_class":"LocalScript","added_runtime_scripts":0,
      "never_cull_critical_flash_ring_ultimate_hit":True,"near_radius_studs":40,
      "heartbeat_cadence_seconds":.22,"max_tracked_parts":128,
      "original_sha256":sha(before.encode()),"selected_sha256":sha(after.encode()),
      "native":"PENDING","rojo":"PENDING","studio_android_fun_owner":"NOT_TESTED"
    },indent=2,sort_keys=True)+"\n")
    print("GQ503_CLIENT_SECONDARY_FX_LOD_ONE_COMBATFEEL_30_EXACT_OFF_PASS")
def verify(base:Path,out:Path,place:Path):
    before,after,paths=inspect(base.resolve(strict=True),out.resolve(strict=True))
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_ROJO_PROPS")
        name=props.findtext("string[@name='Name']")
        code=props.findtext("ProtectedString[@name='Source']")
        if code is None:code=props.findtext("string[@name='Source']")
        if not name or code is None or name in found:raise ValueError("RED_ROJO_NAME_DUP")
        found[name]=(klass,code.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={route[-1] for route in paths}:raise ValueError("RED_REAL_ROJO31_SCRIPT_SET")
    for route,file in paths.items():
        klass=("Script" if file.name.endswith(".server.luau") else
               "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(klass,file.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_CLASS_SOURCE_"+route[-1])
    p=out.parent/RECEIPT
    rec=json.loads(p.read_text(encoding="utf8"))
    if rec["original_sha256"]!=sha(before.encode()) or rec["selected_sha256"]!=sha(after.encode()):
        raise ValueError("RED_FX_SOURCE_HASH")
    rec.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,place_sha256=sha(place.read_bytes()))
    p.write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n")
    print("GQ503_ORIGINAL_CLIENT_LOD_ROJO31_CLASS_SOURCE_PASS",rec["place_bytes"])
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("action",choices=("prepare","verify"))
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--place",type=Path)
    z=a.parse_args()
    if z.action=="prepare":prepare(z.base,z.out)
    else:
        if z.place is None:a.error("verify requires --place")
        verify(z.base,z.out,z.place)
