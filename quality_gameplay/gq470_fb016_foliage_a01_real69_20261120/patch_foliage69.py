#!/usr/bin/env python3
"""#470 FB016: source-locked, reversible A01 forest visibility improvement for REAL69."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

BASE="273e763c42ee0f405ef854b75c3cf071b078e896"
TARGET="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD"
EXPECTED="565a9e2e4e3ee794636116d802c887f799c685a7bedb5cf72d30a130165b147d"
FEATURE="GQ470_FB016_FOLIAGE_TRUE_OCCLUSION_A01_REAL69_20261120"
BEGIN="-- The original S1 FB016 used geometry projection, not client damage/Remote.\n"
END="script.Destroying:Connect(function()\n"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
OFFICIAL_PLACE = {'bytes': 829822, 'sha256': 'ab6c1242a4df6d905b8abaf6662f78b704a15f707e2c6f2a838357f1feb511e5'}
CANDIDATE_SOURCE = {'bytes': 8919, 'sha256': '30c8c5c1946cef9d3ee194f70e2770b08f54e6ba91282b9d2048031eeb4b306a'}
NEW="""-- GQ470_FB016_FOLIAGE_TRUE_OCCLUSION_A01_REAL69_20261120
-- A01 visual-only: preserve nearby forest; fade only when actually between
-- camera and avatar, or enclosing camera; no extra Parts/Remote/render loop.
-- 160 canopies, 1800 tracked art objects, 0.16-second capped sampling.
local function insideCanopy(part:BasePart,point:Vector3):boolean
 local at=part.CFrame:PointToObjectSpace(point)
 return math.abs(at.X)<=part.Size.X*.5+.5
  and math.abs(at.Y)<=part.Size.Y*.5+.5
  and math.abs(at.Z)<=part.Size.Z*.5+.5
end
local function blocksAvatar(part:BasePart,eye:Vector3,avatar:Vector3):boolean
 -- Clip the camera→avatar segment against the canopy's rotated 3D box.
 -- This avoids spherical false positives and handles diagonal crossings.
 local start=part.CFrame:PointToObjectSpace(eye)
 local finish=part.CFrame:PointToObjectSpace(avatar)
 local delta=finish-start
 local tMin,tMax=0,1
 local function clipAxis(origin:number,step:number,radius:number):boolean
  if math.abs(step)<0.0001 then return math.abs(origin)<=radius end
  local enter=(-radius-origin)/step
  local leave=(radius-origin)/step
  if enter>leave then enter,leave=leave,enter end
  tMin=math.max(tMin,enter)
  tMax=math.min(tMax,leave)
  return tMin<=tMax
 end
 -- The slab interval already starts at [0,1]. A percentage cutoff would
 -- miss leaves next to either endpoint as the camera zooms out.
 return clipAxis(start.X,delta.X,part.Size.X*.5+.5)
  and clipAxis(start.Y,delta.Y,part.Size.Y*.5+.5)
  and clipAxis(start.Z,delta.Z,part.Size.Z*.5+.5)
