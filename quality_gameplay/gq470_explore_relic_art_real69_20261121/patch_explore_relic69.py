#!/usr/bin/env python3
"""GQ470: shape the REAL69 exploration relics in place, never gameplay logic.

Only one original source route changes, with 69/69 receipt lock and exact OFF.
No new Parts, scripts, prompts, raycast/collection/score/combat authorities.
Static source/compile/Place gates are not Studio/Android/human ART approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET = "ServerScriptService/EGGRUMBLE_LegacyExplorationBridge"
ORIGINAL_GIT_BLOB = "89cab7de50f7efc03bf5d3f3cfaa667855c14d19"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF = "OFF69_EXPLORE_RELIC_SCULPT"
MARK = "GQ470_FB015_EXPLORE_RELIC_0PART_SCULPT_REAL69_20261121"

OLD_HELPER = '''local function makePart(name:string,size:Vector3,pos:CFrame,color:Color3,mat:Enum.Material,parent:Instance)
 local p=Instance.new("Part")
'''
NEW_HELPER = '''local function makePart(name:string,size:Vector3,pos:CFrame,color:Color3,mat:Enum.Material,parent:Instance,partClass:string?)
 local p=Instance.new(partClass or "Part")
'''

OLD_GEOMETRY = '''  local core=makePart(id.."_Artifact",Vector3.new(2.2,2.2,2.2),
   CFrame.new(point)*CFrame.Angles(math.rad(22),math.rad(45),math.rad(20)),
   spec[6]::Color3,Enum.Material.SmoothPlastic,folder)
  makePart(id.."_Relief",Vector3.new(.28,1.9,.28),
   CFrame.new(point+Vector3.new(0,.05,-1.4))*CFrame.Angles(0,0,math.rad(45)),
   Color3.fromRGB(245,237,205),Enum.Material.Metal,folder)
'''

# Shape, vertical profile and tilt are independent by realm. The six shards
# become frosted spherical fragments. Every marker still uses one core, one
# pedestal and one relief; count remains exactly three Parts/marker.
STYLES = '''-- GQ470_FB015_EXPLORE_RELIC_0PART_SCULPT_REAL69_20261121
-- Four distinct realm silhouettes; no additional physical or decorative Parts.
local realmRelics={
 REALM_SKY={size=Vector3.new(1.6,3.1,1.5),pitch=math.rad(-18),yaw=math.rad(38),mat=Enum.Material.SmoothPlastic},
 REALM_SEA={size=Vector3.new(2.8,1.8,2.2),pitch=math.rad(16),yaw=math.rad(-33),mat=Enum.Material.Glass},
 REALM_EMBER={size=Vector3.new(1.5,3.2,1.8),pitch=math.rad(36),yaw=math.rad(12),mat=Enum.Material.Slate},
 REALM_STAR={size=Vector3.new(2.4,2.5,2.4),pitch=math.rad(-29),yaw=math.rad(48),mat=Enum.Material.Metal},
}
'''

NEW_GEOMETRY = '''  local style=realmRelics[id]
  local core=makePart(id.."_Artifact",
   if style then style.size else Vector3.new(1.7,1.7,1.7),
   CFrame.new(point)*CFrame.Angles(
    if style then style.pitch else math.rad(12),
    if style then style.yaw else math.rad(45),math.rad(20)),
   spec[6]::Color3,
   if style then style.mat else Enum.Material.Glass,folder,
   if style then "WedgePart" else "Part")
  if not style then
   -- Star shards are small frosted orbs, not the former ten identical cubes.
   core.Shape=Enum.PartType.Ball
   core.Transparency=.16
  end
  core.CastShadow=false
  -- A faceted low-glare inlay replaces the former neon-like thin rod:
  -- its position and zero-collision/no-raycast status remain unchanged.
  local relief=makePart(id.."_Relief",
   if style then Vector3.new(1.1,1.8,.46) else Vector3.new(.7,1.25,.38),
   CFrame.new(point+Vector3.new(0,.05,-1.4))*CFrame.Angles(0,math.rad(20),math.rad(18)),
   Color3.fromRGB(225,212,173),Enum.Material.Metal,folder,"WedgePart")
  relief.CastShadow=false
'''

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_blob_sha(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode() + b"\0"
    return hashlib.sha1(header + data).hexdigest()

def require(test: bool, reason: str) -> None:
    if not test:
        raise ValueError("RED_EXPLORE_RELIC_" + reason)

def selected(root: Path) -> dict[str, Path]:
    project=json.loads((root/PROJECT).read_text(encoding="utf-8"))
    paths:dict[str,Path]={}
    base=root.resolve()
    def walk(node: object, route: str=""):
        if not isinstance(node,dict): return
        if "$path" in node:
            path=(root/node["$path"]).resolve()
            require(path.is_relative_to(base) and path.is_file(),"UNSAFE_PROJECT_PATH")
            require(route not in paths,"DUPLICATE_ROUTE")
            paths[route]=path
        for key,value in node.items():
            if not key.startswith("$"):
                walk(value,route+"/"+key if route else key)
    walk(project["tree"])
    return paths

def transform(source: str) -> str:
    require(MARK not in source,"DOUBLE_PATCH")
    require(source.count(OLD_HELPER)==1,"ORIGINAL_HELPER_ANCHOR")
    require(source.count(OLD_GEOMETRY)==1,"ORIGINAL_GEOMETRY_ANCHOR")
    require(source.count("local function install(arena:Instance,mode:string)")==1,"INSTALL_ANCHOR")
    require('if not RunService:IsStudio() then return end' in source,"STUDIO_FENCE")
    require('prompt.RequiresLineOfSight=true' in source,"PROMPT_LINE_OF_SIGHT")
    require('rayParams.RespectCanCollide=true' in source,"SERVER_LOS")
    require('if folder.Parent~=arena or arena.Parent~=origin' in source,"SESSION_AUTHORITY")
    result=source.replace(OLD_HELPER,NEW_HELPER,1)
    result=result.replace("local function install(arena:Instance,mode:string)",
                          STYLES+"local function install(arena:Instance,mode:string)",1)
    result=result.replace(OLD_GEOMETRY,NEW_GEOMETRY,1)
    require(result.count(MARK)==1,"MARKER_COUNT")
    require(NEW_GEOMETRY.count("makePart(")==2 and OLD_GEOMETRY.count("makePart(")==2,"ZERO_PART_GROWTH")
    require("Instance.new(" not in NEW_GEOMETRY,"NO_EXTRA_INSTANCE")
    # Byte-identical gameplay/event/prompt logic after the cosmetic region.
    old_tail=source.split('  local prompt=Instance.new("ProximityPrompt")',1)[1]
    new_tail=result.split('  local prompt=Instance.new("ProximityPrompt")',1)[1]
    require(old_tail==new_tail,"PROMPT_AND_ALL_GAMEPLAY_PRESERVED")
    for forbidden in ("RemoteEvent","DataStore","TakeDamage","SetAttribute","ProximityPrompt"):
        require(forbidden not in NEW_GEOMETRY,"GEOMETRY_AUTHORITY_"+forbidden)
    return result

def self_test() -> None:
    head=('local RunService=game:GetService("RunService")\n'
          'if not RunService:IsStudio() then return end\n'
          'local function install(arena:Instance,mode:string) end\n'
          'prompt.RequiresLineOfSight=true\n'
          'rayParams.RespectCanCollide=true\n'
          'if folder.Parent~=arena or arena.Parent~=origin then return end\n')
    fixture=head+OLD_HELPER+" p.Parent=parent\n return p\nend\n"+OLD_GEOMETRY+'''  local prompt=Instance.new("ProximityPrompt")
  prompt.Triggered:Connect(function(p) return end)
'''
    out=transform(fixture)
    require(out.count("WedgePart")==2 and out.count("realmRelics")==2,"SCULPT_4REALM")
    require("core.Shape=Enum.PartType.Ball" in out and "core.Transparency=.16" in out,"SIX_SHARDS")
    require("if style then style.mat else Enum.Material.Glass" in out,"MATERIAL_TUNING")
    require(out.count("makePart(")==fixture.count("makePart("),"NO_EXTRA_PART_CALLS")
    mutants=[
        out,fixture.replace(OLD_GEOMETRY,""),fixture.replace(OLD_HELPER,""),
        fixture.replace('if not RunService:IsStudio() then return end',""),
        fixture.replace("prompt.RequiresLineOfSight=true","prompt.RequiresLineOfSight=false"),
        fixture.replace("rayParams.RespectCanCollide=true","rayParams.RespectCanCollide=false"),
        fixture.replace("local function install(arena:Instance,mode:string)","local function wrong()"),
        fixture.replace("if folder.Parent~=arena or arena.Parent~=origin","if false"),
    ]
    for i,mutant in enumerate(mutants):
        try: transform(mutant)
        except ValueError: continue
        raise AssertionError("RED_NEGATIVE_MUTANT_"+str(i))
    print("GQ470_EXPLORE_RELIC_8_MUTATION_NEGATIVES_PASS")

def apply(root: Path) -> None:
    files=selected(root)
    receipt_path=root/RECEIPT
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    require(receipt.get("build_head")==BASE and receipt.get("canonical_build") is True,"PINNED_FORMAL_HEAD")
    require(len(files)==69 and TARGET in files,"EXACT_69_ROUTES")
    original_hashes={key:sha(value.read_bytes()) for key,value in files.items()}
    require(receipt.get("source_hashes")==original_hashes,"EXACT_69_RECEIPT_LOCK")
    original=files[TARGET].read_bytes()
    require(git_blob_sha(original)==ORIGINAL_GIT_BLOB,"ORIGINAL_GIT_BLOB_MISMATCH")
    require((root/PLACE).is_file(),"REAL_PRIVATE_PLACE_MISSING")
    before=root/OFF
    require(not before.exists(),"OFF_ALREADY_EXISTS")
    shutil.copytree(root/"sources",before/"sources")
    for name in (PROJECT,RECEIPT,PLACE):
        shutil.copy2(root/name,before/name)
    replacement=transform(original.decode("utf-8")).encode("utf-8")
    files[TARGET].write_bytes(replacement)
    after_hashes={key:sha(value.read_bytes()) for key,value in files.items()}
    require({k for k in after_hashes if after_hashes[k]!=original_hashes[k]}=={TARGET},
            "CHANGED_ONE_SOURCE_ONLY")
    require(all(files[k].read_bytes()==selected(before)[k].read_bytes()
                for k in files if k!=TARGET),"OTHER_68_EXACT")
    receipt["source_hashes"]=after_hashes
    receipt["gq470_explore_relic_art"]={
        "feature_id":MARK,"formal_parent":BASE,"target":TARGET,
        "original_git_blob":ORIGINAL_GIT_BLOB,
        "original_source_sha256":original_hashes[TARGET],
        "candidate_source_sha256":after_hashes[TARGET],
        "unchanged_selected_routes":68,
        "relic_markers":10,"realm_sculptures":4,"orb_shards":6,
        "parts_per_marker_before_after":[3,3],
        "new_instances_per_arena":0,"new_scripts":0,"new_prompts":0,
        "gameplay_authority_changed":False,"collision_changed":False,
        "rollback":OFF,"studio":"NOT_TESTED","android":"NOT_TESTED",
        "human_art":"NOT_TESTED","screenshots_received":0,"owner_accepted":False,
    }
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                            encoding="utf-8")
    print("GQ470_EXPLORE_RELIC_REAL69_1_OF_69_CHANGED_68_EXACT")
    print("TARGET_SOURCE_SHA256",after_hashes[TARGET])

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--base",type=Path)
    args=parser.parse_args()
    if args.self_test: self_test()
    else:
        require(args.base is not None,"BASE_REQUIRED")
        apply(args.base)
