#!/usr/bin/env python3
"""Source-locked visual-only 3D egg objective silhouettes for REAL69.
One existing selected art Script only; no Game, Score, Remote, collision or UI.
"""
import argparse,hashlib,json,shutil
from pathlib import Path

BASE="c226c63eeb235503f9292503b61f2173550337ec"
SOURCE_HASH="899cc3a1fddcf53b31a163f7e406f3758e1b607b185fc1d1f27ce10952d1be97"
SOURCE="ServerScriptService/EGGRUMBLE_EncounterReadabilityArt"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
FEATURE="GQ470_ART_EGG_STATION_SCULPT_REAL69_20261120"
OFF="off69_egg_station"

OLD='''local function decorateVault(part:BasePart)
 if marked[part] then return end
 if part.Name~="EggVault" and part.Name~="OwnEggDeposit" then return end
 if not arenaFor(part) then return end
 marked[part]=true
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_CastleEggStationArt_VisualOnly"
 art.Parent=part
 local isVault=part.Name=="EggVault"
 jewel(art,part,"StationBadge","Cylinder",Vector3.new(.15,2.9,2.9),
  CFrame.new(0,part.Size.Y/2+.6,0)*CFrame.Angles(0,0,math.rad(90)),
  if isVault then gold else jade,Enum.Material.Metal)
 -- Distinguish enemy-vault theft from your own deposit through shape and color.
end
'''

NEW='''-- GQ470_ART_EGG_STATION_SCULPT_REAL69_20261120
-- Source-only egg objective silhouettes, no new mechanics or obstruction.
-- Guarded cache has stone battlements; safe deposit an open metal cradle.
local MAX_EGG_STATION_ORNAMENTS=6
local function decorateVault(part:BasePart)
 if marked[part] then return end
 if part.Name~="EggVault" and part.Name~="OwnEggDeposit" then return end
 if not arenaFor(part) then return end
 marked[part]=true
 part.Destroying:Connect(function() marked[part]=nil end)
 local art=Instance.new("Folder")
 art.Name="EGGRUMBLE_CastleEggStationArt_VisualOnly"
 local isVault=part.Name=="EggVault"
 art:SetAttribute("EGGRUMBLE_ObjectiveKind",if isVault then "STEAL_FROM_VAULT" else "DELIVER_AT_HOME")
 art:SetAttribute("EGGRUMBLE_ArtOnly",true)
 art.Parent=part
 local count=0
 local top=part.Size.Y/2
 local function add(name:string,kind:string,size:Vector3,offset:CFrame,
   color:Color3,material:Enum.Material)
  if count>=MAX_EGG_STATION_ORNAMENTS then return end
  count+=1
  -- Reuse original jewel: welded, massless, shadowless, collision/touch/query OFF.
  jewel(art,part,name,kind,size,offset,color,material)
 end
 if isVault then
  add("VaultShieldFace","Wedge",Vector3.new(2.4,2.8,.40),
   CFrame.new(0,top+1.7,-.20),dark,Enum.Material.Slate)
  for _,side in ipairs({-1,1}) do
   add("VaultCrownTooth"..side,"Wedge",Vector3.new(.95,2.25,1.22),
    CFrame.new(side*1.85,top+1.95,.1)*CFrame.Angles(0,0,math.rad(-side*12)),
    ceramic,Enum.Material.Limestone)
  end
  add("VaultGoldSeal","Cylinder",Vector3.new(.19,1.55,1.55),
   CFrame.new(0,top+1.72,-.49)*CFrame.Angles(0,math.rad(90),0),
   gold,Enum.Material.Metal)
  add("VaultKeystone","Wedge",Vector3.new(1.25,.9,1.18),
   CFrame.new(0,top+3.3,.2),maroon,Enum.Material.Slate)
 else
  add("HomeCradleBowl","Cylinder",Vector3.new(.3,3.5,3.5),
   CFrame.new(0,top+.58,0)*CFrame.Angles(0,0,math.rad(90)),
   jade,Enum.Material.Metal)
  for _,side in ipairs({-1,1}) do
   add("HomeOpenWing"..side,"Wedge",Vector3.new(.8,2.15,1.05),
    CFrame.new(side*1.65,top+1.42,.16)*CFrame.Angles(0,0,math.rad(side*25)),
    ceramic,Enum.Material.Limestone)
  end
  add("HomeDeliveryCore","Ball",Vector3.new(1.55,1.55,1.55),
   CFrame.new(0,top+1.18,0),gold,Enum.Material.Glass)
  add("HomeBowTie","Block",Vector3.new(2.85,.22,.36),
   CFrame.new(0,top+.83,-1.13),steel,Enum.Material.Metal)
 end
end
'''

def need(ok,reason):
 if not ok:raise ValueError("RED_EGG_STATION_"+reason)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def scan(root):
 project=json.loads((root/PROJECT).read_text())
 result={}
 def visit(node,route=""):
  if not isinstance(node,dict):return
  if "$path" in node:
   p=(root/node["$path"]).resolve()
   need(p.is_relative_to(root.resolve()) and p.is_file(),"BAD_SOURCE_PATH")
   need(route not in result,"DUPLICATE_ROUTE")
   result[route]=p
  for name,child in node.items():
   if not name.startswith("$"):visit(child,route+"/"+name if route else name)
 visit(project["tree"])
 return result