end
task.spawn(function()
 while script.Parent and live do
  task.wait(.16)
  if not live or canopyCount==0 then continue end
  local camera=workspace.CurrentCamera
  if not camera then continue end
  local eye=camera.CFrame.Position
  local player=Players.LocalPlayer
  local character=player and player.Character
  local root=character and character:FindFirstChild("HumanoidRootPart")
  local avatar:Vector3?=if root and root:IsA("BasePart") then root.Position else nil
  for part in pairs(canopies) do
   if records[part] and part:IsDescendantOf(workspace) and not hidden[part] then
    local inside=insideCanopy(part,eye)
    local intersects=if avatar then blocksAvatar(part,eye,avatar) else false
    local fade=inside or intersects
    local alpha=if fade then (if inside then .88 else .76) else 0
    -- Distance LOD may have restored .93 on nearward transition; re-sync.
    if occluded[part]~=fade or part.LocalTransparencyModifier~=alpha then
     occluded[part]=fade
     part.LocalTransparencyModifier=alpha
    end
   else
    occluded[part]=nil -- far-distance A01 LOD remains authoritative
   end
  end
 end
end)
"""

def digest(data:bytes)->str:
 return hashlib.sha256(data).hexdigest()

def require(condition:bool,code:str)->None:
 if not condition: raise ValueError("RED_GQ470_A01_"+code)

def selected(root:Path)->dict[str,Path]:
 project=json.loads((root/PROJECT).read_text(encoding="utf-8"))
 files={}
 def walk(node,route=""):
  if not isinstance(node,dict): return
  if "$path" in node:
   path=(root/node["$path"]).resolve()
   require(path.is_relative_to(root.resolve()) and path.is_file(),"PATH")
   require(route not in files,"DUP_ROUTE")
   files[route]=path
  for key,child in node.items():
   if not key.startswith("$"): walk(child,route+"/"+key if route else key)
 walk(project["tree"])
 return files

def transform(source:str)->str:
 require(FEATURE not in source,"DOUBLE")
 require(source.count(BEGIN)==1 and source.count(END)==1,"ANCHOR")
 require(source.index(BEGIN)<source.index(END),"ORDER")
 require(source.count(" fadeConn:Disconnect()\n")==1,"CLEANUP")
 for guard in ("local MAX_CANOPIES=160","local MAX_TRACKED_PARTS=1800",
  "GQ8_RC86_GOROGAN_MOBILE_LOD_REAL68_20261120",
  "GQ8_RC86_FB016_FOLIAGE_SIGHTLINE_V3_20261119",
  "local function originalA01Distance(part:BasePart)",
  'if not RunService:IsStudio() then return end',
  'part.LocalTransparencyModifier=if isFar then 1 elseif occluded[part] then .93 else 0'):
  require(guard in source,"ORIGINAL_GUARD")
 out=(source[:source.index(BEGIN)]+NEW+source[source.index(END):]).replace(" fadeConn:Disconnect()\n","",1)
 require(out.count(FEATURE)==1 and "RunService.RenderStepped:Connect" not in out,"ONE_CLIENT_LOOP")
 require("RemoteEvent" not in NEW and "Instance.new" not in NEW and "CanCollide" not in NEW,"NO_AUTHORITY")
 require(out.count("script.Destroying:Connect(function()")==1,"CLEANUP_RETAINED")
 return out

def selftest():
 original=('if not RunService:IsStudio() then return end\n'
  'local MAX_TRACKED_PARTS=1800\nlocal MAX_CANOPIES=160\n'
  '-- GQ8_RC86_GOROGAN_MOBILE_LOD_REAL68_20261120\n'
  '-- GQ8_RC86_FB016_FOLIAGE_SIGHTLINE_V3_20261119\n'
  'local function originalA01Distance(part:BasePart) end\n'
  'part.LocalTransparencyModifier=if isFar then 1 elseif occluded[part] then .93 else 0\n'
  +BEGIN+"local old=RunService.RenderStepped:Connect(function() end)\n"
  +END+" fadeConn:Disconnect()\nend)\n")
 out=transform(original)
 require("insideCanopy" in out and "clipAxis" in out and "task.wait(.16)" in out and ".76" in out,"FIX_PRESENT")
 for broken in (out,original.replace(BEGIN,""),original.replace(" fadeConn:Disconnect()\n",""),
  original.replace("local MAX_CANOPIES=160","local MAX_CANOPIES=0"),
  original.replace("if not RunService:IsStudio() then return end","")):
  try: transform(broken)
  except ValueError: continue
  raise AssertionError("MUTANT_ACCEPTED")
 print("GQ470_A01_FB016_5_NEGATIVE_SELFTEST_PASS")

def identity(raw: bytes) -> dict:
 return {"bytes": len(raw), "sha256": digest(raw)}

def verify_official(root:Path,data:dict) -> None:
 manifest_file=root/"UNION22_DELIVERY_MANIFEST.json"
 manifest=json.loads(manifest_file.read_bytes())
 admission=json.loads((root/"UNION22_FINAL_ADMISSION.json").read_bytes())
 require(admission["formal_rc_adoption_proven"] is True and admission["official_build_head"]==BASE
  and admission["receipt_provenance"]=="OFFICIAL" and admission["instances"]==75
  and data["canonical_build"] is True and data["formal_rc_adoption_proven"] is True,"OFFICIAL_ADMISSION")
 require(identity((root/"EGGRUMBLE_REAL69_PRIVATE.rbxlx").read_bytes())==OFFICIAL_PLACE,"OFFICIAL_PLACE")
 present={path.relative_to(root).as_posix():identity(path.read_bytes()) for path in root.rglob("*")
  if path.is_file() and path!=manifest_file}
 require(len(present)==325 and present==manifest["files"],"OFFICIAL_MANIFEST_325")

def apply(root:Path,head:str):
 files=selected(root); data=json.loads((root/RECEIPT).read_text())
 require(head==BASE and data.get("build_head")==BASE,"STALE_HEAD")
 verify_official(root,data)
 require(data.get("official_branch")=="rc/p0d-s1-kids-rc01","FORMAL")
 require(len(files)==data.get("selected_source_count")==69,"REAL69")
 require(set(files)==set(data.get("source_hashes",{})),"ROUTE_SET")
 require(data["source_classes"].get(TARGET)=="LocalScript","CLASS")
 require(data["source_hashes"].get(TARGET)==EXPECTED,"TARGET_HASH")
 for route,path in files.items():require(digest(path.read_bytes())==data["source_hashes"][route],"INPUT_HASH_"+route)
 off=root/"OFF69_A01_FB016";require(not off.exists(),"DOUBLE_BACKUP")
 off.mkdir()
 shutil.copytree(root/"sources",off/"sources")
 for f in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):shutil.copyfile(root/f,off/f)
 original=files[TARGET].read_bytes();patched=transform(original.decode("utf-8")).encode("utf-8")
 require(identity(patched)==CANDIDATE_SOURCE,"EXACT_ORIGINAL_ART")
 files[TARGET].write_bytes(patched)
 restored=selected(off)
 require({route for route,path in files.items() if path.read_bytes()!=restored[route].read_bytes()}=={TARGET},"OTHER68_EXACT")
 require((root/PROJECT).read_bytes()==(off/PROJECT).read_bytes(),"PROJECT_LOCK")
 data["source_hashes"][TARGET]=digest(patched)
 data["gq470_fb016_true_occlusion"]={
  "feature_id":FEATURE,"changed_route":TARGET,"before_sha256":digest(original),
  "after_sha256":digest(patched),"other_selected_sources_byte_exact":68,
  "max_canopies":160,"max_tracked_parts":1800,"new_parts":0,
  "remote_or_damage_changes":False,"source_only":True,
  "human_art":"NOT_TESTED","android15":"NOT_TESTED","owner_accepted":False,
  "rollback":"OFF69_A01_FB016"}
 (root/RECEIPT).write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 print("GQ470_A01_FB016_REAL69_PREP_SOURCE_PASS",digest(patched))

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--base",type=Path)
 ap.add_argument("--head",default=BASE)
 args=ap.parse_args()
 if args.self_test:selftest()
 else:
  require(args.base is not None,"ARTIFACT_REQUIRED")
  apply(args.base,args.head)