def patch(source):
 need(FEATURE not in source,"DUPLICATE")
 need(source.count(OLD)==1,"ANCHOR_CHANGED")
 need('if not RunService:IsStudio() then return end' in source,"ART_OWNER_DRIFT")
 need(all(x in source for x in ('p.CanCollide=false','p.CanTouch=false','p.CanQuery=false','p.CastShadow=false')),"NONPHYSICAL_DRIFT")
 need('elseif instance.Name=="EggVault" or instance.Name=="OwnEggDeposit" then' in source,"OBJECTIVE_ROUTE_DRIFT")
 new=source.replace(OLD,NEW,1)
 need(new.count(FEATURE)==1 and new.count('local function decorateVault(part:BasePart)')==1,"SINGLE_OWNER")
 need(new.count("MAX_EGG_STATION_ORNAMENTS=6")==1 and 'part.Destroying:Connect(function() marked[part]=nil end)' in new,"BUDGET_CLEANUP")
 need(all(x not in NEW for x in ('Instance.new("RemoteEvent")','Instance.new("ProximityPrompt")','task.spawn','TweenService:Create')),"NO_GAME_AUTHORITY")
 return new

def selftest():
 s=('if not RunService:IsStudio() then return end\n'
    'p.CanCollide=false\np.CanTouch=false\np.CanQuery=false\np.CastShadow=false\n'
    'elseif instance.Name=="EggVault" or instance.Name=="OwnEggDeposit" then\n'+OLD)
 new=patch(s)
 need("VaultCrownTooth" in new and "HomeOpenWing" in new,"TWO_SHAPES")
 for bad in (new,s.replace(OLD,""),s.replace('p.CanQuery=false','p.CanQuery=true'),
             s.replace('RunService:IsStudio()','false'),s.replace('OwnEggDeposit','Fake')):
  try:patch(bad)
  except ValueError:pass
  else:raise AssertionError("NEGATIVE_MUTATION_ACCEPTED")
 print("GQ470_EGG_STATION_FIVE_MUTANTS_PASS")

def apply(root):
 paths=scan(root)
 rpath=root/RECEIPT
 receipt=json.loads(rpath.read_text())
 need(len(paths)==receipt.get("selected_source_count")==69 and SOURCE in paths and
      set(paths)==set(receipt.get("source_hashes",{})),"REAL69_ROUTES")
 need(receipt.get("build_head")==BASE,"OFFICIAL_PARENT")
 hashes={k:digest(p.read_bytes()) for k,p in paths.items()}
 need(hashes==receipt["source_hashes"] and hashes[SOURCE]==SOURCE_HASH,"SOURCE_LOCK_69")
 off=root/OFF
 need(not off.exists(),"ROLLBACK_COLLISION")
 off.mkdir()
 for path in paths.values():
  p=off/path.relative_to(root.resolve());p.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(path,p)
 for name in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
  shutil.copyfile(root/name,off/name)
 old=paths[SOURCE].read_bytes()
 revised=patch(old.decode("utf-8")).encode("utf-8")
 paths[SOURCE].write_bytes(revised)
 now=scan(root)
 need(set(now)==set(paths) and len(now)==69,"ROUTES")
 need({k for k in now if digest(now[k].read_bytes())!=hashes[k]}=={SOURCE},"ONE_SOURCE_ONLY")
 need(all((off/p.relative_to(root.resolve())).read_bytes()==
          (old if k==SOURCE else p.read_bytes()) for k,p in paths.items()),"OFF69_EXACT")
 need((off/PROJECT).read_bytes()==(root/PROJECT).read_bytes(),"ROJO_ROUTE_CLASS")
 receipt["source_hashes"][SOURCE]=digest(revised)
 receipt["build_head"]="PREP_EGG_STATION_FROM_"+BASE
 receipt["gq470_egg_station_art"]={
  "feature_id":FEATURE,"formal_parent":BASE,"target":SOURCE,
  "original_sha256":SOURCE_HASH,"candidate_sha256":digest(revised),
  "other_selected_sources_byte_exact":68,"total_selected_sources":69,
  "max_ornament_parts_per_station":6,"new_scripts":0,"new_collisions":False,
  "new_ui":False,"new_gameplay_or_scoring_authority":False,
  "source_native":"NOT_TESTED","rojo":"NOT_TESTED","studio":"NOT_TESTED",
  "android":"NOT_TESTED","owner_accepted":False,"rollback":OFF}
 rpath.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 print("GQ470_EGG_STATION_ONE_SOURCE_68_EXACT_OFF69_SOURCE_READY")

if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--self-test",action="store_true")
 a.add_argument("--base",type=Path);x=a.parse_args()
 if x.self_test:selftest()
 else:need(x.base is not None,"NO_ARTIFACT");apply(x.base)
